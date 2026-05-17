"""
Telegram Bot — Multi-Channel Force Subscribe
Uses: Python + Pyrogram
"""

import asyncio
import os
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, ChannelPrivate

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]


def _parse_channel_id(raw: str) -> int:
    """
    Normalize a Telegram channel ID.
    Telegram supergroup/channel IDs must be negative and start with -100.
    If the user supplied a bare numeric ID (e.g. 1003991216449), this
    converts it to the correct form (-1001003991216449).
    """
    val = int(raw)
    if val > 0:
        val = int(f"-100{val}")
    return val


# ── Channels the user must join ───────────────
# Each entry: (check_id, button_label, join_url, is_private)
#   check_id  → @username for public, -100XXXXX (int) for private
#   join_url  → URL shown on the button (never the numeric ID)
#   is_private → True if this is a private channel (allow pending requests)
CHANNELS = [
    (
        "@clas3icx",
        "📢 Public Channel",
        "https://t.me/clas3icx",
        False,
    ),
    (
        _parse_channel_id(os.environ.get("PRIVATE_CHANNEL_ID", "0")),
        "🔒 Private Channel",
        "https://t.me/+p58ZCEE1DhE2OWQ1",
        True,
    ),
]

# ── Welcome videos ────────────────────────────
VIDEOS_DIR = os.path.join(os.path.dirname(__file__), "videos")
VIDEO_FILES = [
    os.path.join(VIDEOS_DIR, "1_1779006845071.mp4"),
    os.path.join(VIDEOS_DIR, "2_1779006845072.mp4"),
    os.path.join(VIDEOS_DIR, "3_1779006845073.mp4"),
    os.path.join(VIDEOS_DIR, "4_1779006845073.mp4"),
    os.path.join(VIDEOS_DIR, "5_1779006845073.mp4"),
    os.path.join(VIDEOS_DIR, "6_1779006845073.mp4"),
]

WELCOME_CAPTION = (
    "🎉 <b>You're verified! Welcome aboard.</b>\n\n"
    "You've successfully joined all required channels and unlocked full access.\n\n"
    "Enjoy all the exclusive content below! 🚀"
)

AUTO_DELETE_SECONDS = 1 * 60  # 1 minute

# ─────────────────────────────────────────────
#  BOT CLIENT
# ─────────────────────────────────────────────
app = Client(
    "force_sub_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
async def check_channel(client: Client, user_id: int, check_id, is_private: bool = False) -> bool:
    """
    Return True if user_id is an active member of check_id.
    
    For private channels: also return True if user has a pending join request.
    For public channels: only return True if user is a full member.
    """
    if not check_id or check_id == 0:
        print(f"[WARN] Channel check_id not configured, skipping check.")
        return True
    try:
        member = await client.get_chat_member(check_id, user_id)
        status = member.status.name
        
        # For private channels, accept RESTRICTED status (pending join request)
        if is_private and status == "RESTRICTED":
            print(f"[INFO] User {user_id} has pending request for private channel {check_id}")
            return True
        
        # Standard check: user is a member and not banned/left
        return status not in ("BANNED", "LEFT")
    except UserNotParticipant:
        return False
    except (ChatAdminRequired, ChannelPrivate):
        print(f"[WARN] Bot cannot check membership for {check_id} — make it an admin.")
        return True
    except Exception as e:
        print(f"[ERROR] Membership check failed for {check_id}: {e}")
        return True


async def is_fully_subscribed(client: Client, user_id: int) -> bool:
    """
    Return True only if the user has joined ALL required channels.
    For private channels, also accept pending join requests.
    """
    results = await asyncio.gather(
        *[check_channel(client, user_id, ch[0], ch[3]) for ch in CHANNELS]
    )
    return all(results)


def join_keyboard() -> InlineKeyboardMarkup:
    """Keyboard with one button per channel + a Verify button."""
    rows = [[InlineKeyboardButton(label, url=url)] for (_, label, url, _) in CHANNELS]
    rows.append([InlineKeyboardButton("✅ Verify", callback_data="verify")])
    return InlineKeyboardMarkup(rows)


async def delete_messages_after(messages: list, delay: int) -> None:
    """Delete every message in *messages* after *delay* seconds."""
    await asyncio.sleep(delay)
    for msg in messages:
        try:
            await msg.delete()
        except Exception as e:
            print(f"[INFO] Could not delete message {msg.id}: {e}")


async def send_welcome(client: Client, chat_id: int) -> None:
    """
    Send all 6 videos one by one (sequential upload avoids MEDIA_EMPTY
    on local files), then schedule deletion of every message after 3 min.
    """
    sent_messages = []

    for i, path in enumerate(VIDEO_FILES):
        caption = WELCOME_CAPTION if i == 0 else ""
        try:
            msg = await client.send_video(
                chat_id=chat_id,
                video=path,
                caption=caption,
                parse_mode=enums.ParseMode.HTML,
            )
            sent_messages.append(msg)
        except Exception as e:
            print(f"[ERROR] Failed to send video {path}: {e}")

    if sent_messages:
        asyncio.create_task(delete_messages_after(sent_messages, AUTO_DELETE_SECONDS))
    else:
        # All videos failed — send a text fallback
        msg = await client.send_message(
            chat_id=chat_id,
            text=WELCOME_CAPTION,
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(delete_messages_after([msg], AUTO_DELETE_SECONDS))


# ─────────────────────────────────────────────
#  HANDLERS
# ─────────────────────────────────────────────
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message) -> None:
    """Always show the join prompt — verification is manual via Verify button."""
    await message.reply(
        "⚠️ <b>To continue, please join all required channels first.</b>\n\n"
        "📌 Join both channels below, then tap <b>✅ Verify</b> to unlock the bot.",
        reply_markup=join_keyboard(),
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^verify$"))
async def verify_callback(client: Client, callback_query) -> None:
    """Check membership and either alert or send the welcome videos."""
    user = callback_query.from_user

    if not await is_fully_subscribed(client, user.id):
        await callback_query.answer(
            "❌ Join all required channels first!",
            show_alert=True,
        )
        return

    await callback_query.answer("✅ Verified! Welcome aboard 🎉")
    try:
        await callback_query.message.delete()
    except Exception:
        pass

    await send_welcome(client, callback_query.message.chat.id)


@app.on_callback_query(filters.regex("^help$"))
async def help_callback(client: Client, callback_query) -> None:
    """Help popup."""
    await callback_query.answer(
        "Use /start to begin. Join all channels to unlock full access.",
        show_alert=True,
    )


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    from keep_alive import keep_alive

    keep_alive()
    print("Keep-alive server started.")
    print("Bot is starting…")
    app.run()
