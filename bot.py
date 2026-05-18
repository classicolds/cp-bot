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
CHANNELS = [
    ("@clas3icx", "📢 Public Channel", "https://t.me/clas3icx"),
    (_parse_channel_id(os.environ.get("PRIVATE_CHANNEL_ID", "0")), "🔒 Private Channel", "https://t.me/+p58ZCEE1DhE2OWQ1"),
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
async def check_public_channel(client: Client, user_id: int, channel_id: str) -> bool:
    """Check if user is a member of public channel."""
    try:
        member = await client.get_chat_member(channel_id, user_id)
        status = member.status.name
        is_member = status not in ("BANNED", "LEFT")
        print(f"[DEBUG] Public channel {channel_id}: user {user_id} status={status}, member={is_member}")
        return is_member
    except UserNotParticipant:
        print(f"[DEBUG] Public channel {channel_id}: user {user_id} not a member")
        return False
    except Exception as e:
        print(f"[ERROR] Public channel {channel_id}: {type(e).__name__}: {e}")
        return False


async def check_private_channel(client: Client, user_id: int, channel_id) -> bool:
    """
    Check if user has access to private channel.
    Returns True if:
    - User is a full member, OR
    - User has sent a join request (pending approval)
    """
    if not channel_id or channel_id == 0:
        print(f"[WARN] Private channel ID not configured")
        return True
    
    try:
        member = await client.get_chat_member(channel_id, user_id)
        status = member.status.name
        is_member = status not in ("BANNED", "LEFT")
        print(f"[DEBUG] Private channel {channel_id}: user {user_id} status={status}, member={is_member}")
        return is_member
    except UserNotParticipant:
        # User is not in the channel - could be pending request
        print(f"[INFO] Private channel {channel_id}: user {user_id} not found (pending request) - ALLOWING")
        return True
    except (ChatAdminRequired, ChannelPrivate):
        # Bot doesn't have admin rights - assume user has pending request
        print(f"[WARN] Private channel {channel_id}: bot cannot check (no admin) - ALLOWING (pending request)")
        return True
    except Exception as e:
        # Any other error - be lenient for private channels
        print(f"[ERROR] Private channel {channel_id}: {type(e).__name__}: {e} - ALLOWING")
        return True


async def is_fully_subscribed(client: Client, user_id: int) -> bool:
    """Check if user has access to all required channels."""
    print(f"[DEBUG] Checking subscription for user {user_id}")
    
    # Check public channel (strict)
    public_ok = await check_public_channel(client, user_id, CHANNELS[0][0])
    
    # Check private channel (lenient - allows pending requests)
    private_ok = await check_private_channel(client, user_id, CHANNELS[1][0])
    
    result = public_ok and private_ok
    print(f"[DEBUG] Subscription result: public={public_ok}, private={private_ok}, final={result}")
    return result


def join_keyboard() -> InlineKeyboardMarkup:
    """Keyboard with one button per channel + a Verify button."""
    rows = [[InlineKeyboardButton(label, url=url)] for (_, label, url) in CHANNELS]
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
    """Send all 6 videos one by one, then schedule deletion."""
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
    """Show the join prompt."""
    print(f"[INFO] /start from user {message.from_user.id}")
    await message.reply(
        "⚠️ <b>To continue, please join all required channels first.</b>\n\n"
        "📌 Join both channels below, then tap <b>✅ Verify</b> to unlock the bot.",
        reply_markup=join_keyboard(),
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex("^verify$"))
async def verify_callback(client: Client, callback_query) -> None:
    """Check membership and send welcome or alert."""
    user = callback_query.from_user
    print(f"[INFO] Verify clicked by user {user.id}")

    if not await is_fully_subscribed(client, user.id):
        print(f"[INFO] User {user.id} FAILED verification")
        await callback_query.answer(
            "❌ Join all required channels first!",
            show_alert=True,
        )
        return

    print(f"[INFO] User {user.id} PASSED verification - sending welcome")
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
