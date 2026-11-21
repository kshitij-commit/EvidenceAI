"""Print a compact audit of the local procurement dataset."""

import json

from src.data import audit_dataset, load_dataset


def main() -> None:
    print(json.dumps(audit_dataset(load_dataset()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
