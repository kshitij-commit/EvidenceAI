"""Small, transparent transformations used by the dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd


def tender_records(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return one row per main record with associated award/supplier summaries."""
    main = tables["main"].copy()
    main["award_date_parsed"] = pd.to_datetime(main["award_date"], errors="coerce", utc=True)
    main["published_date_parsed"] = pd.to_datetime(main["tender_datePublished"], errors="coerce", utc=True)
    awards = tables["awards"]
    supplier = tables["awards_suppliers"]
    # Summarize award records independently from supplier links. Joining first
    # would multiply an award with multiple suppliers and inflate its count/value.
    award_summaries = []
    for link, group in awards.groupby("_link_main", dropna=False):
        amounts = group.drop_duplicates("_link")
        award_summaries.append({
            "_link": link,
            "award_count": int(group["_link"].nunique()),
            "award_amounts": "; ".join(
                f"{row.value_amount:g} {row.value_currency}"
                for row in amounts.itertuples()
                if pd.notna(row.value_amount)
            ),
        })

    supplier_info = awards[["_link", "_link_main"]].merge(
        supplier[["_link_awards", "name"]],
        left_on="_link", right_on="_link_awards", how="left", validate="one_to_many",
    )
    supplier_summaries = supplier_info.groupby("_link_main", dropna=False)["name"].agg(
        lambda values: "; ".join(sorted(set(values.dropna().astype(str))))
    ).rename("supplier_names").reset_index().rename(columns={"_link_main": "_link"})

    if award_summaries:
        main = main.merge(pd.DataFrame(award_summaries), on="_link", how="left", validate="one_to_one")
    else:
        main["award_count"] = 0
        main["award_amounts"] = ""
    if not supplier_summaries.empty:
        main = main.merge(supplier_summaries, on="_link", how="left", validate="one_to_one")
    else:
        main["supplier_names"] = ""
    main["award_count"] = main["award_count"].fillna(0).astype(int)
    main["supplier_names"] = main["supplier_names"].fillna("")
    main["award_amounts"] = main["award_amounts"].fillna("")

    # Comparable award-vs-estimate feature: calculate only when the source
    # records provide the same currency and a positive tender estimate.
    tender_amount = pd.to_numeric(
        main.get("tender_value_amount", pd.Series(index=main.index, dtype="float64")), errors="coerce"
    )
    tender_currency = main.get(
        "tender_value_currency", pd.Series(index=main.index, dtype="string")
    ).astype("string").str.upper()
    award_totals = awards.copy()
    award_totals["value_amount"] = pd.to_numeric(award_totals["value_amount"], errors="coerce")
    award_totals["value_currency"] = award_totals["value_currency"].astype("string").str.upper()
    award_totals = award_totals.drop_duplicates("_link")
    if "tender_value_currency" in main:
        award_totals = award_totals.merge(
            main[["_link", "tender_value_currency"]].rename(columns={"tender_value_currency": "tender_currency"}),
            left_on="_link_main", right_on="_link", how="inner", suffixes=("", "_tender"),
        )
    else:
        award_totals["tender_currency"] = pd.NA
    award_totals = award_totals[
        award_totals["value_amount"].notna()
        & award_totals["value_currency"].eq(award_totals["tender_currency"].astype("string").str.upper())
    ].groupby("_link_main")["value_amount"].sum()
    main["linked_award_total_same_currency"] = main["_link"].map(award_totals)
    estimate_valid = tender_amount.gt(0) & tender_currency.notna() & tender_currency.ne("")
    main["award_to_estimate_pct"] = (
        (main["linked_award_total_same_currency"] - tender_amount) / tender_amount * 100
    ).where(estimate_valid & main["linked_award_total_same_currency"].notna())
    return main


def investigation_flags(records: pd.DataFrame, contamination: float = 0.05, fit_model: bool = True) -> pd.DataFrame:
    """Produce transparent indicators and optional Isolation Forest flags.

    Amount comparisons use only INR tender estimates. Missing-currency amounts
    are never compared. Indicator score is a review-priority score, not risk probability.
    """
    result = records.copy()
    amount = pd.to_numeric(result["tender_value_amount"], errors="coerce")
    currency = result["tender_value_currency"].astype("string").str.upper()
    tenders = pd.to_numeric(result["tender_numberOfTenderers"], errors="coerce")
    result["flag_single_tenderer"] = tenders.eq(1).fillna(False)
    result["flag_missing_amount_or_currency"] = (amount.isna() | currency.isna() | currency.eq("")).fillna(True)
    result["flag_zero_or_negative_amount"] = (amount.notna() & amount.le(0) & currency.eq("INR")).fillna(False)

    comparable = amount.where(currency.eq("INR"))
    positive = comparable[comparable > 0]
    if len(positive) >= 10:
        log_amount = np.log1p(positive)
        high_cutoff = float(log_amount.quantile(0.99))
        result["flag_high_inr_amount"] = (comparable > 0) & (np.log1p(comparable.fillna(0)) >= high_cutoff)
    else:
        result["flag_high_inr_amount"] = False

    # Missing currency is a data-quality note, not a statistical anomaly. It is
    # exposed separately so it does not make nearly the whole dataset "flagged".
    flags = ["flag_single_tenderer", "flag_zero_or_negative_amount", "flag_high_inr_amount"]
    result["indicator_score"] = result[flags].astype(int).sum(axis=1)
    result["model_flag"] = False
    result["model_score"] = np.nan
    result["model_status"] = "Model unavailable" if fit_model else "Model not run for this summary"
    # Use scikit-learn when installed and only INR records with a usable amount.
    model_rows = result.index[comparable.gt(0) & tenders.notna()] if fit_model else result.index[:0]
    if fit_model:
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.impute import SimpleImputer
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler

            if len(model_rows) >= 30:
                features = pd.DataFrame({
                    "log_inr_amount": np.log1p(comparable.loc[model_rows]),
                    "tenderers": tenders.loc[model_rows],
                    "tender_period_days": pd.to_numeric(result.loc[model_rows, "tender_tenderPeriod_durationInDays"], errors="coerce"),
                }, index=model_rows)
                transform = make_pipeline(SimpleImputer(strategy="median"), StandardScaler())
                matrix = transform.fit_transform(features)
                estimator = IsolationForest(
                    contamination=contamination, random_state=42, n_estimators=200
                ).fit(matrix)
                labels = estimator.predict(matrix)
                scores = estimator.decision_function(matrix)
                result.loc[model_rows, "model_flag"] = labels == -1
                result.loc[model_rows, "model_score"] = -scores
                result["model_status"] = f"Isolation Forest fit on {len(model_rows)} INR records"
        except ImportError:
            pass

    result["investigation_score"] = result["indicator_score"] + result["model_flag"].astype(int)
    result["flag_reasons"] = result.apply(
        lambda row: "; ".join(
            label for key, label in [
                ("flag_single_tenderer", "Single tenderer recorded"),
                ("flag_missing_amount_or_currency", "Tender amount or currency missing"),
                ("flag_zero_or_negative_amount", "Zero or negative INR tender amount"),
                ("flag_high_inr_amount", "Tender estimate is in the top 1% of positive INR estimates"),
                ("model_flag", "Isolation Forest statistical outlier"),
            ] if bool(row.get(key, False))
        ), axis=1
    )
    return result


def comparable_tenders(records: pd.DataFrame, tender_id: str, minimum_ratio: float = 0.5, maximum_ratio: float = 2.0) -> pd.DataFrame:
    """Return transparent, same-method/currency estimate peers for one tender.

    This is a simple screening cohort, not a claim that tenders are equivalent.
    It requires a positive estimate, exact procurement method and currency, and
    an estimate within the configured ratio around the selected tender.
    """
    selected = records[records["tender_id"].astype(str).eq(str(tender_id))]
    if selected.empty:
        return records.iloc[0:0].copy()
    row = selected.iloc[0]
    amount = pd.to_numeric(pd.Series([row.get("tender_value_amount")]), errors="coerce").iloc[0]
    currency_value = row.get("tender_value_currency")
    method_value = row.get("tender_procurementMethod")
    currency = "" if pd.isna(currency_value) else str(currency_value).strip().upper()
    method = "" if pd.isna(method_value) else str(method_value).strip()
    if pd.isna(amount) or amount <= 0 or not currency or not method:
        return records.iloc[0:0].copy()

    peer_amounts = pd.to_numeric(records["tender_value_amount"], errors="coerce")
    peer_currency = records["tender_value_currency"].fillna("").astype(str).str.strip().str.upper()
    peer_method = records["tender_procurementMethod"].fillna("").astype(str).str.strip()
    mask = (
        peer_amounts.between(amount * minimum_ratio, amount * maximum_ratio)
        & peer_currency.eq(currency)
        & peer_method.eq(method)
        & records["tender_id"].astype(str).ne(str(tender_id))
    )
    return records.loc[mask].copy()
