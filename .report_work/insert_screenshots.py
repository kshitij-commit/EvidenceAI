from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement

source=Path('EvidenceAI_Project_Report_70_Pages.docx')
output=Path('EvidenceAI_Project_Report_With_Screenshots.docx')
shots=Path('report_screenshots')
doc=Document(source)

figures=[
 ('6.3 Explore Records Module', '01_procurement_overview.jpg', 'Figure 6.1: EvidenceAI procurement overview dashboard.'),
 ('6.4 Anomaly Review Module', '02_procurement_explore_records.jpg', 'Figure 6.2: Explore Records screen with tender filters and source rows.'),
 ('6.5 Buyer & Supplier Search Module', '03_procurement_anomaly_review.jpg', 'Figure 6.3: Anomaly Review screen showing review leads and limits.'),
 ('6.6 Relationships Module', '04_procurement_buyer_supplier_search.jpg', 'Figure 6.4: Buyer and Supplier Search screen.'),
 ('6.7 Data Quality & Reports Module', '05_procurement_relationships.jpg', 'Figure 6.5: Procurement Relationships screen.'),
 ('6.8 Coordination Between Modules', '06_procurement_data_quality.jpg', 'Figure 6.6: Data Quality screen showing dataset audit indicators.'),
 ('16.2 Import, Mapping and Provenance', '07_paimana_overview_empty_state.jpg', 'Figure 16.1: PAIMANA overview before an official project snapshot is imported.'),
 ('16.3 Data Quality and Derived Indicators', '08_paimana_import_project_export.jpg', 'Figure 16.2: PAIMANA project export import workflow and source provenance field.'),
]

def locate_heading(text):
 for p in doc.paragraphs:
  if p.text.strip()==text:
   return p
 raise ValueError(f'Heading not found: {text}')

for target,image_name,caption in figures:
 anchor=locate_heading(target)
 image_path=shots/image_name
 if not image_path.exists(): raise FileNotFoundError(image_path)
 image_p=anchor.insert_paragraph_before()
 image_p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 image_p.paragraph_format.space_before=Pt(5)
 image_p.paragraph_format.space_after=Pt(2)
 image_p.paragraph_format.keep_together=True
 image_p.paragraph_format.keep_with_next=True
 image_p.add_run().add_picture(str(image_path),width=Inches(6.15))
 cap=anchor.insert_paragraph_before(caption)
 cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
 cap.paragraph_format.space_before=Pt(0)
 cap.paragraph_format.space_after=Pt(8)
 cap.paragraph_format.keep_together=True
 cap.paragraph_format.keep_with_next=False
 for r in cap.runs:
  r.font.name='Times New Roman'; r.font.size=Pt(10); r.italic=True

doc.save(output)
print('Saved',output.resolve(),'with',len(figures),'screenshots')
