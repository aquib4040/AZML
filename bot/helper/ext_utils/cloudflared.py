import os
import sys
import re
import time
import shutil
import urllib.request
import subprocess
from logging import getLogger

LOGGER = getLogger("cloudflared")

def check_cloudflared_binary():
    # 1. Check system PATH
    bin_path = shutil.which("cloudflared")
    if bin_path:
        return bin_path
    
    # 2. Check standard Linux install location
    if os.path.exists("/usr/local/bin/cloudflared"):
        return "/usr/local/bin/cloudflared"

    # 3. Check current working directory
    local_bin = os.path.join(os.getcwd(), "cloudflared")
    if sys.platform == "win32":
        local_bin += ".exe"
    if os.path.exists(local_bin):
        return local_bin

    # 4. Auto-download binary if missing
    try:
        LOGGER.info("cloudflared binary not found. Auto-downloading...")
        if sys.platform.startswith("linux"):
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        elif sys.platform == "win32":
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        elif sys.platform == "darwin":
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64"
        else:
            LOGGER.error(f"Unsupported platform for cloudflared: {sys.platform}")
            return None

        urllib.request.urlretrieve(url, local_bin)
        if sys.platform != "win32":
            os.chmod(local_bin, 0o755)
        LOGGER.info(f"Successfully downloaded cloudflared to {local_bin}")
        return local_bin
    except Exception as e:
        LOGGER.error(f"Failed to download cloudflared: {e}")
        return None

_cf_process = None


def start_cloudflared_tunnel(port=85, max_retries=3):
    global _cf_process
    binary = check_cloudflared_binary()
    if not binary:
        LOGGER.error("Cannot start Cloudflare tunnel: cloudflared binary missing.")
        return None

    # Kill any stale cloudflared processes from previous runs
    try:
        if sys.platform != "win32":
            subprocess.run(["pkill", "-f", "cloudflared.*tunnel"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            time.sleep(0.5)
    except Exception:
        pass

    tunnel_port = os.environ.get("CF_PORT", port)
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    for attempt in range(1, max_retries + 1):
        cmd = [binary, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{tunnel_port}"]
        LOGGER.info(f"Launching Cloudflare quick tunnel targeting port {tunnel_port} (Attempt {attempt}/{max_retries})...")

        captured_output = []
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )
            _cf_process = proc
        except Exception as e:
            LOGGER.error(f"Error launching cloudflared process: {e}")
            time.sleep(2)
            continue

        cf_url = None
        start_t = time.time()

        # Wait up to 35 seconds for Cloudflare to return tunnel URL
        while time.time() - start_t < 35:
            if proc.poll() is not None:
                rest, _ = proc.communicate()
                if rest:
                    for l in rest.splitlines():
                        clean_l = l.strip()
                        if clean_l:
                            captured_output.append(clean_l)
                            LOGGER.info(f"[cloudflared] {clean_l}")
                            match = url_pattern.search(clean_l)
                            if match:
                                cf_url = match.group(0)
                break

            line = proc.stdout.readline()
            if not line:
                time.sleep(0.2)
                continue

            clean_line = line.strip()
            captured_output.append(clean_line)
            LOGGER.info(f"[cloudflared] {clean_line}")

            match = url_pattern.search(clean_line)
            if match:
                cf_url = match.group(0)
                LOGGER.info(f"Cloudflare Tunnel successfully connected: {cf_url}")
                return cf_url

        if cf_url:
            return cf_url

        LOGGER.warning(f"Attempt {attempt} failed to establish Cloudflare quick tunnel.")
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

        if attempt < max_retries:
            time.sleep(3)

    LOGGER.error("Failed to retrieve Cloudflare Quick Tunnel URL after all retries.")
    return None
