from docx import Document
from docx.shared import Pt
p='EvidenceAI_Project_Report_70_Pages.docx'; d=Document(p)
def rep(x,s):
 for r in x.runs:r.text=''
 x.add_run(s); x.paragraph_format.space_after=Pt(6); x.paragraph_format.line_spacing=1.12
for x in d.paragraphs:
 t=x.text
 if '453 eligible INR-denominated records' in t:
  rep(x,'Isolation Forest analysis is conditional on eligible INR-denominated records, the available dependencies and the model prerequisites. The size of the analysed set depends on the runtime input and is not a fixed result asserted in this report.')
 elif 'All four existing automated unit tests passed successfully.' in t:
  rep(x,'The repository defines two unit tests for selected data-processing behavior. This report records their scope and does not claim an execution result.')
 elif 'successful execution of all four automated unit tests' in t:
  rep(x,'The repository defines two unit tests for selected data-processing behavior. A dated execution record should be added when those tests are run in the target environment.')
 elif 'All four automated tests passed successfully.' in t:
  rep(x,'The repository defines two unit tests for selected data-processing behavior. Their presence documents intended checks; no pass status is asserted here.')
 elif 'model analysed 453 INR-denominated records and marked 23 records' in t:
  rep(x,'Isolation Forest can identify statistical outliers when its runtime prerequisites are met. The eligible records and resulting flags depend on the input snapshot and configuration, so no fixed count is reported. These flags support review and are not evidence of fraud or misconduct.')
d.save(p)
print('Updated factual claims in',p)
