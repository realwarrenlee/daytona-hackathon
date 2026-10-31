# Demo runbook

Commands and screen checklist. Narration is in [PRESENTATION.md](PRESENTATION.md).

## Before presenting

Open PowerShell in the project folder:

```powershell
cd "C:\Users\Warren\Documents\Daytona Hackathon"
```

- Confirm the Nosana **BidBlast - Muse Glimmer 30B** deployment is running and its endpoint is online. Update `.env` if the endpoint changed; keep `.env` off screen.
- Keep the Daytona Sandboxes and Nosana Deployments pages open for the sponsor demonstration.
- Use the synthetic pack for the public demo. Setup instructions are in [README.md](README.md).

Check that the configured model is available before presenting:

```powershell
.\.venv\Scripts\python.exe -c "from dotenv import load_dotenv; load_dotenv('.env'); from bidblast import Model; m=Model(); assert any(x.id==m.name for x in m.client.models.list().data), 'Configured model unavailable'; print('Model endpoint ready:', m.name)"
```

The initial Nosana deployment has a 60-minute runtime. Check its remaining time in Nosana and restart it before presenting if necessary; a working endpoint now does not guarantee it stays online later.

The PDF demo prepares only its PDF dependency, which is already installed in the tested default Daytona image. Word and Excel packs may still need package downloads; the earlier setup failure was caused by intermittent PyPI DNS resolution in a sandbox.

Generate the two demo PDFs and prepare the output folder:

```powershell
.\.venv\Scripts\python.exe make_demo.py
New-Item -ItemType Directory -Force output | Out-Null
```

## 1. Show the company being checked

Display the values actually read from `COMPANY.md`:

```powershell
.\.venv\Scripts\python.exe -c "from bidblast import load_company; c=load_company('COMPANY.md'); print(c['name']); print('FM02:', c.get('registration', {}).get('FM02', 'Unknown')); print('Certifications:', ', '.join(c.get('certifications', [])))"
```

For the supplied fictional company, highlight **FM02 L5** and **bizSAFE Level 3**. The other declared licences and certifications may also appear.

## 2. Run the live review

```powershell
& {
    .\.venv\Scripts\python.exe -u bidblast.py demo --output output/live-demo 2>&1 | Tee-Object -FilePath output/live-demo.log
    if ($LASTEXITCODE -ne 0) { throw 'Review failed. Do not present an older report as this run; use the labelled fallback below.' }
    Start-Process .\output\live-demo.html
}
```

The verified Glimmer demo took about one minute; allow for service latency. Watch for:

1. `Company details: ... COMPANY.md` and `Model: muse-glimmer:30b`.
2. A real Daytona sandbox ID, followed by PDF uploads and extraction.
3. First-pass **FM02 L6 required / company L5** blocker.
4. `Re-investigating ... 02_Contract_Conditions.pdf` after the document reference.
5. A further **bizSAFE Level 4 required / company Level 3** blocker.
6. A **5% security deposit** condition marked for review.
7. `Daytona sandbox deleted` and the final **NO-GO (identified blocker)** assessment.

Additional review items and finding counts can vary between model runs.

**While extraction is running:** refresh Daytona Sandboxes and match the ID shown in the terminal. The sandbox is deleted when the review finishes, so it should disappear afterwards. Nosana's model deployment has a separate lifecycle and remains running until stopped or timed out.

## 3. Show the HTML report

The command block above opens the HTML only after a successful review. If it fails, inspect the terminal/log or use the labelled fallback below.

Show these parts:

- **Company details source:** `COMPANY.md`, with the bidder's declared holdings.
- **Decision and requirements register:** potential blockers separated from review items.
- **Evidence links:** open a source quotation and show its document and physical page.
- **Investigation record:** first-pass findings, follow-up requests and final findings; the actual model and endpoint used.
- **Unresolved evidence and coverage:** what still needs human review.
- **Print / Save as PDF:** available in the footer if needed.

The full evidence is also saved to `output/live-demo.json`, and the terminal transcript to `output/live-demo.log`.

## Optional: run the local Temasek tender

This is a longer demonstration using the eight top-level documents in `Temasek`. The verified Glimmer run took about three minutes. Its report contains local tender text; use it only in an authorised walkthrough.

```powershell
.\.venv\Scripts\python.exe -u bidblast.py Temasek --output output/temasek
Start-Process .\output\temasek.html
```

Highlight the FM02 L6 requirement in the evaluation criteria against the company's L5 registration. Show the coverage gaps as well as the blocker. The `_unused` subfolder is excluded.

## Fallback: previously completed results

If a live service is unavailable, open an existing report and identify it as a **previously completed run**:

```powershell
Start-Process .\output\glimmer-demo.html
```

Or the previously completed real-pack report:

```powershell
Start-Process .\output\glimmer-temasek.html
```

These files are local run artifacts and are not included in the public repository. If only a saved JSON result is available, rebuild its HTML without model or Daytona calls:

```powershell
.\.venv\Scripts\python.exe report_html.py output/glimmer-demo.json
Start-Process .\output\glimmer-demo.html
```
