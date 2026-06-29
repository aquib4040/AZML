<p align="center">
    <a href="https://github.com/utkarshdubey2008/AZML">
        <kbd>
            <img width="250" src="https://i.ibb.co/Mx2TJns0/file-00000000096c7207a8cef40bc07b65ef.png" alt="AZML Logo">
        </kbd>
    </a>
</p>

<p align="center">
    <i>A Telegram Bot written in Python using the Pyrogram framework for mirroring and leeching files
    from the internet to Google Drive, Telegram, or any RClone-supported cloud storage.
    Forked and extended from <a href="https://github.com/weebzone/WZML-X">WZML-X</a>.</i>
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
  <summary><b>⬇️ Download Engines</b></summary>

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

</details>

<details>
  <summary><b>☁️ Upload Targets</b></summary>

**Telegram (Leech)**
- Split files at configurable size thresholds (up to 4 GB with premium)
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
  <summary><b>🔄 Google Drive Operations</b></summary>

- Clone files/folders between drives server-side
- Count files and folders in a Drive path
- Search across multiple folders and TeamDrives
- Recursive search on root and TeamDrive IDs
- Fallback from Service Account to `token.pickle` on failure
- **GDrive Clean** — bulk delete or move to trash all files inside a Drive folder (owner-only, with confirmation prompt)

</details>

<details>
  <summary><b>🌀 Torrent</b></summary>

- Torrent search via API and qBittorrent search plugins
- Cached magnet support via Real-Debrid API
- Multi-tracker support
- Per-task rename via `-n` flag — works with magnet links and `.torrent` files, inline or by reply
- Auto rename applies to every file in a batch torrent independently

</details>

<details>
  <summary><b>📦 Archive Handling</b></summary>

- Extraction via 7-zip: RAR, ZIP, 7z, ISO, TAR, and split archives
- Password-protected archive extraction and creation
- ZIP compression with optional password
- Auto rename runs post-extraction on each file individually

</details>

<details>
  <summary><b>📰 RSS</b></summary>

- RSS feed monitoring with filters
- Per-user feeds with tag support
- Pause, resume, and edit feeds without restart
- Sudo controls over user feeds

</details>

<details>
  <summary><b>🗄️ Database & Storage</b></summary>

- MongoDB backend for persistent state
- Per-user settings, thumbnails, and rclone configs stored in DB
- RSS data and incomplete task recovery across restarts
- Private file storage

</details>

<details>
  <summary><b>🔍 Media Info & Scraper</b></summary>

**MediaInfo (`/mediainfo`, `/mi`)**
- Generate full MediaInfo report from a Telegram file or direct download link
- Supports video, audio, document, voice, animation, and video notes
- Output posted to Telegraph for easy sharing

**Universal Scraper (`/scrape`, `/sc`)**
- Extract metadata and download links from streaming platforms and social media
- Supports 30+ platforms including Zee5, YouTube, Crunchyroll, and more
- Auto-detects platform from URL
- Returns title, type, year, duration, quality, thumbnail, landscape/poster, and download links

</details>

<details>
  <summary><b>🎭 Anime, IMDB & Drama Lookup</b></summary>

**AniList (`/anime`)**
- Search anime and manga via AniList GraphQL API
- Returns title (romaji, English, native), format, status, score, episodes, genres, studios, and synopsis
- Inline pagination for multiple results
- Manga chapter/volume data included

**IMDB (`/imdb`)**
- Search movies and TV shows via IMDb (Cinemagoer)
- Returns title, year, rating, genres, cast, directors, plot summary, and poster
- Genre-to-emoji mapping for visual output
- Inline pagination for multiple results

**MyDramaList (`/mdl`)**
- Search Korean dramas and Asian content via MyDramaList API
- Returns title, year, rating, genres, cast, and synopsis
- Inline pagination

**Crunchyroll Poster (`/cr`)**
- Fetch landscape and portrait poster/backdrop links for any Crunchyroll series by URL
- No login required (uses public client token)

</details>

<details>
  <summary><b>🏎️ Speedtest</b></summary>

- Run a server speedtest directly from the bot (`/speedtest`, `/sp`)
- Reports upload speed, download speed, ping, data sent/received
- Includes ISP info, geolocation, and server details
- Result image shared automatically

</details>

<details>
  <summary><b>🔑 Session Generator</b></summary>

- Generate a Pyrogram string session via guided bot conversation in PM (`/genss`)
- Supports phone and bot account session generation
- Encrypted session output for security
- Works with 2FA (password) accounts

</details>

<details>
  <summary><b>📢 Broadcast</b></summary>

- Send a message to all bot users stored in DB (`/broadcast`, `/bc`)
- Supports forward mode (`-f`), quiet mode (`-q`), edit (`-e`), and delete (`-d`) by broadcast ID
- Flood-wait aware with skip logic for blocked/deactivated accounts

</details>

<details>
  <summary><b>🖼️ Image Management</b></summary>

- Add images to the bot's rotation pool (`/addimg`) via Telegram photo reply or direct link
- View all stored images (`/images`)
- Bot uses stored images as rotating backgrounds for status and start messages
- Auto image search via `IMG_SEARCH` config to auto-populate the pool from wallpaper sites

</details>

<details>
  <summary><b>📁 Category / Drive Selection</b></summary>

- Per-task Google Drive category selection before upload
- Users can choose from pre-configured categories (each with its own Drive ID and index URL)
- Configurable per-user default upload category via `/usetting`
- Supports custom Drive ID (`-id`) and index URL (`-index`) flags per task

</details>

<details>
  <summary><b>⚙️ User Settings (`/usetting`)</b></summary>

- **Leech Settings**: prefix, suffix, caption, regex rename, media/document toggle, split size, equal splits, media group
- **Auto Rename**: template-based rename with `{title}`, `{season}`, `{episode}`, `{chapter}`, `{quality}`, `{audio}` tags
- **Regex Rename**: legacy find-and-replace rename (runs before template)
- **Thumbnail**: set/clear a persistent custom thumbnail applied to all leeched files
- **RClone Config**: per-user `rclone.conf` upload and management
- **Google Drive**: per-user Drive ID, index URL, TeamDrive toggle
- **Intro Subtitles**: text overlay, duration, font size, position, styling — burned into video via FFmpeg
- **Personal Bot**: connect a personal Telegram bot token for isolated leeching
- **Personal Dump**: set a personal channel/group for dump uploads
- **yt-dlp Options**: per-user custom yt-dlp flags

</details>

<details>
  <summary><b>🌐 Overall</b></summary>

- Docker image support: `amd64`, `arm64/v8`, `arm/v7`
- Fully async (Pyrogram-based, uvloop-accelerated)
- Live variable editing and private file overwrite without restart
- Auto-update from `UPSTREAM_REPO` on restart
- Queue system for concurrent download/upload slots
- Per-user and global task limits (size, count, type)
- Bulk download from `.txt` file or newline-separated message
- Force subscribe to channels/groups before bot usage
- Token-based access control with configurable timeout and permanent passphrase login
- Shell executor (`/shell`), Python eval (`/eval`), and bot log access for sudo users
- Bot theming support (`minimal` and custom via `BotTheme`)
- Telegraph integration for Drive listings and MediaInfo
- Topic/thread-level authorization for supergroups
- Authorize, unauthorize, blacklist, and sudo management commands
- Safe mode — strip filenames/links from group chat, send only to PM
- Screenshots mode — generate video screenshots via `-ss` argument
- Save button and Source button toggles on file output

</details>

---

## Exclusive Features

---

### Auto Rename & Smart Metadata Extraction

Auto rename is a template-driven renaming system that extracts structured metadata directly from filenames before upload. It reads the title, season, episode, chapter, quality, and audio track from the raw filename and renames the file according to a pattern you define. It can be toggled on or off per user from the user settings panel (`/usetting`).

When auto rename is active, every file passing through the bot — whether from a direct link, torrent, Telegram file, or extracted archive — is renamed automatically before it hits the upload pipeline. No manual intervention needed.

<details>
  <summary><b>Template Tags</b></summary>

| Tag | What It Extracts |
|---|---|
| `{title}` | The show or file title, cleaned of noise like quality tags, group names, and codec strings |
| `{season}` | Season number (e.g. `01`, `02`) |
| `{episode}` | Episode number (e.g. `05`, `12`) |
| `{chapter}` | Chapter number, zero-padded to 3 digits (e.g. `001`, `045`, `140`) |
| `{quality}` | Video quality string (e.g. `1080p`, `720p`, `HDRip`) |
| `{audio}` | Audio language or type tag — used in captions to indicate dub, sub, or multi-audio |

Template examples:

```
{title} - S{season}E{episode} [{quality}]
{title} S{season}E{episode} {audio}
{title} - Chapter {chapter}.pdf
[{chapter}] {title}.pdf
Ch-{chapter} - {title}.pdf
```

</details>

<details>
  <summary><b>Title Extraction & Quality Auto-Detection</b></summary>

The extractor strips known noise from the filename — quality markers, resolution strings, codec identifiers, release group tags, site watermarks — and returns the clean content title. It handles anime, manga, manhwa, live-action, and generic files consistently.

```
[S01-E03] Takamine San [1080p][x264]        →  Takamine San
[CH-140] Infinite Mage - AnimeDynasty.pdf   →  Infinite Mage
Attack.on.Titan.S04E28.1080p.WEB.mkv        →  Attack on Titan
[SubsPlease] Frieren - 16 (1080p).mkv       →  Frieren
```

If `{quality}` is in the template but no quality string is detected, the extractor falls back to a file-size check. Any file over **500 MB** without a detected quality tag automatically receives `HDRip` as the quality value.

</details>

<details>
  <summary><b>Chapter Detection</b></summary>

Chapters are zero-padded to 3 digits. The extractor recognises a wide range of release naming conventions including Japanese numerals:

```
[CH-140] Blue Lock.pdf            →  140
[CH 58] One Piece.pdf             →  058
[059] Solo Leveling.pdf           →  059
Ch-123 My Hero Academia.pdf       →  123
[C576] Lookism @Manga_Cruise.pdf  →  576
#88 Naruto.pdf                    →  088
Ep-19 Demon Slayer.pdf            →  019
Vol2 Attack on Titan.pdf          →  002
Part 4 JoJo.pdf                   →  004
第233話 One Piece.pdf              →  233
Chap 90 Spy Family.pdf            →  090
Book 3 Mushoku Tensei.pdf         →  003
E120 Bleach.pdf                   →  120
S01E13 Classroom of the Elite     →  013
364 END Berserk.pdf               →  364
456 Final Tokyo Ghoul.pdf         →  456
c 789 Black Clover.pdf            →  789
Ch1234 One Punch Man.pdf          →  1234
C 25 Hunter x Hunter.pdf          →  025
Episode 12 Chainsaw Man.pdf       →  012
```

</details>

<details>
  <summary><b>Regex Rename (Legacy)</b></summary>

The older find-and-replace rename system based on regex patterns continues to work alongside the template system. Configure a regex pattern and a replacement string separately in `/usetting`. Both coexist — regex rename runs first on the raw filename, and then the template is applied to the result if auto rename is enabled.

</details>

<details>
  <summary><b>Batch Torrents & Archive Extraction</b></summary>

When a torrent contains multiple files, auto rename processes each file independently. Metadata is extracted per file, not per torrent — so a batch release with 12 episodes or 20 chapters will have every individual file renamed based on its own filename.

Auto rename also runs as a post-extraction step. When a ZIP, RAR, 7z, or split archive is extracted, every resulting file is passed through the full rename pipeline before upload.

</details>

---

### Per-Task Manual Filename Override (`-n`)

The `-n` flag lets you force a specific output filename for any single task, bypassing auto rename entirely. No metadata extraction, no template substitution, no regex processing — it is a hard per-task override.

<details>
  <summary><b>Usage Examples</b></summary>

Inline with a URL:
```
/command https://example.com/file.mkv -n Filename.mkv
```

By replying to a file:
```
/command -n Filename.mkv
```

With direct links:
```
/command https://files.example.com/release.zip -n ShowName.S01E04.1080p.mkv
/command https://cdn.example.org/manga-ch140.pdf -n [CH-140] Blue Lock.pdf
```

With torrents (single-file sets filename, multi-file sets root folder name):
```
/command magnet:?xt=urn:btih:HASH&dn=... -n ShowName.S02E05.mkv
/command -n ShowName.S02E05.mkv
```

With Telegram files (reply to any document, video, or audio):
```
/command -n CleanName.mp4
/command -n [CH-140] Blue Lock.pdf
```

</details>

---

### Custom Leech Thumbnail (`/t`)

Each user can set a persistent custom thumbnail applied to every file they leech. Stored per-user in the database — works across sessions without re-setting.

<details>
  <summary><b>Usage</b></summary>

Reply to any photo in Telegram with either command:
```
/t
/thumbnail
```

Both are identical. The photo you replied to is saved as your thumbnail. To clear or change it, go to `/usetting` → Thumbnail.

Once set, the thumbnail is applied to all leeched output — videos, documents, audio files, and every part of a split upload.

</details>

---

### Intro Subtitles

Intro subtitles let you burn a text overlay into the opening seconds of a video during the leech process, before the file is sent to Telegram. The overlay is rendered via FFmpeg and embedded directly into the video stream — not as a separate subtitle track.

<details>
  <summary><b>Details</b></summary>

- Appears for a configured duration at the start of the video, then disappears
- Useful for adding a channel name, group tag, or attribution watermark as a brief bumper
- Configuration — text content, display duration in seconds, font size, position, and styling — is managed through `/usetting`
- Does not re-encode the entire file; only the intro segment is processed

</details>

---

### GDrive Clean (`/gdclean`, `/gc`)

Owner-only command to bulk delete or trash all files inside a Google Drive folder.

<details>
  <summary><b>Details</b></summary>

- Accepts a Drive folder link inline or as a reply
- Defaults to the configured `GDRIVE_ID` if no link provided
- Shows folder name, size, file count, and folder count before acting
- Two options: **Move to Bin** (restorable) or **Permanent Clean** (irreversible)
- Folder itself is never deleted — only the files inside
- Confirmation buttons prevent accidental execution

</details>

---

### Personal Bot & Personal Dump

<details>
  <summary><b>Personal Bot</b></summary>

- Each user can connect their own Telegram bot token via `/usetting` → Personal Bot
- Leeched files are sent through the user's personal bot instead of the main bot
- Provides isolation — files appear from a different bot identity
- Verification step ensures the token and bot are valid before saving

</details>

<details>
  <summary><b>Personal Dump</b></summary>

- Each user can configure a personal channel or group as their dump destination via `/usetting` → Personal Dump
- All leeched files go to the dump channel/group automatically
- Supports channel IDs and usernames
- Verification checks that the bot (or user bot) has send permissions in the target

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

> All commands support a configurable `CMD_SUFFIX`. With suffix `x`, `/leech` becomes `/leechx`. The names listed below are defaults.

<details>
  <summary><b>Mirror & Leech</b></summary>

```
mirror        - Mirror a link or file to Drive/Cloud
m             - Alias for /mirror
qbmirror      - Mirror torrent via qBittorrent
qm            - Alias for /qbmirror
ytdl          - Mirror a yt-dlp supported link
y             - Alias for /ytdl
leech         - Leech a link or file to Telegram
l             - Alias for /leech
qbleech       - Leech torrent via qBittorrent
ql            - Alias for /qbleech
ytdlleech     - Leech a yt-dlp supported link
yl            - Alias for /ytdlleech
```

</details>

<details>
  <summary><b>Google Drive</b></summary>

```
clone         - Clone a Drive file/folder
c             - Alias for /clone
count         - Count items in a Drive path
del           - Delete a Drive file/folder
list          - Search Drive for files
gdclean       - Bulk delete/trash files in a Drive folder (owner only)
gc            - Alias for /gdclean
```

</details>

<details>
  <summary><b>Torrent & Search</b></summary>

```
search        - Search torrents via API
btsel         - Select files from a torrent
```

</details>

<details>
  <summary><b>Status & Tasks</b></summary>

```
status        - View active task status
s             - Alias for /status
statusall     - Global status (all bots)
cancel        - Cancel a specific task
cancelall     - Cancel all active tasks
cancellallbot - Cancel all tasks (multi-bot)
```

</details>

<details>
  <summary><b>User Tools</b></summary>

```
usetting      - User settings panel
us            - Alias for /usetting
t             - Set leech thumbnail (reply to a photo)
thumbnail     - Alias for /t
rss           - Open RSS feed menu
autorename    - Quick auto rename toggle/template set
ar            - Alias for /autorename
login         - Login with permanent passphrase
```

</details>

<details>
  <summary><b>Info & Media</b></summary>

```
imdb          - Search IMDB for movies/shows
anime         - Search AniList for anime/manga
mdl           - Search MyDramaList for dramas
mediainfo     - Generate MediaInfo for a file or link
mi            - Alias for /mediainfo
scrape        - Universal platform scraper
sc            - Alias for /scrape
cr            - Fetch Crunchyroll series posters
speedtest     - Run a server speedtest
sp            - Alias for /speedtest
```

</details>

<details>
  <summary><b>Admin & Sudo</b></summary>

```
bsetting      - Bot settings panel
bs            - Alias for /bsetting
authorize     - Authorize a user or chat
a             - Alias for /authorize
unauthorize   - Unauthorize a user or chat
ua            - Alias for /unauthorize
blacklist     - Blacklist a user
bl            - Alias for /blacklist
rmblacklist   - Remove user from blacklist
rbl           - Alias for /rmblacklist
addsudo       - Add a sudo user
rmsudo        - Remove a sudo user
users         - List all authorized users
broadcast     - Broadcast a message to all users
bc            - Alias for /broadcast
addimg        - Add an image to the bot's rotation pool
images        - View all stored images
log           - Fetch bot log
shell         - Execute a shell command
eval          - Evaluate Python code
exec          - Execute Python code (exec)
clearlocals   - Clear eval/exec local variables
restart       - Restart the bot
r             - Alias for /restart
restartall    - Restart all bots
stats         - Bot resource usage stats
st            - Alias for /stats
ping          - Check bot responsiveness
p             - Alias for /ping
help          - List all commands with descriptions
genss         - Generate a Pyrogram string session
```

</details>

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

- **Base Repository**: [WZML](https://github.com/weebzone/WZML) by [Weebzone](https://github.com/weebzone) — core architecture, feature design, and original implementation.
- **Original Creator**: [Utkarsh](https://github.com/utkarshdubey2008)
- **Lead Contributor & Maintainer**: [Aquib](https://github.com/aquib4040)

---

## Authors

| | |
|:---:|:---:|
| <img width="80" src="https://avatars.githubusercontent.com/u/97157730?v=4"> | <img width="80" src="https://avatars.githubusercontent.com/u/200465492?v=4"> |
| [`Utkarsh`](https://github.com/utkarshdubey2008) | [`Aquib`](https://github.com/aquib4040) |
| Original Creator [AZML] | Lead Contributor & Maintainer |

---

<p align="center">Licensed under MIT &nbsp;·&nbsp; PRs welcome</p>
