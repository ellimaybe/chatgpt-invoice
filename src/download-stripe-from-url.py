from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import os
import re
import sys
import argparse
import glob
import getpass
from datetime import datetime
from pathlib import Path

def download_invoice(invoice_url, download_path="./"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Silent mode - no browser window
        try:
            page = browser.new_page()
            page.goto(invoice_url, timeout=30000)

            # Wait for DOM to be ready (not networkidle - Stripe keeps connections open)
            page.wait_for_load_state("domcontentloaded")

            # Wait for the download button to appear (this is the key element we need)
            receipt_selector = '[data-testid="download-invoice-receipt-pdf-button"]'
            page.wait_for_selector(receipt_selector, state="visible", timeout=15000)

            # Selectors for download buttons
            invoice_selector = 'button:has-text("Download invoice")'

            # Function to find button in main page or iframes
            def find_download_button():
                # First check main page
                if page.locator(receipt_selector).count() > 0 and page.locator(receipt_selector).is_visible():
                    return page, receipt_selector
                if page.locator(invoice_selector).count() > 0 and page.locator(invoice_selector).is_visible():
                    return page, invoice_selector

                # Check all iframes
                for frame in page.frames:
                    if frame == page.main_frame:
                        continue
                    try:
                        if frame.locator(receipt_selector).count() > 0 and frame.locator(receipt_selector).is_visible():
                            return frame, receipt_selector
                        if frame.locator(invoice_selector).count() > 0 and frame.locator(invoice_selector).is_visible():
                            return frame, invoice_selector
                    except:
                        continue

                return None, None

            target_frame, selector = find_download_button()

            if not target_frame:
                raise Exception("No download button found on page or in iframes")
            # Click the download button
            with page.expect_download(timeout=15000) as download_info:
                target_frame.click(selector)

            download = download_info.value

            # Extract Payment Date from the page
            # Look for the date in the page content
            page_content = page.content()

            # Try to find "Payment date" or "Date paid" followed by a date
            # Common formats: "Dec 25, 2025", "December 25, 2025", "2025-12-25"
            payment_date = None

            # Look for date in the InvoiceDetails table after "Payment date"
            # HTML structure: <span>Payment date</span>...</td><td>...<span>December 25, 2025</span>
            date_pattern = r'Payment date</span></td><td[^>]*><span[^>]*>(\w+\s+\d{1,2},?\s+\d{4})</span>'
            match = re.search(date_pattern, page_content, re.IGNORECASE)

            if match:
                date_str = match.group(1)
                # Try to parse the date
                for fmt in ["%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y", "%Y-%m-%d"]:
                    try:
                        parsed_date = datetime.strptime(date_str.replace(",", ""), fmt.replace(",", ""))
                        payment_date = parsed_date.strftime("%Y%m%d")
                        break
                    except ValueError:
                        continue

            if not payment_date:
                # Fallback: use today's date
                payment_date = datetime.now().strftime("%Y%m%d")

            # Extract the amount paid from the page
            # HTML: <span class="CurrencyAmount">$25.00</span>
            amount_str = ""
            amount_pattern = r'data-testid="invoice-amount-post-payment"[^>]*><span class="CurrencyAmount">\$?([\d.]+)</span>'
            amount_match = re.search(amount_pattern, page_content)
            if amount_match:
                amount_value = amount_match.group(1)
                # Remove decimal part if it's .00
                if amount_value.endswith('.00'):
                    amount_value = amount_value[:-3]
                amount_str = f"-{amount_value}USD"

            # Create the new filename
            username = getpass.getuser()
            new_filename = f"{payment_date}-{username}-chatgpt-invoice{amount_str}.pdf"

            # Create download path if it doesn't exist
            os.makedirs(download_path, exist_ok=True)

            save_path = os.path.join(download_path, new_filename)
            download.save_as(save_path)
            print(f"Invoice saved to: {save_path}")

        except PlaywrightTimeout as e:
            print(f"Timeout error: {e}")
        except Exception as e:
            print(f"Error downloading invoice: {e}")
        finally:
            browser.close()

DEFAULT_DOWNLOAD_PATH = (
    Path.home()
    / "sfm-berlin.de"
    / "SFM shared - Documents"
    / "Accounting"
    / f"{os.environ.get('SFM_RECEIPTS_USER', getpass.getuser())} - receipts"
    / str(datetime.now().year)
)
DEFAULT_LINK_DIR = Path.home() / "Downloads"

def find_latest_link_file(directory):
    """Find the most recent *-stripe-link.txt file in the directory."""
    pattern = os.path.join(directory, "*-stripe-link.txt")
    files = sorted(glob.glob(pattern))
    if files:
        return files[-1]
    return None

def read_url_from_file(filepath):
    """Read URL from a text file."""
    with open(filepath, 'r') as f:
        return f.read().strip()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download ChatGPT invoice from Stripe URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src\\download-stripe-from-url.py "https://invoice.stripe.com/..."
  python src\\download-stripe-from-url.py --file 20251225-stripe-link.txt
  python src\\download-stripe-from-url.py --latest
  python src\\download-stripe-from-url.py "https://..." --output ./my-invoices
        """
    )
    parser.add_argument('url', nargs='?', help='Stripe invoice URL')
    parser.add_argument('--file', '-f', help='Read URL from a text file')
    parser.add_argument('--latest', '-l', action='store_true',
                        help='Use the latest *-stripe-link.txt file from Downloads')
    parser.add_argument('--output', '-o', default=DEFAULT_DOWNLOAD_PATH,
                        help=f'Output directory for PDF (default: {DEFAULT_DOWNLOAD_PATH})')

    args = parser.parse_args()

    invoice_url = None

    # Priority: direct URL > --file > --latest
    if args.url:
        invoice_url = args.url
        print(f"Using URL from command line")
    elif args.file:
        invoice_url = read_url_from_file(args.file)
        print(f"Read URL from file: {args.file}")
    elif args.latest:
        link_file = find_latest_link_file(DEFAULT_LINK_DIR)
        if link_file:
            invoice_url = read_url_from_file(link_file)
            print(f"Read URL from latest file: {link_file}")
        else:
            print(f"Error: No *-stripe-link.txt files found in {DEFAULT_LINK_DIR}")
            sys.exit(1)
    else:
        # No arguments - try to find latest link file
        link_file = find_latest_link_file(DEFAULT_LINK_DIR)
        if link_file:
            invoice_url = read_url_from_file(link_file)
            print(f"Read URL from latest file: {link_file}")
        else:
            parser.print_help()
            print("\nError: No URL provided and no *-stripe-link.txt files found")
            sys.exit(1)

    download_invoice(invoice_url, args.output)
