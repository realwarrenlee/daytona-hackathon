from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

ROOT = Path(__file__).resolve().parent

def make_pdf(name, pages):
    target = ROOT/'demo'/name
    doc = canvas.Canvas(str(target), pagesize=A4)
    for i, lines in enumerate(pages, 1):
        doc.setFont('Helvetica-Bold', 15)
        doc.drawString(48, 790, 'BIDBLAST / SYNTHETIC TENDER')
        doc.setFont('Helvetica', 11)
        y = 750
        for line in lines:
            doc.drawString(48, y, line)
            y -= 23
        doc.drawString(48, 42, f'Fictional demonstration document - physical page {i}')
        doc.showPage()
    doc.save()

if __name__ == '__main__':
    (ROOT/'demo').mkdir(exist_ok=True)
    make_pdf('01_Evaluation.pdf', [[
        'Section 1. Mandatory eligibility',
        '1.1 Bidders must hold FM02 grade L6 at the date of submission.',
        '1.2 Bidders must also meet the mandatory safety certification',
        'requirements in 02_Contract_Conditions.pdf, physical page 3.',
        'The complete quotation in clause 1.2 continues across these two lines.',
    ]])
    filler = [f'{i}. Cleaning activities should be coordinated with the site manager.' for i in range(1,23)]
    make_pdf('02_Contract_Conditions.pdf', [
        ['Section 2. Contract administration', 'The contract covers daily cleaning services.'],
        ['Section 3. Site coordination'] + filler,
        ['Section 4. Mandatory conditions',
         '4.1 Bidders must hold bizSAFE Level 4 certification at submission.',
         '4.2 The successful contractor shall provide a security deposit of 5%',
         'of the awarded contract value before commencement.']])
    print('Created 2 synthetic PDFs. Company details are read from COMPANY.md; this script leaves that file unchanged.')
