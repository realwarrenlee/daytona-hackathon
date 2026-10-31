"""Runs inside Daytona. Extract source text, return bounded excerpts or targeted reads."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path('/tmp/bidblast')
KEYWORDS = re.compile(r'mandatory|shall|must|required|eligib|registr|FM02|bizSAFE|licen[cs]|deposit|PW Mark|progressive wage', re.I)


def extract(path):
    if path.suffix == '.pdf':
        from pypdf import PdfReader
        return [page.extract_text() or '' for page in PdfReader(path).pages]
    if path.suffix == '.docx':
        from docx import Document
        from docx.oxml.ns import qn
        document = Document(path)
        # Body order includes table cells and paragraphs; there are no stable physical pages in DOCX.
        text = '\n'.join(''.join(node.text or '' for node in paragraph.iter(qn('w:t')))
                         for block in document.element.body
                         if block.tag in {qn('w:p'), qn('w:tbl')}
                         for paragraph in block.iter(qn('w:p')))
        return [text[i:i+10000] for i in range(0,len(text),10000)] or ['']
    if path.suffix == '.doc':
        result = subprocess.run(['antiword', str(path)], capture_output=True, check=True)
        text = result.stdout.decode('utf-8', errors='replace')
        return [text[i:i+10000] for i in range(0,len(text),10000)] or ['']
    if path.suffix == '.xlsx':
        from openpyxl import load_workbook
        workbook = load_workbook(path, read_only=True, data_only=False)
        sections = []
        for sheet in workbook:
            text = f'Worksheet: {sheet.title}\n' + '\n'.join(
                f'Row {i}: ' + ' | '.join('' if value is None else str(value) for value in row)
                for i,row in enumerate(sheet.iter_rows(values_only=True),1) if any(value is not None for value in row))
            sections.extend(text[i:i+10000] for i in range(0,len(text),10000))
        workbook.close()
        return sections or ['']
    raise ValueError('Unsupported format')


def record(name, page, text, limit=14000):
    return dict(file=name, page=page, text=text[:limit], partial=len(text)>limit)


def index():
    documents, excerpts, cache = [], [], {}
    for item in json.loads((ROOT/'manifest.json').read_text()):
        name = item['file']
        try:
            pages = extract(Path(item['path']))
            cache[name] = pages
            documents.append(dict(file=name, pages=len(pages), characters=sum(map(len,pages))))
            documents[-1]['page_hints'] = [dict(page=i, hits=len(KEYWORDS.findall(text))) for i,text in enumerate(pages,1)]
            excerpts.append(record(name,1,pages[0],limit=6000))
            if not any(text.strip() for text in pages):
                documents[-1]['error'] = 'No extractable text; OCR may be required.'
        except Exception as error:
            documents.append(dict(file=name,pages=0,error=type(error).__name__ + ': extraction failed'))
    (ROOT/'cache.json').write_text(json.dumps(cache), encoding='utf-8')
    return dict(documents=documents,excerpts=excerpts)


def read():
    cache = json.loads((ROOT/'cache.json').read_text(encoding='utf-8'))
    excerpts, errors, seen = [], [], set()
    for request in json.loads((ROOT/'request.json').read_text()):
        name = request['file']
        if name not in cache:
            errors.append(f'Document not available: {name}')
            continue
        pages = cache[name]
        if 'page' in request:
            targets = [request['page']]
        else:
            words = {x.casefold() for x in re.findall(r'[A-Za-z]{4,}',request.get('query',''))}
            ranking = sorted(range(1,len(pages)+1),key=lambda p:sum(word in pages[p-1].casefold() for word in words),reverse=True)
            targets = ranking[:2]
        for number in targets:
            if type(number) is not int or not 1 <= number <= len(pages):
                errors.append(f'Invalid page/section for {name}')
            elif (name,number) not in seen:
                excerpts.append(record(name,number,pages[number-1]))
                seen.add((name,number))
    return dict(excerpts=excerpts,errors=errors)


if __name__ == '__main__':
    print(json.dumps(index() if sys.argv[1]=='index' else read(),ensure_ascii=False))
