# BidBlast

BidBlast screens tender documents against the bidder details in [COMPANY.md](COMPANY.md), flags potential eligibility blockers, and shows the source quotations behind its findings.

**Daytona** runs document extraction and follow-up reads. **Muse Glimmer 30B on Nosana** identifies candidate requirements. Local rules check quotations and compare supported requirements with the company details. Results appear in the terminal and a standalone HTML report.

## Setup

Tested on Python 3.14.5. Use Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Configure `.env`:

```dotenv
DAYTONA_API_KEY=your-daytona-key
NOSANA_API_KEY=your-nosana-key
MODEL_API_BASE_URL=https://your-nosana-deployment-endpoint/v1/
MODEL_API_MODEL=muse-glimmer:30b
MODEL_API_KEY=nosana-deployment
```

Use Nosana's **Muse Glimmer 30B** deployment template and wait for its endpoint to be online. The tested deployment uses Ollama 0.32.9, a 48 GB GPU and a 32K context window. Copy its endpoint into `MODEL_API_BASE_URL`, including `/v1/`.

For this Ollama deployment, `MODEL_API_KEY` is a nonsecret client placeholder. `NOSANA_API_KEY` is for managing the deployment and is not sent to the model endpoint. Restart stopped or expired deployments and update the endpoint if it changes. Credentials and local output are excluded from version control.

## Company details

Edit [COMPANY.md](COMPANY.md) before reviewing a tender. The included company is fictional.

BidBlast reads the file on every run. It supports simple `Name:`, `Registrations` and `Certifications` bullet sections, plus the numbered company overview, registration/licence and certification tables in the supplied document. It compares BCA grades and supported named certifications; other company facts remain for human review. Unknown information stays unresolved.

## Run a tender

Place PDF, DOCX, DOC or XLSX files in a folder, then run:

```powershell
.\.venv\Scripts\python.exe bidblast.py Temasek --output output/temasek
```

Replace `Temasek` with your tender folder, such as `PUB`. Only top-level supported files are processed; subfolders are excluded. Tender packs are local data and are not included in the public source.

To generate and run the original synthetic example:

```powershell
.\.venv\Scripts\python.exe make_demo.py
.\.venv\Scripts\python.exe bidblast.py demo --output output/demo
```

The demo includes an FM02 L6 requirement and a reference to a later certification clause. The agent investigates the reference and updates its findings. The company details still come from `COMPANY.md`; the demo generator does not overwrite them.

## Read the results

Open the HTML path printed at the end of the run, such as `output/temasek.html`. It contains the assessment, company details, requirements register, linked quotations, coverage gaps and investigation history. The **Print / Save as PDF** action is in the footer.

- **NO-GO (identified blocker):** a checked requirement conflicts with the company details.
- **REVIEW REQUIRED:** evidence, applicability, company information or coverage needs review.
- **NO BLOCKER DETECTED IN CHECKED CONDITIONS:** no mismatch was identified in the checked conditions; this does not establish overall eligibility.

The matching JSON file preserves full evidence, model/endpoint details and sandbox lifecycle events. To generate HTML from an existing result without API calls:

```powershell
.\.venv\Scripts\python.exe report_html.py output/temasek.json
```

## Limits and data handling

This is a first-pass screen for human review. Matching a quotation does not prove its interpretation or complete document coverage. Investigation is limited to two follow-up rounds, and incomplete coverage is reported. OCR is not supported; Excel formulas are not recalculated. PDF references use physical pages; Word and Excel use extraction sections.

Documents are uploaded to Daytona and selected excerpts sent to the configured model endpoint. The Daytona sandbox is deleted after a run, including processing failures after creation. The Nosana model deployment has its own lifecycle and billing. Use synthetic or authorised documents for public demos.

## Source files

| File | Purpose |
|---|---|
| `bidblast.py` | Terminal workflow, Daytona integration, model calls, evidence checks and comparison rules |
| `inspect_file.py` | Document extraction and targeted reads inside Daytona |
| `report_html.py` | Standalone HTML report generation |
| `COMPANY.md` | Bidder details read at the start of each run |
| `make_demo.py` | Generates the synthetic tender pack |
| `.env.example`, `requirements.txt` | Configuration template and dependencies |
