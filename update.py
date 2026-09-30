from logging import (
    FileHandler,
    StreamHandler,
    INFO,
    basicConfig,
    error as log_error,
    info as log_info,
)
from os import path as ospath, environ, remove
from glob import glob
from subprocess import run as srun, call as scall
from importlib.metadata import distributions
from shutil import which as shutil_which
import hashlib
from requests import get as rget
from dotenv import load_dotenv, dotenv_values
from pymongo import MongoClient

if ospath.exists("log.txt"):
    with open("log.txt", "r+") as f:
        f.truncate(0)

if ospath.exists("rlog.txt"):
    remove("rlog.txt")

for f in glob("*.session*"):
    try:
        remove(f)
    except Exception:
        pass

basicConfig(
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%d-%b-%y %I:%M:%S %p",
    handlers=[FileHandler("log.txt"), StreamHandler()],
    level=INFO,
)

if ospath.exists("config.env"):
    load_dotenv("config.env", override=False)

try:
    if bool(environ.get("_____REMOVE_THIS_LINE_____")):
        log_error("The README.md file there to be read! Exiting now!")
        exit()
except Exception:
    pass

BOT_TOKEN = environ.get("BOT_TOKEN", "")
if len(BOT_TOKEN) == 0:
    log_error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

bot_id = BOT_TOKEN.split(":", 1)[0]

DATABASE_URL = environ.get("DATABASE_URL", "")
if len(DATABASE_URL) == 0:
    DATABASE_URL = None

if DATABASE_URL is not None:
    conn = MongoClient(DATABASE_URL)
    db = conn.canonleech
    old_config = db.settings.deployConfig.find_one({"_id": bot_id})
    config_dict = db.settings.config.find_one({"_id": bot_id})
    if config_dict is not None:
        if config_dict.get("UPSTREAM_REPO"):
            environ["UPSTREAM_REPO"] = str(config_dict["UPSTREAM_REPO"])
        if config_dict.get("UPSTREAM_BRANCH"):
            environ["UPSTREAM_BRANCH"] = str(config_dict["UPSTREAM_BRANCH"])
        if config_dict.get("UPDATE_PACKAGES"):
            environ["UPGRADE_PACKAGES"] = str(config_dict.get("UPDATE_PACKAGES"))
    conn.close()


def get_file_hash(filepath):
    if not ospath.exists(filepath):
        return None
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        log_error(f"Failed to calculate hash for {filepath}: {e}")
        return None


def get_uv_path():
    uv_path = shutil_which("uv")
    if not uv_path:
        for path in [
            "/bin/uv",
            "/usr/local/bin/uv",
            "/usr/bin/uv",
            ospath.expanduser("~/.local/bin/uv"),
            ospath.expanduser("~/.cargo/bin/uv"),
        ]:
            if ospath.exists(path):
                uv_path = path
                break
    return uv_path or "uv"


def install_requirements(req_path="requirements.txt", current_hash=None):
    if not ospath.exists(req_path):
        return False
    uv_bin = get_uv_path()
    log_info(f"Installing/updating requirements from {req_path} using {uv_bin}...")
    cmd = f'"{uv_bin}" pip install --system --break-system-packages --no-cache -r "{req_path}"'
    log_info(f"Executing: {cmd}")
    res = srun(cmd, shell=True)
    if res.returncode == 0:
        log_info("Successfully installed requirements with uv pip!")
        saved_hash = current_hash or get_file_hash(req_path)
        if saved_hash:
            try:
                with open(".requirements_installed", "w") as f:
                    f.write(saved_hash)
            except Exception as e:
                log_error(f"Failed to update .requirements_installed: {e}")
        return True
    else:
        log_error(
            f"uv pip install failed with exit code {res.returncode}! Attempting fallback with python3 -m pip..."
        )
        fallback_res = srun(
            f'python3 -m pip install --break-system-packages --no-cache-dir -r "{req_path}"',
            shell=True,
        )
        if fallback_res.returncode == 0:
            log_info("Successfully installed requirements with pip fallback!")
            saved_hash = current_hash or get_file_hash(req_path)
            if saved_hash:
                try:
                    with open(".requirements_installed", "w") as f:
                        f.write(saved_hash)
                except Exception as e:
                    log_error(f"Failed to update .requirements_installed: {e}")
            return True
        else:
            log_error("Failed to install requirements with fallback pip!")
            return False


def check_and_update_requirements(req_hash_before=None):
    req_file = "requirements.txt"
    if not ospath.exists(req_file):
        return

    req_hash_after = get_file_hash(req_file)
    if not req_hash_after:
        return

    installed_hash = None
    if ospath.exists(".requirements_installed"):
        try:
            with open(".requirements_installed", "r") as f:
                installed_hash = f.read().strip()
        except Exception:
            pass

    req_changed = False
    if req_hash_before is not None and req_hash_before != req_hash_after:
        req_changed = True
        log_info("Detected changes in requirements.txt from upstream repository!")
    elif installed_hash is not None and installed_hash != req_hash_after:
        req_changed = True
        log_info("Current requirements.txt differs from installed version!")

    if req_changed:
        install_requirements(req_file, req_hash_after)
    elif not ospath.exists(".requirements_installed"):
        try:
            with open(".requirements_installed", "w") as f:
                f.write(req_hash_after)
        except Exception:
            pass


UPGRADE_PACKAGES = environ.get("UPGRADE_PACKAGES", "False")
if UPGRADE_PACKAGES.lower() == "true":
    packages = [dist.metadata["Name"] for dist in distributions()]
    uv_bin = get_uv_path()
    scall(f'"{uv_bin}" pip install --system --break-system-packages ' + " ".join(packages), shell=True)

UPSTREAM_REPO = environ.get("UPSTREAM_REPO", "")
if "WZMLakane" in UPSTREAM_REPO or len(UPSTREAM_REPO) == 0:
    UPSTREAM_REPO = "https://github.com/aquib4040/AZML"
    UPSTREAM_BRANCH = "main"
else:
    UPSTREAM_BRANCH = environ.get("UPSTREAM_BRANCH", "main")
    if len(UPSTREAM_BRANCH) == 0:
        UPSTREAM_BRANCH = "main"

req_hash_before = get_file_hash("requirements.txt")

if UPSTREAM_REPO is not None:
    if "github_pat_" in UPSTREAM_REPO and "@github.com" not in UPSTREAM_REPO:
        parts = UPSTREAM_REPO.split("github_pat_")
        if len(parts) == 2 and "/" in parts[1]:
            token_part, repo_part = parts[1].split("/", 1)
            UPSTREAM_REPO = f"{parts[0]}github_pat_{token_part}@github.com/{repo_part}"
    if ospath.exists(".git"):
        srun(["rm", "-rf", ".git"])

    update = srun(
        [
            f"git init -q \
                     && git config --global user.email mdaquibjawed1106@gmial.com \
                     && git config --global user.name aquib4040 \
                     && git add . \
                     && git commit -sm update -q \
                     && git remote add origin {UPSTREAM_REPO} \
                     && git fetch origin -q \
                     && git reset --hard origin/{UPSTREAM_BRANCH} -q"
        ],
        shell=True,
    )

    repo = UPSTREAM_REPO.split("/")
    UPSTREAM_REPO = f"https://github.com/{repo[-2]}/{repo[-1]}"
    if update.returncode == 0:
        log_info("Successfully updated with latest commits !!")
        # Log latest commit info
        try:
            commit_info = srun(
                ["git", "log", "--oneline", "-1"],
                capture_output=True,
                text=True,
            ).stdout.strip()
            log_info(f"Latest commit: {commit_info}")
        except Exception as e:
            log_error(f"Failed to get commit info: {e}")
        check_and_update_requirements(req_hash_before)
    else:
        log_error("Something went Wrong ! Retry or Ask Support !")
    log_info(f"UPSTREAM_REPO: {UPSTREAM_REPO} | UPSTREAM_BRANCH: {UPSTREAM_BRANCH}")
else:
    check_and_update_requirements(req_hash_before)

