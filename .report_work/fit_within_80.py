from pathlib import Path
from docx import Document
source=Path('EvidenceAI_Project_Report_With_Screenshots_And_Code.docx')
out=Path('EvidenceAI_Project_Report_70_Pages_With_Screenshots_And_Code.docx')
d=Document(source)
heading=next(p for p in d.paragraphs if p.text.strip()=='16.8 Results, Verification and Limitations')
heading.paragraph_format.page_break_before=False
d.save(out)
print('Saved',out.resolve())
