import argparse
import os
import shutil
import sys
import tempfile
import subprocess

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


DEFAULT_URL = "https://chatgpt.com/#settings/Account"


def default_user_data_dir():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None
    return os.path.join(local_app_data, "Google", "Chrome", "User Data")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Open ChatGPT account settings and click the Payment -> Manage button.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Target URL (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--user-data-dir",
        help="Chrome user data dir (defaults to LOCALAPPDATA Chrome path).",
    )
    parser.add_argument(
        "--profile-dir",
        help="Chrome profile directory name (e.g., Default or Profile 1).",
    )
    parser.add_argument(
        "--copy-profile",
        action="store_true",
        help="Copy the profile to a temp folder to avoid closing Chrome.",
    )
    parser.add_argument(
        "--profile-copy-dir",
        help="Persistent user data dir for a copied profile (reused across runs).",
    )
    parser.add_argument(
        "--refresh-profile-copy",
        action="store_true",
        help="Overwrite files in --profile-copy-dir with a fresh copy.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary profile copy on disk.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without showing the browser window.",
    )
    parser.add_argument(
        "--skip-chrome-check",
        action="store_true",
        help="Skip verifying that Chrome is closed before running.",
    )
    parser.add_argument(
        "--stealth",
        action="store_true",
        help="Apply stealthy browser tweaks (UA/webdriver/plugins).",
    )
    parser.add_argument(
        "--user-agent",
        help="Override the browser user agent string.",
    )
    parser.add_argument(
        "--lang",
        default="en-US",
        help="Navigator language/locale (default: en-US).",
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


def is_locked_error(exc):
    winerror = getattr(exc, "winerror", None)
    if winerror in (32, 33):
        return True
    errno = getattr(exc, "errno", None)
    return errno in (13,)


def copy_profile_to_dir(source_user_data_dir, profile_dir, target_user_data_dir):
    os.makedirs(target_user_data_dir, exist_ok=True)

    local_state_src = os.path.join(source_user_data_dir, "Local State")
    if os.path.isfile(local_state_src):
        try:
            shutil.copy2(local_state_src, os.path.join(target_user_data_dir, "Local State"))
        except OSError as exc:
            if not is_locked_error(exc):
                raise

    source_profile_dir = os.path.join(source_user_data_dir, profile_dir)
    if not os.path.isdir(source_profile_dir):
        raise FileNotFoundError(f"Profile directory not found: {source_profile_dir}")

    ignored_dirs = {
        "Cache",
        "Code Cache",
        "GPUCache",
        "Media Cache",
        "Service Worker",
        "ShaderCache",
    }

    dest_profile_dir = os.path.join(target_user_data_dir, profile_dir)
    skipped = []
    for root, dirs, files in os.walk(source_profile_dir):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        rel_root = os.path.relpath(root, source_profile_dir)
        dest_root = dest_profile_dir if rel_root == "." else os.path.join(dest_profile_dir, rel_root)
        os.makedirs(dest_root, exist_ok=True)
        for filename in files:
            src_path = os.path.join(root, filename)
            dst_path = os.path.join(dest_root, filename)
            try:
                shutil.copy2(src_path, dst_path)
            except OSError as exc:
                if is_locked_error(exc):
                    skipped.append(src_path)
                    continue
                raise

    return skipped


def copy_profile_to_temp(user_data_dir, profile_dir):
    temp_root = tempfile.mkdtemp(prefix="chrome-profile-")
    skipped = copy_profile_to_dir(user_data_dir, profile_dir, temp_root)
    return temp_root, skipped


def is_chrome_running():
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq chrome.exe"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None

    output = (result.stdout or "") + (result.stderr or "")
    return "chrome.exe" in output.lower()


def add_stealth_init_script(context, language):
    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => [LANG] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        window.chrome = window.chrome || { runtime: {} };
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters)
        );
        """.replace("LANG", repr(language))
    )


def main():
    args = parse_args()
    timeout_ms = int(args.timeout * 1000)
    user_data_dir = args.user_data_dir or default_user_data_dir()
    if not user_data_dir or not os.path.isdir(user_data_dir):
        print(
            "Chrome user data dir not found. Pass --user-data-dir to your Chrome profile.",
            file=sys.stderr,
        )
        return 1

    if not args.skip_chrome_check:
        chrome_running = is_chrome_running()
        if chrome_running is None:
            print(
                "Warning: Unable to verify Chrome is closed. Proceeding anyway.",
                file=sys.stderr,
            )
        elif chrome_running:
            print(
                "Chrome is running. Close all Chrome windows before continuing.",
                file=sys.stderr,
            )
            print("Use --skip-chrome-check to bypass this check.", file=sys.stderr)
            return 1

    profile_dir = args.profile_dir
    temp_root = None
    if args.copy_profile and args.profile_copy_dir:
        print(
            "Use either --copy-profile or --profile-copy-dir, not both.",
            file=sys.stderr,
        )
        return 1

    if args.profile_copy_dir:
        profile_dir = profile_dir or "Default"
        profile_copy_dir = os.path.abspath(args.profile_copy_dir)
        needs_copy = args.refresh_profile_copy or not os.path.isdir(
            os.path.join(profile_copy_dir, profile_dir)
        )
        if needs_copy:
            try:
                skipped = copy_profile_to_dir(user_data_dir, profile_dir, profile_copy_dir)
            except Exception as exc:
                print(f"Failed to copy Chrome profile: {exc}", file=sys.stderr)
                return 1
            if skipped:
                print(
                    f"Skipped {len(skipped)} locked files while copying the profile. "
                    "If you get logged out, close Chrome and run with --refresh-profile-copy.",
                    file=sys.stderr,
                )
        user_data_dir = profile_copy_dir
    elif args.copy_profile:
        profile_dir = profile_dir or "Default"
        try:
            user_data_dir, skipped = copy_profile_to_temp(user_data_dir, profile_dir)
        except Exception as exc:
            print(f"Failed to copy Chrome profile: {exc}", file=sys.stderr)
            return 1
        if skipped:
            print(
                f"Skipped {len(skipped)} locked files while copying the profile. "
                "If you get logged out, close Chrome and retry without --copy-profile.",
                file=sys.stderr,
            )

    launch_args = []
    if profile_dir:
        launch_args.append(f"--profile-directory={profile_dir}")
    if args.stealth:
        launch_args.extend(
            [
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        )

    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir,
                channel="chrome",
                headless=args.headless,
                args=launch_args,
                locale=args.lang or None,
                user_agent=args.user_agent or None,
            )
        except Exception as exc:
            print(f"Failed to launch Chrome: {exc}", file=sys.stderr)
            print(
                "Close other Chrome windows or use a different profile directory.",
                file=sys.stderr,
            )
            return 1

        try:
            if args.stealth:
                add_stealth_init_script(context, args.lang)
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(args.url, wait_until="domcontentloaded")

            try:
                manage_button = find_manage_button(page, timeout_ms)
            except PlaywrightTimeout:
                print(
                    "Manage button not found. Make sure you're logged in and the page finished loading.",
                    file=sys.stderr,
                )
                context.close()
                return 1

            before_count = len(context.pages)
            manage_button.click()

            target_page = page
            try:
                context.wait_for_event("page", timeout=timeout_ms)
            except PlaywrightTimeout:
                pass

            if len(context.pages) > before_count:
                target_page = context.pages[-1]
            target_page.wait_for_load_state("domcontentloaded")
            print(f"Billing page URL: {target_page.url}")

            if args.pause:
                input("Press Enter to close the browser...")
            context.close()
        finally:
            if temp_root and not args.keep_temp:
                shutil.rmtree(temp_root, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
