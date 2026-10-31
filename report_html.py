"""Create a standalone tender review from a saved BidBlast JSON result."""
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path


LABELS = {'BLOCKER':'Potential blocker', 'REVIEW':'Review needed', 'SATISFIED':'Checked match'}


def norm(value):
    return ' '.join(str(value).casefold().split())


def group_findings(findings):
    groups = {}
    for item in findings:
        status, category = item['status'], item.get('category', '')
        if category == 'registration' and status in {'BLOCKER','SATISFIED'}:
            key = (status,category,norm(item.get('scheme','')),norm(item.get('required','')),norm(item.get('company','')))
        else:
            key = (status,category,norm(item.get('requirement','')),norm(item.get('required','')),norm(item.get('company','')))
        if key not in groups:
            groups[key] = dict(item, sources=[])
        sources = groups[key]['sources']
        if not any((x['file'],x['page'],x['quote']) == (item['file'],item['page'],item['quote']) for x in sources):
            sources.append(dict(item))
    return sorted(groups.values(),key=lambda item: list(LABELS).index(item['status']))


def render_report(report):
    esc = lambda value: escape(str(value),quote=True)
    groups = group_findings(report['findings'])
    counts = Counter(item['status'] for item in groups)
    metrics,profile = report['metrics'],report['profile']
    evidence = {}
    for group in groups:
        for item in group['sources']:
            key = (item['file'],item['page'],item['quote'])
            if key not in evidence:
                evidence[key] = {'id':f'E{len(evidence)+1:02}', 'item':item, 'findings':[]}

    def links(group):
        refs = []
        for item in group['sources']:
            ref = evidence[(item['file'],item['page'],item['quote'])]['id']
            refs.append(f'<a href="#{ref}" aria-label="Source evidence {ref}">{ref}</a>')
        return ', '.join(refs)

    rows = []
    for number,group in enumerate(groups,1):
        finding_id = f'F{number:02}'
        required = group.get('required','See source')
        requirement = group.get('requirement',required)
        required_note = f'<p class="secondary">Required: {esc(required)}</p>' if norm(required)!=norm(requirement) else ''
        for item in group['sources']:
            evidence[(item['file'],item['page'],item['quote'])]['findings'].append(finding_id)
        rows.append(f'''<tr id="{finding_id}"><td><span class="ref">{finding_id}</span>
            <strong>{esc(requirement)}</strong>{required_note}</td>
            <td>{esc(group.get('company','Not supplied'))}</td>
            <td><span class="assessment {group['status'].lower()}">{LABELS[group['status']]}</span>
            <p class="secondary">{esc(group.get('reason','Review the source requirement.'))}</p></td>
            <td class="source-links">{links(group)}</td></tr>''')

    blockers = [item for item in groups if item['status']=='BLOCKER']
    if blockers:
        decision = '<ul class="decision-list">' + ''.join(
            f'<li><strong>{esc(item.get("requirement",item.get("required","Requirement")))}</strong>'
            f'<p>{esc(item.get("reason","Review the mismatch."))} '
            f'Source evidence: {links(item)}.</p></li>' for item in blockers) + '</ul>'
    elif groups:
        decision = '<p>No checked condition was classified as a blocker. Review the unresolved evidence and applicability of the conditions below before deciding whether to bid.</p>'
    else:
        decision = '<p>No verified findings are available. A decision requires further investigation.</p>'

    quotations = []
    for source in evidence.values():
        item, ref = source['item'],source['id']
        locator = ('Physical page ' if item['file'].lower().endswith('.pdf') else 'Extraction section ') + str(item['page'])
        back = ', '.join(f'<a href="#{finding_id}">{finding_id}</a>' for finding_id in dict.fromkeys(source['findings']))
        quotations.append(f'''<details class="evidence" id="{ref}"><summary><span class="ref">{ref}</span>
            <span>{esc(item['file'])}<small>{esc(locator)}</small></span></summary>
            <div class="quotation"><p class="secondary">Supports findings {back}</p>
            <blockquote>{esc(' '.join(item['quote'].split()))}</blockquote></div></details>''')

    issues = ''.join(f'<li>{esc(issue)}</li>' for issue in report['unresolved'])
    issues = f'<ul class="issues">{issues}</ul>' if issues else '<p>No unresolved items were recorded. This does not establish overall eligibility.</p>'
    rounds = []
    for step in report.get('audit',[]):
        targets = '; '.join(request['file'] + (f" · page/section {request['page']}" if 'page' in request else ' · targeted section search') for request in step.get('followups',[]))
        rounds.append(f'<tr><th scope="row">{step["round"]}</th><td>{step["new_findings"]}</td><td>{esc(targets or "No further reads requested.")}</td></tr>')
    documents = []
    for doc in report.get('documents',[]):
        unit = ('page' if doc['pages']==1 else 'pages') if doc['file'].lower().endswith('.pdf') else ('extraction section' if doc['pages']==1 else 'extraction sections')
        documents.append(f'<tr><td>{esc(doc["file"])}</td><td>{doc["pages"]} {unit}</td><td>{esc(doc.get("error","Text extracted"))}</td></tr>')
    registration = '; '.join(f'{scheme} {grade}' for scheme,grade in profile.get('registration',{}).items()) or 'Not supplied'
    certifications = '; '.join(profile.get('certifications',[])) or 'None declared'
    company_source = Path(report['company_file']).name if report.get('company_file') else 'Saved result; source file not recorded'
    certifications = certifications if 'certifications' in profile else 'Not supplied'
    inference = report.get('inference',{})
    inference_note = f'<p class="run-data">Requirement extraction: {esc(inference.get("model","Not recorded"))}<br>Endpoint: {esc(inference.get("endpoint","Not recorded"))}</p>' if inference else ''
    title_class = 'blocker' if blockers else 'review' if report['verdict']=='REVIEW REQUIRED' else 'matched'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>BidBlast — Tender eligibility review</title><link rel="icon" href="data:,">
<style>
:root{{font-family:"Segoe UI",Arial,sans-serif;color:#242623;background:#eceeea;font-size:14px;line-height:1.6}}
*{{box-sizing:border-box}}body{{margin:0}}.paper{{max-width:1100px;margin:36px auto;background:#fff;padding:48px 60px 36px}}
button{{font:inherit;text-transform:none;letter-spacing:0;background:none;border:1px solid #9ca49c;padding:7px 12px;color:#414940;cursor:pointer}}
button:hover{{background:#f1f3ef}}button:focus-visible,a:focus-visible,summary:focus-visible{{outline:2px solid #50664e;outline-offset:4px}}
h1{{font-family:Georgia,"Times New Roman",serif;font-size:38px;font-weight:400;letter-spacing:-1px;line-height:1.2;margin:0 0 10px}}
.subtitle{{margin:0 0 30px;color:#60685e}}.profile{{display:grid;grid-template-columns:1fr 1fr;gap:16px 32px;margin:0 0 32px;font-size:12px}}
dt{{color:#687164;font-size:10px;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px}}dd{{margin:0}}
.decision{{border-top:2px solid #292e27;border-bottom:1px solid #cbd0c7;padding:22px 0 20px}}.decision h2{{font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:28px;line-height:1.3;margin:4px 0 16px}}
.blocker{{color:#933b31}}.review{{color:#715e27}}.matched{{color:#315e47}}.eyebrow{{font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:#687164}}
.decision-list{{list-style:none;padding:0;margin:0}}.decision-list li+li{{margin-top:16px}}.decision-list strong{{font-size:14px;font-weight:600}}.decision-list p{{margin:5px 0;font-size:13px}}
.scope{{font-size:12px;color:#60685e;margin:18px 0 0;max-width:820px}}.tally{{display:flex;flex-wrap:wrap;gap:10px 30px;margin:16px 0 0;font-size:12px}}
.tally b{{font-weight:650}}section{{margin:36px 0}}h2{{font-size:18px;font-weight:600;letter-spacing:-.2px;margin:0 0 8px}}.section-number{{font-size:11px;font-weight:400;color:#7a8275;margin-right:12px}}
.section-note{{font-size:12px;color:#687164;margin:0 0 18px}}table{{border-collapse:collapse;width:100%;text-align:left;font-size:12px;table-layout:fixed}}
thead th{{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;border-top:1px solid #a4ada0;border-bottom:1px solid #a4ada0;padding:10px 10px 10px 0;color:#626d5d}}
td,tbody th{{vertical-align:top;padding:14px 12px 14px 0;border-bottom:1px solid #e1e5dc;overflow-wrap:anywhere}}
td strong{{display:block;font-weight:550;line-height:1.55}}.register th:nth-child(1){{width:42%}}.register th:nth-child(2){{width:16%}}.register th:nth-child(3){{width:30%}}.register th:nth-child(4){{width:12%}}
.ref{{font-size:10px;font-weight:600;letter-spacing:.04em;color:#687164;display:block;margin-bottom:5px}}.assessment{{font-size:11px;font-weight:650}}
.assessment.blocker{{color:#933b31}}.assessment.review{{color:#715e27}}.assessment.satisfied{{color:#315e47}}
.secondary{{font-size:11px;color:#687164;margin:6px 0 0;line-height:1.55}}a{{color:#425d49;text-decoration:underline;text-underline-offset:3px}}.source-links a{{display:inline-block;margin:0 6px 4px 0}}
.evidence{{border-top:1px solid #d4dace;padding:0}}.evidence:last-child{{border-bottom:1px solid #d4dace}}
summary{{cursor:pointer;display:flex;align-items:start;gap:18px;padding:16px 0;font-size:12px}}summary::before{{content:'+';color:#687164;width:12px;flex:none}}details[open]>summary::before{{content:'−'}}
summary .ref{{min-width:28px;margin-top:1px}}summary small{{display:block;font-size:10px;color:#687164;margin-top:3px}}summary span:last-child{{overflow-wrap:anywhere}}
.quotation{{padding:0 0 20px 58px}}blockquote{{font-family:Georgia,"Times New Roman",serif;font-size:15px;line-height:1.8;margin:14px 0 0;padding-left:18px;border-left:2px solid #c2cabb}}
.issues{{padding-left:20px;font-size:12px}}.issues li{{margin:9px 0;overflow-wrap:anywhere}}.rounds th:first-child{{width:10%}}.rounds th:nth-child(2){{width:18%}}
.documents th:nth-child(1){{width:62%}}.documents th:nth-child(2){{width:20%}}.documents th:nth-child(3){{width:18%}}
.run-data{{font-size:11px;color:#687164;border-top:1px solid #d4dace;padding-top:14px;margin-top:20px}}footer{{border-top:1px solid #252b27;padding-top:16px;margin-top:40px;font-size:10px;color:#687164;line-height:1.7}}
tr:target,details:target{{background:#f6f6eb}}.empty{{font-size:13px;color:#687164;padding:15px 0}}
@media(max-width:720px){{.paper{{margin:0;padding:28px 22px}}h1{{font-size:31px}}.profile{{grid-template-columns:1fr}}.table-scroll{{overflow-x:auto}}.register{{min-width:640px}}.quotation{{padding-left:0}}}}
@page{{size:A4;margin:18mm 15mm;@bottom-right{{content:counter(page) " / " counter(pages);font:8pt "Segoe UI",Arial,sans-serif;color:#687164}}}}
@media print{{:root{{background:white;font-size:10pt}}.paper{{max-width:none;margin:0;padding:0}}button,.screen-only{{display:none!important}}h1{{font-size:27pt;margin-top:0}}.profile{{grid-template-columns:1fr 1fr}}section{{margin:25px 0}}h2,h1,summary{{break-after:avoid}}thead{{display:table-header-group}}tr,.documents,.inventory{{break-inside:avoid}}.table-scroll{{overflow:visible}}.register{{min-width:0}}table{{font-size:9pt}}.ref,.secondary{{font-size:8pt}}blockquote{{font-size:11pt;line-height:1.6}}details::details-content{{display:block;content-visibility:visible}}details>div{{display:block!important}}summary::before{{display:none}}.quotation{{padding-left:0}}a{{color:inherit}}.decision h2{{font-size:21pt}}.section-note,.scope{{font-size:9pt}}footer{{font-size:8pt}}}}
</style></head><body><main class="paper">
<h1>Tender eligibility review</h1><p class="subtitle">{esc(profile.get('name','Supplied company profile'))}</p>
<dl class="profile"><div><dt>Company details source</dt><dd>{esc(company_source)}</dd></div><div><dt>Declared registration</dt><dd>{esc(registration)}</dd></div><div><dt>Declared certifications</dt><dd>{esc(certifications)}</dd></div></dl>
<section class="decision" aria-label="Decision summary"><div class="eyebrow">Assessment of checked conditions</div><h2 class="{title_class}">{esc(report['verdict'])}</h2>
{decision}<div class="tally"><span><b>{counts['BLOCKER']}</b> potential blocker{'s' if counts['BLOCKER']!=1 else ''}</span><span><b>{counts['REVIEW']}</b> review item{'s' if counts['REVIEW']!=1 else ''}</span><span><b>{counts['SATISFIED']}</b> checked match{'es' if counts['SATISFIED']!=1 else ''}</span><span><b>{len(report['unresolved'])}</b> unresolved notes</span></div>
<p class="scope">This is a first-pass screen against the supplied profile. A source quotation supports the finding but does not establish overall eligibility or a legally correct interpretation. Coverage limits are recorded below.</p></section>
<section><h2><span class="section-number">01</span>Requirements register</h2><p class="section-note">Read potential blockers first. Repeated registration citations are grouped; distinct obligations remain separate. Evidence references open the full quotation.</p>
<div class="table-scroll"><table class="register"><thead><tr><th scope="col">Requirement</th><th scope="col">Company profile</th><th scope="col">Assessment</th><th scope="col">Evidence</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
{'' if groups else '<p class="empty">No verified findings. Further review is required.</p>'}</section>
<section><h2><span class="section-number">02</span>Full source quotations</h2><p class="section-note">PDF references use physical page numbers. Word and Excel references use extraction sections. Whitespace is normalized for readability; all quoted words are retained.</p>
{''.join(quotations) or '<p class="empty">No verified quotations available.</p>'}</section>
<section><h2><span class="section-number">03</span>Unresolved evidence &amp; coverage</h2>{issues}</section>
<section><h2><span class="section-number">04</span>Investigation record</h2><p class="section-note">First pass: <strong>{esc(report.get('first_pass_verdict','Not recorded'))}</strong><br>Final: <strong>{esc(report['verdict'])}</strong></p>
<table class="rounds"><thead><tr><th scope="col">Pass</th><th scope="col">New findings</th><th scope="col">Follow-up requests</th></tr></thead><tbody>{''.join(rounds)}</tbody></table>
<p class="run-data">{esc(metrics.get('documents',0))} documents · {esc(metrics.get('elapsed_seconds','Not recorded'))} seconds · {esc(metrics.get('model_calls',0))} model calls · {esc(metrics.get('first_pass_findings',0))} first-pass source findings → {esc(metrics.get('final_findings',0))} final source findings. Counts here precede presentation grouping.</p>{inference_note}</section>
<section class="inventory"><h2><span class="section-number">05</span>Document inventory</h2><p class="section-note">Text extraction does not mean that every page or condition was reviewed.</p>
<table class="documents"><thead><tr><th scope="col">Document</th><th scope="col">Extent</th><th scope="col">Extraction</th></tr></thead><tbody>{''.join(documents)}</tbody></table></section>
<footer>Evidence brief for human review.<br>Files were processed in Daytona and selected excerpts sent to the configured model API. The JSON evidence file retains the complete run record.<p class="screen-only"><button type="button" onclick="window.print()">Print / Save as PDF</button></p></footer>
</main><script>
document.querySelectorAll('.source-links a,.decision-list a').forEach(link=>link.addEventListener('click',()=>{{const target=document.getElementById(link.hash.slice(1));if(target)target.open=true;}}));
let previous=[];addEventListener('beforeprint',()=>{{previous=[...document.querySelectorAll('details')].map(node=>[node,node.open]);previous.forEach(([node])=>node.open=true);}});addEventListener('afterprint',()=>{{previous.forEach(([node,open])=>node.open=open);}});
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('result',type=Path,help='Existing BidBlast JSON result; no API calls are made')
    parser.add_argument('--output',type=Path,help='HTML destination; defaults beside the JSON file')
    args = parser.parse_args()
    report = json.loads(args.result.read_text(encoding='utf-8-sig'))
    output = args.output or args.result.with_suffix('.html')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(render_report(report),encoding='utf-8')
    print(f'HTML report: {output.resolve()}')


if __name__ == '__main__':
    main()
