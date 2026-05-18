"""
Telegram Bot — Multi-Channel Force Subscribe
Uses: Python + Pyrogram
"""

import asyncio
import os
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, ChannelPrivate

# CONFIG
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

# Store user IDs
USERS_FILE = "users.txt"
users_set = set()

def load_users():
    global users_set
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                users_set = set(int(line.strip()) for line in f if line.strip())
            print(f"[INFO] Loaded {len(users_set)} users")
        except Exception as e:
            print(f"[ERROR] Failed to load users: {e}")

def save_user(user_id: int):
    if user_id not in users_set:
        users_set.add(user_id)
        try:
            with open(USERS_FILE, "a") as f:
                f.write(f"{user_id}\n")
        except Exception as e:
            print(f"[ERROR] Failed to save user: {e}")

def _parse_channel_id(raw: str) -> int:
    val = int(raw)
    if val > 0:
        val = int(f"-100{val}")
    return val

CHANNELS = [
    ("@clas3icx", "📢 Public Channel", "https://t.me/clas3icx"),
    (_parse_channel_id(os.environ.get("PRIVATE_CHANNEL_ID", "0")), "🔒 Private Channel", "https://t.me/+p58ZCEE1DhE2OWQ1"),
]

VIDEOS_DIR = os.path.join(os.path.dirname(__file__), "videos")
VIDEO_FILES = [
    os.path.join(VIDEOS_DIR, "1_1779006845071.mp4"),
    os.path.join(VIDEOS_DIR, "2_1779006845072.mp4"),
    os.path.join(VIDEOS_DIR, "3_1779006845073.mp4"),
    os.path.join(VIDEOS_DIR, "4_1779006845073.mp4"),
    os.path.join(VIDEOS_DIR, "5_1779006845073.mp4"),
    os.path.join(VIDEOS_DIR, "6_1779006845073.mp4"),
]

WELCOME_CAPTION = "🎉 <b>You're verified! Welcome aboard.</b>\n\nYou've successfully joined all required channels and unlocked full access.\n\nEnjoy all the exclusive content below! 🚀"
AUTO_DELETE_SECONDS = 1 * 60

app = Client("force_sub_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def check_public_channel(client: Client, user_id: int, channel_id: str) -> bool:
    try:
        member = await client.get_chat_member(channel_id, user_id)
        status = member.status.name
        return status not in ("BANNED", "LEFT")
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"[ERROR] Public channel check: {e}")
        return False

async def check_private_channel(client: Client, user_id: int, channel_id) -> bool:
    if not channel_id or channel_id == 0:
        return True
    try:
        member = await client.get_chat_member(channel_id, user_id)
        status = member.status.name
        return status not in ("BANNED", "LEFT")
    except UserNotParticipant:
        print(f"[INFO] Private channel: user not found (pending request) - ALLOWING")
        return True
    except (ChatAdminRequired, ChannelPrivate):
        print(f"[WARN] Private channel: bot cannot check (no admin) - ALLOWING")
        return True
    except Exception as e:
        print(f"[ERROR] Private channel check: {e} - ALLOWING")
        return True

async def is_fully_subscribed(client: Client, user_id: int) -> bool:
    public_ok = await check_public_channel(client, user_id, CHANNELS[0][0])
    private_ok = await check_private_channel(client, user_id, CHANNELS[1][0])
    return public_ok and private_ok

def join_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(label, url=url)] for (_, label, url) in CHANNELS]
    rows.append([InlineKeyboardButton("✅ Verify", callback_data="verify")])
    return InlineKeyboardMarkup(rows)

async def delete_messages_after(messages: list, delay: int) -> None:
    await asyncio.sleep(delay)
    for msg in messages:
        try:
            await msg.delete()
        except Exception:
            pass

async def send_welcome(client: Client, chat_id: int) -> None:
    sent_messages = []
    for i, path in enumerate(VIDEO_FILES):
        caption = WELCOME_CAPTION if i == 0 else ""
        try:
            msg = await client.send_video(chat_id=chat_id, video=path, caption=caption, parse_mode=enums.ParseMode.HTML)
            sent_messages.append(msg)
        except Exception as e:
            print(f"[ERROR] Failed to send video: {e}")
    if sent_messages:
        asyncio.create_task(delete_messages_after(sent_messages, AUTO_DELETE_SECONDS))
    else:
        msg = await client.send_message(chat_id=chat_id, text=WELCOME_CAPTION, parse_mode=enums.ParseMode.HTML)
        asyncio.create_task(delete_messages_after([msg], AUTO_DELETE_SECONDS))

async def send_to_all_users(client: Client, message_text: str) -> None:
    """Send message to all tracked users."""
    print(f"[INFO] Sending message to {len(users_set)} users")
    success = 0
    failed = 0
    for user_id in users_set:
        try:
            await client.send_message(user_id, message_text, parse_mode=enums.ParseMode.HTML)
            success += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[WARN] Failed to send to {user_id}: {e}")
            failed += 1
    print(f"[INFO] Message sent: {success} success, {failed} failed")

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message) -> None:
    user_id = message.from_user.id
    save_user(user_id)
    print(f"[INFO] /start from user {user_id}")
    await message.reply("⚠️ <b>To continue, please join all required channels first.</b>\n\n📌 Join both channels below, then tap <b>✅ Verify</b> to unlock the bot.", reply_markup=join_keyboard(), parse_mode=enums.ParseMode.HTML)

@app.on_callback_query(filters.regex("^verify$"))
async def verify_callback(client: Client, callback_query) -> None:
    user = callback_query.from_user
    save_user(user.id)
    if not await is_fully_subscribed(client, user.id):
        await callback_query.answer("❌ Join all required channels first!", show_alert=True)
        return
    await callback_query.answer("✅ Verified! Welcome aboard 🎉")
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await send_welcome(client, callback_query.message.chat.id)

@app.on_message(filters.command("notify"))
async def notify_handler(client: Client, message: Message) -> None:
    """Send notification to all users. Usage: /notify <message>"""
    print(f"[INFO] Notify command from user {message.from_user.id}")
    
    # Get message text
    if not message.text or len(message.text.split(None, 1)) < 2:
        await message.reply("Usage: /notify <message>\n\nExample: /notify Bot is active, you can use now")
        return
    
    notify_text = message.text.split(None, 1)[1]
    print(f"[INFO] Sending notification: {notify_text}")
    await message.reply(f"📢 Sending to {len(users_set)} users...")
    await send_to_all_users(client, notify_text)
    await message.reply("✅ Message sent to all users!")

if __name__ == "__main__":
    from keep_alive import keep_alive
    load_users()
    keep_alive()
    print("Keep-alive server started.")
    print("Bot is starting…")
    app.run()
