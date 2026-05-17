# Telegram Force-Subscribe Bot

A professional Telegram bot built with **Python + Pyrogram** that:

- Enforces channel membership before allowing use
- Sends a welcome video once the user joins
- Auto-deletes the welcome video after 5 minutes
- Shows clean inline buttons

---

## Quick Setup

### 1. Configure secrets

Set these in the Replit **Secrets** tab (or in a local `.env` file):

| Key | Where to get it |
|-----|-----------------|
| `API_ID` | https://my.telegram.org/apps |
| `API_HASH` | https://my.telegram.org/apps |
| `BOT_TOKEN` | @BotFather on Telegram |
| `CHANNEL_USERNAME` | Your channel, e.g. `@mychannel` |
| `VIDEO_FILE` | Local path or Telegram `file_id` |

### 2. Make the bot a channel admin

The bot must be an **admin** (or at least a member with "Read messages" access) of your channel so it can verify memberships.

### 3. Upload your welcome video

Place your video file at the path set in `VIDEO_FILE` (default: `welcome.mp4` next to `bot.py`), **or** use a Telegram `file_id` string instead — no upload needed.

### 4. Customise captions & buttons

Open `bot.py` and edit:

```python
VIDEO_CAPTION = "..."          # HTML-formatted caption
WELCOME_BUTTONS = InlineKeyboardMarkup([...])
AUTO_DELETE_SECONDS = 5 * 60  # change the deletion delay
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Entry point — checks subscription and sends welcome video |

---

## How it works

```
User sends /start
    │
    ├─ Not subscribed?  → Show "Join Channel" + "I've Joined — Check" buttons
    │
    └─ Subscribed?      → Send welcome video with inline buttons
                              └─ Auto-delete video after 5 minutes (background task)
```

---

## Requirements

- Python 3.11+
- `pyrogram`
- `tgcrypto` (faster crypto, optional but recommended)
