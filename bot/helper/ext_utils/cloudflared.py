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

def start_cloudflared_tunnel(port=85):
    binary = check_cloudflared_binary()
    if not binary:
        LOGGER.error("Cannot start Cloudflare tunnel: cloudflared binary missing.")
        return None

    # Use environment override if provided, otherwise default to 11687
    tunnel_port = os.environ.get("CF_PORT", port)
    cmd = [binary, "tunnel", "--url", f"http://localhost:{tunnel_port}"]
    LOGGER.info(f"Launching Cloudflare quick tunnel targeting port {tunnel_port}...")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
    except Exception as e:
        LOGGER.error(f"Error launching cloudflared process: {e}")
        return None

    cf_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    start_t = time.time()

    # Wait up to 30 seconds for Cloudflare to return tunnel URL
    while time.time() - start_t < 30:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                break
            time.sleep(0.5)
            continue

        LOGGER.debug(f"[cloudflared] {line.strip()}")
        match = url_pattern.search(line)
        if match:
            cf_url = match.group(0)
            LOGGER.info(f"Cloudflare Tunnel successfully connected: {cf_url}")
            break

    if not cf_url:
        LOGGER.error("Failed to retrieve Cloudflare Quick Tunnel URL.")

    return cf_url
