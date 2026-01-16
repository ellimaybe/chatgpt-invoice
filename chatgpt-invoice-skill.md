# Skill: Download ChatGPT Invoice from Stripe

## Overview
This skill automates the process of retrieving the latest ChatGPT subscription invoice link from Stripe and downloading it as a properly named PDF.

## Steps Performed

### 1. Navigate to ChatGPT Settings
- Go to `chatgpt.com`
- Click the hamburger menu (top left) to expand the sidebar
- Click on the account name in the bottom left corner
- Click "Settings" from the popup menu

### 2. Access Payment Management
- In the Settings dialog, scroll the tab bar to find "Account" tab (it's the last tab)
- Click on "Account" tab
- Scroll down to the "Payment" section
- Click "Manage" button - this opens the Stripe billing portal

### 3. Find Invoice History
- Wait for the Stripe billing page to load (`pay.openai.com`)
- Scroll down to the "INVOICE HISTORY" section
- Identify the latest paid invoice (topmost entry)

### 4. Extract Invoice Link (Without Clicking)
- Use `read_page` tool to get all interactive elements
- Invoice links follow this pattern: `https://invoice.stripe.com/i/acct_.../live_...`
- The first invoice link (ref_4 in this case) corresponds to the latest invoice

### 5. Save the Link
- Create a file named `YYYYMMDD-stripe-link.txt` (using invoice date)
- Save only the URL, nothing else
- Location: User's default Downloads folder

### 6. Run Download Script
- Update `download-stripe-from-url.py` with the new invoice URL
- Run the script which:
  - Opens the invoice page headlessly with Playwright
  - Clicks "Download receipt" button
  - Extracts payment date and amount from the page
  - Saves PDF as `YYYYMMDD-elena-chatgpt-invoice-XXUSD.pdf`

## Output Files
- `%USERPROFILE%\Downloads\20251225-stripe-link.txt` - The Stripe invoice link
- `...\invoices\20251225-elena-chatgpt-invoice-25USD.pdf` - The downloaded invoice

---

## Suggested Improvements

### 1. Accept Command-Line Arguments in Script
**Current:** The script has a hardcoded URL that needs manual editing.

**Better:** Accept URL as a command-line argument or read from a file.

```python
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        invoice_url = sys.argv[1]
    else:
        # Read from the link file
        with open(r"%USERPROFILE%\Downloads\20251225-stripe-link.txt") as f:
            invoice_url = f.read().strip()

    download_invoice(invoice_url, r"...\invoices")
```

### 2. Dynamic Link File Reading
**Current:** The link file name is hardcoded with a specific date.

**Better:** Find the most recent `*-stripe-link.txt` file automatically.

```python
import glob
link_files = sorted(glob.glob(r"%USERPROFILE%\Downloads\*-stripe-link.txt"))
if link_files:
    latest_link_file = link_files[-1]
```

### 3. Direct URL Navigation
**Current:** Navigate through multiple UI clicks (Settings → Account → Manage).

**Better:** The Stripe billing portal URL pattern could potentially be bookmarked or accessed directly if the session URL structure is predictable (though it uses session tokens).

### 4. Batch Invoice Download
**Current:** Downloads one invoice at a time.

**Better:** Add option to download all invoices or invoices within a date range.

```python
def download_all_invoices(invoice_urls, download_path):
    for url in invoice_urls:
        download_invoice(url, download_path)
```

### 5. Remove Debug Output in Production
**Current:** Script prints extensive debug information.

**Better:** Add a `--verbose` or `--debug` flag to control output.

```python
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')
args = parser.parse_args()

if args.debug:
    print(f"[DEBUG] ...")
```

### 6. Error Handling for Link Extraction
**Current:** Assumes the first invoice link is the latest.

**Better:** Parse the invoice date from the page to verify which is truly the latest.

### 7. Configuration File
**Current:** Paths are hardcoded in the script.

**Better:** Use a config file or environment variables.

```python
# config.json
{
    "download_path": "%USERPROFILE%\\...\\invoices",
    "link_save_path": "%USERPROFILE%\\Downloads",
    "filename_template": "{date}-elena-chatgpt-invoice-{amount}.pdf"
}
```

### 8. Combined Automation Script
**Better:** Create a single script that does everything:
1. Uses browser automation to navigate to Stripe
2. Extracts all invoice links
3. Downloads each invoice
4. No need for intermediate link file

This would eliminate the two-step process and manual intervention.
