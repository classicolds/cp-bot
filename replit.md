# Telegram Force-Subscribe Bot

A professional Telegram bot built with Python + Pyrogram. Enforces channel membership before granting access, sends a welcome video, and auto-deletes it after 5 minutes.

## Run & Operate

- Run via the **Telegram Bot** workflow (auto-starts)
- Bot logs appear in the workflow console

## Stack

- Python 3.11
- Pyrogram 2.x + TgCrypto

## Where things live

- `bot/bot.py` — main bot logic (all features in one file)
- `bot/README.md` — setup & customization guide
- `bot/.env.example` — template for required env vars

## Architecture decisions

- Single-file bot for simplicity and easy portability
- Force-subscribe check happens on every `/start` before any action
- Auto-delete runs as an `asyncio.create_task` so it never blocks the handler
- Graceful fallback if `VIDEO_FILE` is missing or bot lacks channel admin rights

## Product

- `/start` → checks if user joined the configured channel
- If not joined: shows "Join Channel" + "I've Joined — Check" buttons
- After joining: sends welcome video with inline buttons (auto-deleted after 5 min)

## User preferences

- Uses Pyrogram (not python-telegram-bot)
- All config via environment variables / Replit Secrets

## Gotchas

- Bot must be an **admin** in the channel to verify memberships
- `VIDEO_FILE` must be a local file path or a valid Telegram `file_id`
- `CHANNEL_USERNAME` must start with `@` for public channels, or be a numeric ID for private ones

## Required Secrets (set in Replit Secrets tab)

| Key | Description |
|-----|-------------|
| `API_ID` | From https://my.telegram.org/apps |
| `API_HASH` | From https://my.telegram.org/apps |
| `BOT_TOKEN` | From @BotFather |
| `CHANNEL_USERNAME` | e.g. `@yourchannel` |
| `VIDEO_FILE` | Local path or Telegram file_id |
