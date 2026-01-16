ChatGPT Invoice Downloader (Windows)

Prerequisites (one-time):
1) Install Claude Code CLI and sign in
2) Install the Claude Chrome extension and sign in
3) Ensure you can access chatgpt.com in Chrome

Setup (one-time):
1) Open PowerShell in this folder
2) Run: .\setup.ps1
   - This attempts to install Python 3.12 via winget
   - If it fails, install Python manually, then re-run setup

Run:
- .\run.ps1

Notes:
- The script uses Claude Code with Chrome to extract the invoice link
- Downloads are saved to the default output path in download-stripe-from-url.py
