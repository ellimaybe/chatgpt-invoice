import argparse
import sys

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


DEFAULT_URL = "https://chatgpt.com/#settings/Account"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Attach to an existing Chrome session and click the Payment -> Manage button.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9222,
        help="Remote debugging port (default: 9222).",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Target URL (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Timeout in seconds for UI waits (default: 15).",
    )
    parser.add_argument(
        "--pause",
        action="store_true",
        help="Pause after clicking Manage until you press Enter.",
    )
    return parser.parse_args()


def find_manage_button(page, timeout_ms):
    try:
        payment_label = page.get_by_text("Payment", exact=True).first
        payment_row = payment_label.locator("..").locator("..")
        manage_button = payment_row.get_by_role("button", name="Manage")
        manage_button.wait_for(state="visible", timeout=timeout_ms)
        return manage_button
    except PlaywrightTimeout:
        manage_button = page.get_by_role("button", name="Manage").first
        manage_button.wait_for(state="visible", timeout=timeout_ms)
        return manage_button


def main():
    args = parse_args()
    timeout_ms = int(args.timeout * 1000)
    endpoint = f"http://127.0.0.1:{args.port}"

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(endpoint)
        except Exception as exc:
            print(f"Failed to connect to Chrome at {endpoint}: {exc}", file=sys.stderr)
            print("Launch Chrome with --remote-debugging-port first.", file=sys.stderr)
            return 1

        if not browser.contexts:
            context = browser.new_context()
        else:
            context = browser.contexts[0]

        target_page = None
        for page in context.pages:
            if "chatgpt.com" in (page.url or ""):
                target_page = page
                break

        if not target_page:
            target_page = context.new_page()

        target_page.goto(args.url, wait_until="domcontentloaded")

        try:
            manage_button = find_manage_button(target_page, timeout_ms)
        except PlaywrightTimeout:
            print(
                "Manage button not found. Make sure you're logged in and the page finished loading.",
                file=sys.stderr,
            )
            return 1

        before_count = len(context.pages)
        manage_button.click()

        new_page = None
        try:
            context.wait_for_event("page", timeout=timeout_ms)
        except PlaywrightTimeout:
            pass

        if len(context.pages) > before_count:
            new_page = context.pages[-1]

        if new_page:
            new_page.wait_for_load_state("domcontentloaded")
            print(f"Billing page URL: {new_page.url}")
        else:
            target_page.wait_for_load_state("domcontentloaded")
            print(f"Billing page URL: {target_page.url}")

        if args.pause:
            input("Press Enter to finish...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
