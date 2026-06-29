<p align="center">
    <a href="https://github.com/utkarshdubey2008/AZML">
        <kbd>
            <img width="250" src="https://i.ibb.co/Mx2TJns0/file-00000000096c7207a8cef40bc07b65ef.png" alt="AZML-X Logo">
        </kbd>
    </a>
</p>

<p align="center">
    <i>A Telegram Bot written in Python using the Pyrogram framework for mirroring and leeching files
    from the internet to Google Drive, Telegram, or any RClone-supported cloud storage.
    Forked and extended from <a href="https://github.com/weebzone/WZML-X">mirror-leech-telegram-bot</a>.</i>
</p>

<div align="center">

[![](https://img.shields.io/github/repo-size/utkarshdubey2008/AZML?color=green&label=Repo%20Size&labelColor=292c3b)](#)
[![](https://img.shields.io/github/commit-activity/m/utkarshdubey2008/AZML?logo=github&labelColor=292c3b&label=Github%20Commits)](#)
[![](https://img.shields.io/github/license/utkarshdubey2008/AZML?style=flat&label=License&labelColor=292c3b)](#)
[![](https://img.shields.io/github/issues-raw/utkarshdubey2008/AZML?style=flat&label=Open%20Issues&labelColor=292c3b)](#)
[![](https://img.shields.io/github/issues-closed-raw/utkarshdubey2008/AZML?style=flat&label=Closed%20Issues&labelColor=292c3b)](#)
[![](https://img.shields.io/github/stars/utkarshdubey2008/AZML?style=flat&logo=github&label=Stars&labelColor=292c3b&color=yellow)](#)
[![](https://img.shields.io/badge/Telegram%20Channel-Join-9cf?logo=telegram&labelColor=292c3b)](https://t.me/Thealphabotz)
[![](https://img.shields.io/badge/Support%20Group-Join-9cf?logo=telegram&labelColor=292c3b)](https://t.me/AlphaBotzChat)

</div>

---

## Features

<details>
  <summary><b>Download Engines</b></summary>

**qBittorrent**
- File selection before and during download
- Seeding to a specific ratio and time limit
- Live global option editing via bot settings

**Aria2c**
- File selection before and during download
- Seeding to a specific ratio and time limit
- Netrc support and per-link authentication
- Live global option editing via bot settings

**yt-dlp**
- Quality selection via inline buttons
- Per-task and per-user custom yt-dlp options
- Embedded thumbnails for leeched files
- All supported audio format outputs

**Thunder API (Beta)**
- Fast direct link generation for Telegram files
- *Note: Thunder API is in beta and currently being tested for personal use. It will soon be available for everyone.*

</details>

<details>
  <summary><b>Upload Targets</b></summary>

**Telegram (Leech)**
- Split files at configurable size thresholds (up to 4GB with premium)
- Per-user thumbnail, prefix, suffix, rename regex, and document/media toggle
- Media group support for split file parts
- Upload to a designated supergroup or channel

**Google Drive**
- Upload with Service Accounts and random SA rotation
- TeamDrive support
- Duplicate detection by name before upload
- Index link integration

**RClone**
- Upload to any RClone-supported remote
- Per-user `rclone.conf` support
- Per-task and global RClone flags
- Server-side clone between remotes
- RClone serve for remote index exposure

**DDL (Direct Download Links)**
- Upload to Gofile.io and Streamtape.com
- Multi-site simultaneous upload
- User-supplied API keys

</details>

<details>
  <summary><b>Google Drive Operations</b></summary>

- Clone files/folders between drives server-side
- Count files and folders in a Drive path
- Search across multiple folders and TeamDrives
- Recursive search on root and TeamDrive IDs
- Fallback from Service Account to `token.pickle` on failure

</details>

<details>
  <summary><b>Torrent</b></summary>

- Torrent search via API and qBittorrent search plugins
- Cached magnet support via real-debrid API
- Multi-tracker support
- Per-task rename via `-n` flag — works with magnet links and `.torrent` files, inline or by reply
- Auto rename applies to every file in a batch torrent independently

</details>

<details>
  <summary><b>Archive Handling</b></summary>

- Extraction via 7-zip: RAR, ZIP, 7z, ISO, TAR, and split archives
- Password-protected archive extraction and creation
- ZIP compression with optional password
- Auto rename runs post-extraction on each file individually

</details>

<details>
  <summary><b>RSS</b></summary>

- RSS feed monitoring with filters
- Per-user feeds with tag support
- Pause, resume, and edit feeds without restart
- Sudo controls over user feeds

</details>

<details>
  <summary><b>Database & Storage</b></summary>

- MongoDB backend for persistent state
- Per-user settings, thumbnails, and rclone configs stored in DB
- RSS data and incomplete task recovery across restarts
- Private file storage

</details>

<details>
  <summary><b>Overall</b></summary>

- Docker image support: `amd64`, `arm64/v8`, `arm/v7`
- Fully async (Pyrogram-based)
- Live variable editing and private file overwrite without restart
- Auto-update from `UPSTREAM_REPO` on restart
- Queue system for concurrent download/upload slots
- Per-user and global task limits (size, count, type)
- Bulk download from `.txt` file or newline-separated message
- Force subscribe to channels/groups before bot usage
- Token-based access control with configurable timeout
- Shell executor and bot log access for sudo users
- Bot theming support (`minimal` and custom)
- Telegraph integration for Drive listings

</details>

---

## Deployment

<details>
  <summary><b>Docker (Recommended)</b></summary>

**Using docker-compose**

```bash
sudo apt install docker-compose
sudo docker-compose up
```

To rebuild after config changes:

```bash
sudo docker-compose up --build
```

Stop, start, and manage:

```bash
sudo docker-compose stop
sudo docker-compose start
```

**Using Docker CLI**

```bash
sudo docker build . -t wzmlx
sudo docker run -p 80:80 -p 8080:8080 wzmlx
```

To stop:

```bash
sudo docker ps
sudo docker stop <container_id>
```

Cleanup:

```bash
sudo docker container prune
sudo docker image prune -a
```

**Notes**
- `BASE_URL_PORT` defaults to `80`, `RCLONE_SERVE_PORT` defaults to `8080`. Set these in `config.env` if using non-default ports.
- Stop the container before deleting it; delete the container before deleting the image.
- Check `nproc` and multiply by 4 for a recommended `AsyncIOThreadsCount` in `qbittorrent.conf`.

</details>

---

## Bot Commands

> All commands support a configurable `CMD_SUFFIX`. With suffix `x`, `/leech` becomes `/leechx`. The names listed below are defaults — use whatever trigger your instance exposes.

```
mirror        - Mirror a link or file to Drive/Cloud
qbmirror      - Mirror torrent via qBittorrent
leech         - Leech a link or file to Telegram
qbleech       - Leech torrent via qBittorrent
ytdl          - Mirror a yt-dlp supported link
ytdlleech     - Leech a yt-dlp supported link
clone         - Clone a Drive file/folder
count         - Count items in a Drive path
del           - Delete a Drive file/folder
list          - Search Drive for files
search        - Search torrents via API
status        - View active task status
btsel         - Select files from a torrent
rss           - Open RSS feed menu
usetting      - User settings panel
bsetting      - Bot settings panel
cancel        - Cancel a specific task
cancelall     - Cancel all active tasks
ar            - Set/view AutoRename template directly
t             - Set leech thumbnail (reply to a photo)
log           - Fetch bot log
shell         - Execute a shell command
restart       - Restart the bot
stats         - Bot resource usage stats
ping          - Check bot responsiveness
help          - List all commands with descriptions
```

---

## Exclusive Features

---

### Auto Rename & Smart Metadata Extraction (`/ar`)

Auto rename is a template-driven renaming system that extracts structured metadata directly from filenames before upload. It reads the title, season, episode, chapter, quality, and audio track from the raw filename and renames the file according to a template pattern you define.

You can toggle it on or off or configure it from the user settings panel (`/usetting`), or interact with it directly using the `/ar` or `/autorename` command.

#### Command Usage

- `/{ar|autorename} [template]` — Saves the template string for auto-renaming.
- `/{ar|autorename}` — Shows your current saved template and a list of available tags.
- `/{ar|autorename} off` (or `clear`/`reset`/`del`/`none`) — Clears and disables the AutoRename template.

#### Template Tags

| Tag | What It Extracts |
|---|---|
| `{title}` | The show or file title, cleaned of noise like quality tags, group names, and codec strings |
| `{season}` | Season number (e.g. `01`, `02`) |
| `{episode}` | Episode number (e.g. `05`, `12`) |
| `{episode:+N}` | Episode with a custom offset `N` |
| `{quality}` | Video quality string (e.g. `1080p`, `720p`, `HDRip`) |
| `{codec}` | Video codec (e.g. `x265`, `x264`, `h264`) |
| `{audio}` | Audio language or type tag |
| `{chapter}` | Chapter number, zero-padded to 3 digits (e.g. `001`, `045`, `140`) |

#### Template Examples

```
{title} - S{season}E{episode} [{quality}]
{title} S{season}E{episode} {audio}
{title} - Chapter {chapter}.pdf
[{chapter}] {title}.pdf
```

#### How Title Extraction Works

The extractor strips known noise from the filename — quality markers, resolution strings, codec identifiers, release group tags, site watermarks — and returns the clean content title. It handles anime, manga, manhwa, live-action, and generic files consistently.

```
[S01-E03] Takamine San [1080p][x264]        →  Takamine San
[CH-140] Infinite Mage - AnimeDynasty.pdf   →  Infinite Mage
Attack.on.Titan.S04E28.1080p.WEB.mkv        →  Attack on Titan
[SubsPlease] Frieren - 16 (1080p).mkv       →  Frieren
```

#### Quality Auto-Detection

If `{quality}` is in the template but no quality string is detected in the filename, the extractor falls back to a file size check. Any file over **500 MB** without a detected quality tag automatically receives `HDRip` as the quality value. This prevents blank or malformed filenames for unlabelled rips.

#### Chapter Detection

Chapters are zero-padded to 3 digits. The extractor recognises a wide range of release naming conventions used across manga, manhwa, light novels, and anime — including Japanese numerals.

---

### Custom Leech Thumbnail (`/t`)

Each user can set a persistent custom thumbnail that gets applied to every file they leech. The thumbnail is stored per-user in the database and used automatically from that point forward.

#### Command Usage

- `/t` or `/thumb` (reply to a photo) — Saves the photo as your persistent custom thumbnail.
- To view or clear your thumbnail, navigate to `/usetting` → Leech → Custom Thumbnail.

Once set, the thumbnail is applied to all leeched output — videos, documents, audio files, and every part of a split upload all carry it. It works on top of per-user settings, so different users in the same bot can each have their own thumbnail independently.

---

### Per-Task Manual Filename Override (`-n`)

The `-n` flag lets you force a specific output filename for any single task, bypassing auto rename entirely. When `-n` is used, the file is uploaded with exactly the name you provide — no metadata extraction, no template substitution, no regex processing. It is a hard per-task override.

This is the correct approach when you already know the exact output filename and do not want the rename system involved at all.

#### Basic Syntax

Inline with a URL — send the command with the link and the flag in the same message:

```
/command https://example.com/file.mkv -n Filename.mkv
```

By replying to a file, Telegram message, or torrent — send the command as a reply with just the flag:

```
/command -n Filename.mkv
```

Since command names depend on your `CMD_SUFFIX` configuration, `/command` is used here as a placeholder. `/leech` and `/l` refer to the same command — use whichever your deployment exposes.

#### With Direct Download Links

```
/command https://files.example.com/release.zip -n ShowName.S01E04.1080p.mkv
/command https://cdn.example.org/manga-ch140.pdf -n [CH-140] Blue Lock.pdf
/command https://example.com/archive.zip -n dataset.zip
```

#### With Torrents

Works identically with magnet links or `.torrent` files, whether sent inline or by replying to a torrent file already in chat:

```
/command magnet:?xt=urn:btih:HASH&dn=... -n ShowName.S02E05.mkv
/command -n ShowName.S02E05.mkv
```

The second example above is sent as a reply to a `.torrent` file. For single-file torrents, `-n` sets the output filename directly. For multi-file batch torrents, `-n` sets the name of the torrent's root folder rather than the individual files inside it — individual file naming within a batch is handled by the auto rename template.

#### With Telegram Files

Reply to any file already in Telegram — document, video, audio — and rename it before upload:

```
/command -n CleanName.mp4
/command -n [CH-140] Blue Lock.pdf
```

The renamed file is uploaded to Telegram (or Drive/cloud depending on your configured upload target) with exactly that name.

---

### Intro Subtitles

Intro subtitles let you burn a text overlay into the opening seconds of a video during the leech process, before the file is sent to Telegram. The overlay is rendered via FFmpeg at upload time and is embedded directly into the video stream — not as a separate subtitle track.

The subtitle appears for a configured duration at the start of the video and then disappears. The rest of the video beyond that window is completely untouched. This is useful for adding a channel name, group tag, or attribution watermark as a brief bumper without re-encoding the entire file or modifying the source.

Configuration — the text content, display duration in seconds, font size, position, and styling — is managed through the user settings panel (`/usetting`).

---

## Variables

<details>
  <summary><b>Required</b></summary>

| Variable | Type | Description |
|---|---|---|
| `BOT_TOKEN` | `str` | Telegram bot token from @BotFather |
| `OWNER_ID` | `int` | Telegram user ID of the bot owner |
| `TELEGRAM_API` | `int` | API ID from my.telegram.org |
| `TELEGRAM_HASH` | `str` | API hash from my.telegram.org |

</details>

<details>
  <summary><b>Optional / General</b></summary>

| Variable | Type | Description |
|---|---|---|
| `USER_SESSION_STRING` | `str` | Pyrogram string session for premium account operations |
| `DATABASE_URL` | `str` | MongoDB connection string |
| `DOWNLOAD_DIR` | `str` | Local download path |
| `CMD_SUFFIX` | `str/int` | Suffix appended to all bot commands |
| `AUTHORIZED_CHATS` | `int` | Space-separated user/chat IDs to authorize |
| `SUDO_USERS` | `int` | Space-separated user IDs with sudo access |
| `BLACKLIST_USERS` | `int` | Space-separated user IDs to block |
| `STATUS_LIMIT` | `int` | Max tasks shown per status page (recommended: 4) |
| `STATUS_UPDATE_INTERVAL` | `int` | Status message refresh interval in seconds |
| `AUTO_DELETE_MESSAGE_DURATION` | `int` | Seconds before bot messages are auto-deleted (-1 to disable) |
| `INCOMPLETE_TASK_NOTIFIER` | `bool` | Notify on incomplete tasks after restart (requires DB) |
| `SET_COMMANDS` | `bool` | Auto-set bot commands via Telegram API |
| `EXTENSION_FILTER` | `str` | Space-separated file extensions to skip on upload/clone |
| `YT_DLP_OPTIONS` | `str` | Default yt-dlp options as `key:value\|key:value` pairs |
| `FSUB_IDS` | `int` | Space-separated chat IDs for force-subscribe enforcement |
| `BOT_PM` | `bool` | Send files/links to bot PM instead of group |
| `DEFAULT_UPLOAD` | `str` | Upload target: `gd`, `rc`, or `ddl` |
| `TIMEZONE` | `str` | Bot timezone (default: `Asia/Kolkata`) |

</details>

<details>
  <summary><b>Google Drive</b></summary>

| Variable | Type | Description |
|---|---|---|
| `GDRIVE_ID` | `str` | Target folder/TeamDrive ID or `root` |
| `INDEX_URL` | `str` | Google Drive index URL |
| `USE_SERVICE_ACCOUNTS` | `bool` | Enable Service Account rotation |
| `IS_TEAM_DRIVE` | `bool` | Set `True` when uploading to a TeamDrive |
| `STOP_DUPLICATE` | `bool` | Block duplicate uploads by name |
| `DISABLE_DRIVE_LINK` | `bool` | Hide the Drive link button from output |
| `USER_TD_MODE` | `bool` | Allow users to upload to their own Drive |
| `USER_TD_SA` | `str` | SA email/group to share with users for TD access |
| `GD_INFO` | `str` | Description written to uploaded Drive items |

</details>

<details>
  <summary><b>RClone</b></summary>

| Variable | Type | Description |
|---|---|---|
| `RCLONE_PATH` | `str` | Default RClone upload path |
| `RCLONE_FLAGS` | `str` | Global RClone flags as `key:value\|key` pairs |
| `RCLONE_SERVE_URL` | `str` | Public URL for RClone serve (`http://ip` or `http://ip:port`) |
| `RCLONE_SERVE_PORT` | `int` | RClone serve port (default: `8080`) |
| `RCLONE_SERVE_USER` | `str` | RClone serve basic auth username |
| `RCLONE_SERVE_PASS` | `str` | RClone serve basic auth password |

</details>

<details>
  <summary><b>Telegram Leech</b></summary>

| Variable | Type | Description |
|---|---|---|
| `LEECH_SPLIT_SIZE` | `int` | Split size in bytes (default: 2GB, 4GB for premium) |
| `AS_DOCUMENT` | `bool` | Upload as document instead of media |
| `EQUAL_SPLITS` | `bool` | Split into equal-sized parts |
| `MEDIA_GROUP` | `bool` | Send split parts as a media group |
| `LEECH_FILENAME_PREFIX` | `str` | Prefix for leeched filenames |
| `LEECH_FILENAME_SUFFIX` | `str` | Suffix for leeched filenames |
| `LEECH_FILENAME_CAPTION` | `str` | Custom caption for leeched files |
| `LEECH_FILENAME_REMNAME` | `str` | Regex pattern to remove from leeched filenames |
| `LEECH_LOG_ID` | `int` | Channel/group ID for leech logs |
| `MIRROR_LOG_ID` | `int` | Channel/group ID for mirror logs |
| `LINKS_LOG_ID` | `int` | Channel/group ID for link logs |

</details>

<details>
  <summary><b>Auto Rename</b></summary>

| Variable | Type | Description |
|---|---|---|
| `AUTO_RENAME` | `bool` | Enable or disable auto rename globally |
| `RENAME_TEMPLATE` | `str` | Default rename template using tags: `{title}`, `{episode}`, `{quality}`, `{season}`, `{chapter}`, `{audio}` |

</details>

<details>
  <summary><b>qBittorrent / Aria2c</b></summary>

| Variable | Type | Description |
|---|---|---|
| `TORRENT_TIMEOUT` | `int` | Dead torrent timeout in seconds |
| `BASE_URL` | `str` | Public URL for torrent file selection web UI |
| `BASE_URL_PORT` | `int` | Port for `BASE_URL` (default: `80`) |
| `WEB_PINCODE` | `bool` | Require pincode for torrent file selection |

</details>

<details>
  <summary><b>Queue System</b></summary>

| Variable | Type | Description |
|---|---|---|
| `QUEUE_ALL` | `int` | Max concurrent download + upload tasks combined |
| `QUEUE_DOWNLOAD` | `int` | Max concurrent download tasks |
| `QUEUE_UPLOAD` | `int` | Max concurrent upload tasks |

> `QUEUE_ALL` must be >= the larger of `QUEUE_DOWNLOAD`/`QUEUE_UPLOAD` and <= their sum.

</details>

<details>
  <summary><b>Limits</b></summary>

| Variable | Type | Description |
|---|---|---|
| `DAILY_TASK_LIMIT` | `int` | Max tasks per user per day |
| `DAILY_MIRROR_LIMIT` | `int` | Max mirror size per user per day (GB) |
| `DAILY_LEECH_LIMIT` | `int` | Max leech size per user per day (GB) |
| `USER_MAX_TASKS` | `int` | Max simultaneous tasks per user |
| `BOT_MAX_TASKS` | `int` | Max simultaneous tasks across all users |
| `TORRENT_LIMIT` | `int` | Max torrent download size (GB) |
| `DIRECT_LIMIT` | `int` | Max direct link download size (GB) |
| `GDRIVE_LIMIT` | `int` | Max GDrive file/folder size for leech/zip (GB) |
| `CLONE_LIMIT` | `int` | Max GDrive clone size (GB) |
| `YTDLP_LIMIT` | `int` | Max yt-dlp download size (GB) |
| `PLAYLIST_LIMIT` | `int` | Max playlist item count |
| `LEECH_LIMIT` | `int` | Max leech size across sources (GB) |
| `MEGA_LIMIT` | `int` | Max Mega download size (GB) |
| `STORAGE_THRESHOLD` | `int` | Minimum free storage to maintain (GB) |
| `USER_TIME_INTERVAL` | `int` | Minimum gap between consecutive user tasks (sec) |

</details>

<details>
  <summary><b>RSS</b></summary>

| Variable | Type | Description |
|---|---|---|
| `RSS_DELAY` | `int` | Feed refresh interval in seconds (min recommended: 900) |
| `RSS_CHAT_ID` | `int` | Chat/channel ID to forward RSS links |

> `USER_SESSION_STRING` or a linked channel is required for RSS monitoring. A database is required to persist feeds across restarts.

</details>

<details>
  <summary><b>Mega</b></summary>

| Variable | Type | Description |
|---|---|---|
| `MEGA_EMAIL` | `str` | Mega.nz account email |
| `MEGA_PASSWORD` | `str` | Mega.nz account password |

</details>

<details>
  <summary><b>APIs & Cookies</b></summary>

| Variable | Type | Description |
|---|---|---|
| `REAL_DEBRID_API` | `str` | real-debrid.com API key |
| `DEBRID_LINK_API` | `str` | debrid-link.com API key |
| `FILELION_API` | `str` | Filelions API key |
| `GDTOT_CRYPT` | `str` | GDTot cookie for link bypass |
| `JIODRIVE_TOKEN` | `str` | JioDrive bypass token |
| `THUNDER_API` | `str` | Base URL of Thunder API (Beta, currently testing for self, soon available for all) |

</details>

<details>
  <summary><b>Torrent Search</b></summary>

| Variable | Type | Description |
|---|---|---|
| `SEARCH_API_LINK` | `str` | Torrent search API endpoint |
| `SEARCH_LIMIT` | `int` | Max results per site from search API |
| `SEARCH_PLUGINS` | `list` | Raw GitHub URLs for qBittorrent search plugins |

Supported sites via API: 1337x, Piratebay, Nyaasi, Torlock, Torrent Galaxy, Zooqle, Kickass, Bitsearch, MagnetDL, Libgen, YTS, Limetorrent, TorrentFunk, Glodls, TorrentProject, YourBittorrent

</details>

<details>
  <summary><b>Token System</b></summary>

| Variable | Type | Description |
|---|---|---|
| `TOKEN_TIMEOUT` | `int` | Token validity duration per user in seconds (default: 21600) |
| `LOGIN_PASS` | `str` | Permanent passphrase to bypass token verification |

</details>

<details>
  <summary><b>Telegraph</b></summary>

| Variable | Type | Description |
|---|---|---|
| `TITLE_NAME` | `str` | Title for Telegraph pages (used in /list) |
| `AUTHOR_NAME` | `str` | Author name on Telegraph pages |
| `AUTHOR_URL` | `str` | Author URL on Telegraph pages |
| `COVER_IMAGE` | `str` | graph.org image URL for Telegraph page header |

</details>

<details>
  <summary><b>Extra</b></summary>

| Variable | Type | Description |
|---|---|---|
| `SAFE_MODE` | `bool` | Strip filenames and links from group; send to PM only (requires `BOT_PM=True`) |
| `DELETE_LINKS` | `bool` | Delete command messages after processing |
| `CLEAN_LOG_MSG` | `bool` | Remove "leech started" messages from leech log |
| `SHOW_EXTRA_CMDS` | `bool` | Expose legacy commands (e.g. `zipleech`) |
| `IMAGES` | `str` | Space-separated graph.org image links for rotation |
| `IMG_SEARCH` | `str` | Comma-separated keywords for background image search |
| `IMG_PAGE` | `int` | Image result page offset (~70 images/page, default: 1) |
| `BOT_THEME` | `str` | Bot UI theme (`minimal` or custom) |
| `EXCEP_CHATS` | `int` | Space-separated group IDs exempt from log forwarding |
| `SHOW_MEDIAINFO` | `bool` | Show MediaInfo button on file output |
| `SCREENSHOTS_MODE` | `bool` | Enable screenshot generation via `-ss` argument |
| `SAVE_MSG` | `bool` | Add a Save button to each file/link output |
| `SOURCE_LINK` | `bool` | Add a Source button to file/link output |
| `UPSTREAM_REPO` | `str` | GitHub repo URL for auto-update on restart |
| `UPSTREAM_BRANCH` | `str` | Branch to pull from `UPSTREAM_REPO` (default: `master`) |

</details>

---

## Credits

- **Base Repository**: [WZML](https://github.com/weebzone/WZML) by [wzml](https://github.com/weebzone) — core architecture, feature design, and original implementation.
- **Foundation**: [mirror-leech-telegram-bot](https://github.com/anasty17/mirror-leech-telegram-bot) by anasty17
- **Origin**: [python-aria-mirror-bot](https://github.com/lzzy12/python-aria-mirror-bot) by lzzy12
- **Drive Search**: [searchX-bot](https://github.com/SVR666) by Sreeraj
- **Telegraph**: [loaderX-bot](https://github.com/SVR666) by Sreeraj
- **RSS**: [rss-chan](https://github.com/hyPnOtICDo0g/rss-chan) by hyPnOtICDo0g

---

## Authors

| | | |
|:---:|:---:|:---:|
| <img width="80" src="https://avatars.githubusercontent.com/u/105407900"> | <img width="80" src="https://avatars.githubusercontent.com/u/113664541"> | <img width="80" src="https://avatars.githubusercontent.com/u/84721324"> |
| [`SilentDemonSD`](https://github.com/SilentDemonSD) | [`CodeWithWeeb`](https://github.com/weebzone) | [`Maverick`](https://github.com/MajnuRangeela) |
| Author — DDL, UI Design, Custom Modules | Author — Feature Integration | Co-Author & QA |

---

<p align="center">Licensed under MIT &nbsp;·&nbsp; PRs welcome</p>
