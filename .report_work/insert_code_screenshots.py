from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

source=Path('EvidenceAI_Project_Report_With_Screenshots.docx')
output=Path('EvidenceAI_Project_Report_With_Screenshots_And_Code.docx')
media=Path('.report_work/source_media')
doc=Document(source)

sections=[
 ('13.1 Loading Procurement Datasets',[
  ('image6_data_loading.png','Figure 13.1: Source code screenshot for loading the procurement CSV files in src/data.py.',5.9)]),
 ('13.2 Data Integration and Processing',[
  ('image7.png','Figure 13.2: Source code screenshot for integrating tender, award and supplier records.',5.9),
  ('image8.png','Figure 13.3: Continuation of the procurement record integration code.',5.9)]),
 ('13.3 Rule-Based Anomaly Identification',[
  ('image9.png','Figure 13.4: Source code screenshot for rule-based procurement review indicators.',5.9)]),
 ('13.4 Machine Learning Using Isolation Forest',[
  ('image10.png','Figure 13.5: Source code screenshot for conditional Isolation Forest screening.',5.9)]),
 ('13.5 Main Application Interface',[
  ('image11.png','Figure 13.6: Source code screenshot for the Streamlit application page configuration.',5.9),
  ('image12.png','Figure 13.7: Source code screenshot for the procurement application page logic.',5.9),
  ('image13.png','Figure 13.8: Continuation of the Streamlit page implementation.',5.9)]),
 ('13.7 Data Quality Audit',[
  ('image14.png','Figure 13.9: Source code screenshot for auditing missing values and procurement links.',5.9)]),
 ('13.8 Data Visualization and Report Generation',[
  ('image15.png','Figure 13.10: Source code screenshot for publication activity visualization.',5.9)]),
]

def find_heading(title):
 for p in doc.paragraphs:
  if p.text.strip()==title: return p
 raise ValueError(f'Missing section: {title}')

def find_explanation(title):
 start=find_heading(title)
 in_section=False
 for p in doc.paragraphs:
  if p._p is start._p: in_section=True; continue
  if in_section and p.text.strip()=='Explanation:': return p
 raise ValueError(f'Missing Explanation after {title}')

for title,items in sections:
 anchor=find_explanation(title)
 for image_name,caption,width in items:
  image_path=media/image_name
  if not image_path.exists(): raise FileNotFoundError(image_path)
  image_p=anchor.insert_paragraph_before()
  image_p.alignment=WD_ALIGN_PARAGRAPH.CENTER
  image_p.paragraph_format.space_before=Pt(4)
  image_p.paragraph_format.space_after=Pt(1)
  image_p.paragraph_format.keep_together=True
  image_p.paragraph_format.keep_with_next=True
  image_p.add_run().add_picture(str(image_path),width=Inches(width))
  cap=anchor.insert_paragraph_before(caption)
  cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
  cap.paragraph_format.space_before=Pt(0)
  cap.paragraph_format.space_after=Pt(7)
  cap.paragraph_format.keep_together=True
  cap.paragraph_format.keep_with_next=False
  for run in cap.runs:
   run.font.name='Times New Roman'; run.font.size=Pt(9.5); run.italic=True

doc.save(output)
print('Saved',output.resolve(),'code screenshots',sum(len(items) for _,items in sections),'total inline images',len(doc.inline_shapes))
