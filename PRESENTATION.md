# BidBlast — Terminal demo narrative

Use the original synthetic pack for the public demonstration. Describe only behavior actually shown in a live or clearly labelled recorded run.

A bid team can spend time preparing a tender response before discovering a mandatory requirement the company does not meet. BidBlast screens the documents early and shows the evidence behind potential blockers.

The supplied `COMPANY.md` describes a fictional company holding FM02 L5 and bizSAFE Level 3. The application reads that file at the start of the run:

```powershell
.\.venv\Scripts\python.exe bidblast.py demo --output output/demo
```

Daytona creates a sandbox, receives the two PDFs and executes text extraction. Muse Glimmer 30B, served on a Nosana GPU, identifies candidate requirements; source checks verify its quotations, and explicit rules compare supported requirements with the company details in `COMPANY.md`.

The first pass finds the FM02 L6 requirement and flags the mismatch with the L5 company. Coverage remains incomplete because the second document has unread pages.

The evaluation document directs bidders to physical page 3 of the contract conditions. The agent follows that reference in the same live sandbox and discovers two more requirements: bizSAFE Level 4 at submission, and a 5% security deposit before commencement.

`COMPANY.md` lists bizSAFE Level 3, so the named certification check flags an additional potential blocker. The deposit remains a condition for human review. The terminal shows the quotation, document and page behind each finding, then records the sandbox deletion and final assessment. The HTML report identifies the company file used.

That is the investigation loop: inspect, verify, read the referenced evidence and update the findings. The follow-up target comes from the document rather than a hardcoded page in the application.

The tool also processes the eight-file local Temasek Polytechnic pack. It has identified the FM02 L6 requirement in the evaluation criteria and compliance table against a fictional L5 profile. Use the synthetic pack for the public demonstration; keep local tender documents and their private output out of the public repository.

BidBlast is a first-pass screen. Matching quotations does not prove interpretation or complete coverage. Unresolved requirements and unread content remain visible for the bid manager's review.

**BidBlast: identify potential reasons you cannot bid before spending days preparing the bid.**
