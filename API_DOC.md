# Thunder API Documentation

**Base URL:** `https://animeshrinexyz-92535430c5ef.herokuapp.com/api/`

---

## API Endpoint

Thunder exposes an API to programmatically generate download links for files in any Telegram channel the bot has access to.

### `POST /api/generate_link`

Forwards a file from any channel to the storage channel and returns a fast direct download link.

### Request

```bash
curl -X POST https://your-fqdn/api/generate_link \
  -H "Content-Type: application/json" \
  -d '{"channel_id": -1001234567890, "message_id": 123}'
```

| Field        | Type  | Description                                    |
|--------------|-------|------------------------------------------------|
| `channel_id` | `int` | Telegram channel/chat ID containing the file   |
| `message_id` | `int` | Message ID of the file                         |

### Response

```json
{
  "success": true,
  "download_link": "https://your-fqdn/AbCdEf123/filename.mkv",
  "file_name": "filename.mkv",
  "file_size": "1.5 GB"
}
```

> **Note:** Links are direct — no tokens or database storage involved. The link works as long as the file exists in `BIN_CHANNEL`.
