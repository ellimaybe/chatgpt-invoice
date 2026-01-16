"""
Extract the first invoice link from a pay.openai.com session URL.
"""
from playwright.sync_api import sync_playwright
import argparse
import glob
import os
import sys
from pathlib import Path

DEFAULT_LINK_DIR = Path.home() / "Downloads"

def find_latest_pay_link_file(directory):
    """Find the most recent *-pay-link.txt file in the directory."""
    pattern = os.path.join(directory, "*-pay-link.txt")
    files = sorted(glob.glob(pattern))
    if files:
        return files[-1]
    return None

def read_url_from_file(filepath):
    """Read URL from a text file."""
    with open(filepath, 'r') as f:
        return f.read().strip()

def get_invoice_link(url, headless=True):
    """Open a pay.openai.com URL and extract the first invoice link."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        try:
            page.goto(url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")

            # Wait for invoice links to appear
            invoice_link_selector = 'a[data-testid="hip-link"]'
            page.wait_for_selector(invoice_link_selector, state="visible", timeout=10000)

            # Get the first invoice link
            first_invoice = page.locator(invoice_link_selector).first
            invoice_url = first_invoice.get_attribute("href")

            if invoice_url:
                print(invoice_url)
                return invoice_url
            else:
                print("Error: Could not extract href from invoice link", file=sys.stderr)
                return None

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return None
        finally:
            browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract Stripe invoice link from pay.openai.com session URL"
    )
    parser.add_argument('url', nargs='?', help='pay.openai.com session URL')
    parser.add_argument('--latest', '-l', action='store_true',
                        help='Use the latest *-pay-link.txt file from Downloads')
    args = parser.parse_args()

    pay_url = None

    if args.url:
        pay_url = args.url
    elif args.latest:
        link_file = find_latest_pay_link_file(DEFAULT_LINK_DIR)
        if link_file:
            pay_url = read_url_from_file(link_file)
        else:
            print(f"Error: No *-pay-link.txt files found in {DEFAULT_LINK_DIR}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

    result = get_invoice_link(pay_url, headless=True)
    sys.exit(0 if result else 1)
