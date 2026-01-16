import argparse
import os
import shutil
import subprocess
import sys
import time
from urllib.request import urlopen
from urllib.error import URLError


DEFAULT_URL = "https://chatgpt.com/#settings/Account"
DEFAULT_CDP_TIMEOUT = 6.0


def find_chrome_exe():
    path = shutil.which("chrome") or shutil.which("chrome.exe")
    if path:
        return path

    candidates = []
    for env_var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        root = os.environ.get(env_var)
        if not root:
            continue
        candidates.append(os.path.join(root, "Google", "Chrome", "Application", "chrome.exe"))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Open ChatGPT account settings in Chrome without automating login.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Target URL (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--chrome-path",
        help="Full path to chrome.exe if it is not in PATH.",
    )
    parser.add_argument(
        "--user-data-dir",
        help="Chrome user data dir (optional).",
    )
    parser.add_argument(
        "--profile-dir",
        help="Chrome profile directory name (e.g., Default or Profile 1).",
    )
    parser.add_argument(
        "--incognito",
        action="store_true",
        help="Open in an incognito window.",
    )
    parser.add_argument(
        "--guest",
        action="store_true",
        help="Open in Chrome guest mode (ignores --profile-dir).",
    )
    parser.add_argument(
        "--remote-debugging-port",
        type=int,
        help="Enable remote debugging on the given port (for automation attach).",
    )
    parser.add_argument(
        "--cdp-timeout",
        type=float,
        default=DEFAULT_CDP_TIMEOUT,
        help=f"Seconds to wait for CDP to come up (default: {DEFAULT_CDP_TIMEOUT}).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    chrome_exe = args.chrome_path or find_chrome_exe()
    if not chrome_exe:
        print("Chrome not found. Install it or pass --chrome-path.", file=sys.stderr)
        return 1

    command = [chrome_exe, "--new-window"]
    if args.remote_debugging_port:
        command.append(f"--remote-debugging-port={args.remote_debugging_port}")
    if args.user_data_dir:
        command.append(f"--user-data-dir={args.user_data_dir}")
    if args.guest:
        command.append("--guest")
    elif args.profile_dir:
        command.append(f"--profile-directory={args.profile_dir}")
    if args.incognito:
        command.append("--incognito")
    command.append(args.url)

    subprocess.Popen(command, close_fds=True)

    if args.remote_debugging_port:
        if wait_for_cdp(args.remote_debugging_port, args.cdp_timeout):
            print(f"CDP is up at http://127.0.0.1:{args.remote_debugging_port}")
        else:
            print(
                f"CDP did not come up at http://127.0.0.1:{args.remote_debugging_port}",
                file=sys.stderr,
            )
    return 0


def wait_for_cdp(port, timeout_seconds):
    deadline = time.time() + max(timeout_seconds, 0)
    url = f"http://127.0.0.1:{port}/json/version"
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except URLError:
            time.sleep(0.2)
    return False


if __name__ == "__main__":
    raise SystemExit(main())
