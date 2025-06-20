import random
import asyncio
import time
from logging import getLogger
from time import time

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFont
from pyrogram import enums, filters
from pyrogram.types import ChatMemberUpdated

from ChampuMusic import app
from ChampuMusic.utils.database import get_assistant
from pymongo import MongoClient
from config import MONGO_DB_URI

# Define a dictionary to track the last message timestamp for each user
user_last_message_time = {}
user_command_count = {}
# Define the threshold for command spamming (e.g., 20 commands within 60 seconds)
SPAM_THRESHOLD = 2
SPAM_WINDOW_SECONDS = 5

LOGGER = getLogger(__name__)

champu = [
    "ʜᴇʏ", "ʜᴏᴡ ᴀʀᴇ ʏᴏᴜ?", "ʜᴇʟʟᴏ", "ʜɪ", "ᴋᴀɪsᴇ ʜᴏ?", "ᴡᴇʟᴄᴏᴍᴇ ᴊɪ", "ᴡᴇʟᴄᴏᴍᴇ",
    "ᴀᴀɪʏᴇ ᴀᴀɪʏᴇ", "ᴋᴀʜᴀ ᴛʜᴇ ᴋᴀʙsᴇ ᴡᴀɪᴛ ᴋᴀʀ ʀʜᴇ ᴀᴘᴋᴀ", "ɪss ɢʀᴏᴜᴘ ᴍᴀɪɴ ᴀᴘᴋᴀ sᴡᴀɢᴀᴛ ʜᴀɪ",
    "ᴏʀ ʙᴀᴛᴀᴏ sᴜʙ ʙᴀᴅʜɪʏᴀ", "ᴀᴘᴋᴇ ᴀᴀɴᴇ sᴇ ɢʀᴏᴜᴘ ᴏʀ ᴀᴄʜʜᴀ ʜᴏɢʏᴀ",
    
    "✦ 𝐇𝐞𝐥𝐥𝐨! 𝐊𝐚𝐡𝐚𝐧 𝐭𝐡𝐞 𝐚𝐚𝐩? 𝐇𝐚𝐦 𝐤𝐚𝐛𝐬𝐞 𝐰𝐚𝐢𝐭 𝐤𝐚𝐫 𝐫𝐚𝐡𝐞 𝐭𝐡𝐞! ✦",
    "★彡 𝐀𝐫𝐞𝐲! 𝐀𝐚𝐩 𝐚𝐛 𝐚𝐚𝐲𝐞? 𝐊𝐚𝐢𝐬𝐞 𝐡𝐨? 彡★",
    "⭑❥ 𝐇𝐞𝐲! 𝐅𝐢𝐧𝐚𝐥𝐥𝐲 𝐚𝐚 𝐠𝐚𝐲𝐞! 𝐇𝐨𝐰 𝐚𝐫𝐞 𝐲𝐨𝐮? ❥⭑",
    "꧁༒☬ 𝐇𝐞𝐥𝐥𝐨! 𝐇𝐚𝐦𝐚𝐫𝐢 𝐝𝐮𝐧𝐢𝐲𝐚 𝐦𝐞 𝐚𝐚𝐩𝐤𝐚 𝐬𝐰𝐚𝐠𝐚𝐭 𝐡𝐚𝐢! ☬༒꧂",
    "┏━✦❘༻༺❘✦━┓ 𝐊𝐚𝐡𝐚𝐧 𝐭𝐡𝐞 𝐛𝐡𝐚𝐢? 𝐁𝐨𝐡𝐨𝐭 𝐝𝐢𝐧 𝐛𝐚𝐚𝐝 𝐝𝐢𝐤𝐡𝐚𝐢 𝐝𝐢𝐲𝐞! ┏━✦❘༻༺❘✦━┓",
    "𓆩♡𓆪 𝐎𝐨𝐲𝐞! 𝐇𝐞𝐥𝐥𝐨, 𝐤𝐚𝐢𝐬𝐞 𝐡𝐨? 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐭𝐡𝐞 𝐟𝐚𝐦! 𓆩♡𓆪",
    "━❀❀━ 𝐀𝐫𝐞𝐲! 𝐀𝐚𝐩 𝐤𝐚𝐡𝐚𝐧 𝐠𝐮𝐦 𝐭𝐡𝐞? 𝐇𝐚𝐦 𝐭𝐨 𝐢𝐧𝐭𝐳𝐚𝐚𝐫 𝐦𝐞 𝐭ʜᴇ! ━❀❀━",
    "★彡 𝐖𝐨𝐰! 𝐀𝐚𝐣 𝐬𝐮𝐫𝐚𝐣 𝐤𝐢𝐝ʜᴀʀ 𝐬ᴇ 𝐧ɪᴋʟᴀ? 𝐀𝐚𝐩 𝐚𝐚 𝐠𝐚ʏᴇ! 彡★",
    "❖ 𝐁𝐡𝐚𝐢! 𝐀𝐚𝐣 𝐭𝐨 𝐛𝐢𝐥𝐞𝐭 𝐡𝐢 𝐥𝐚𝐠 𝐠𝐚𝐲𝐚! 𝐀𝐚𝐩 𝐚𝐚 𝐠𝐚𝐲𝐞! ❖",
    "☠️👑 𝐀𝐫𝐞 𝐁𝐚𝐝𝐬𝐡𝐚𝐡! 𝐀𝐚 𝐠𝐚𝐲𝐞 𝐚𝐩𝐧𝐞 𝐆𝐂 𝐦𝐞? 𝐍𝐚𝐦𝐚𝐧 𝐡𝐚𝐢! 👑☠️",

    "✦ 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐎𝐮𝐫 𝐆𝐂 ✦",
    "•★ 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐎𝐮𝐫 𝐒𝐦𝐚𝐥𝐥 𝐖𝐨𝐫𝐥𝐝 ★•",
    "𓆩♡𓆪 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐎𝐮𝐫 𝐆𝐂 𓆩♡𓆪",
    "⭑★ 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐎𝐮𝐫 𝐅𝐚𝐦𝐢𝐥𝐲 ★⭑",
    "𒆜 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐎𝐮𝐫 𝐖𝐨𝐫𝐥𝐝 𒆜",
    "━❀❀━ 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐎𝐮𝐫 𝐊𝐢𝐧𝐠𝐝𝐨𝐦 ━❀❀━",
    "★彡 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐎𝐮𝐫 𝐏𝐚𝐫𝐚𝐝𝐢𝐬𝐞 彡★",
    "╰☆☆ 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐇𝐞𝐚𝐯𝐞𝐧 ☆☆╮",
    "꧁༒☬ 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐎𝐮𝐫 𝐆𝐚𝐧𝐠 ☬༒꧂",
    "❖ 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐎𝐮𝐫 𝐋𝐞𝐠𝐞𝐧𝐝𝐬 𝐅𝐚𝐦𝐢𝐥𝐲 ❖"
]

class temp:
    ME = None
    CURRENT = 2
    CANCEL = False
    MELCOW = {}
    U_NAME = None
    B_NAME = None


# Database setup for welcome status
awelcomedb = MongoClient(MONGO_DB_URI)
astatus_db = awelcomedb.awelcome_status_db.status

async def get_awelcome_status(chat_id):
    status = astatus_db.find_one({"chat_id": chat_id})
    if status:
        return status.get("welcome", "on")
    return "on"

async def set_awelcome_status(chat_id, state):
    astatus_db.update_one(
        {"chat_id": chat_id},
        {"$set": {"welcome": state}},
        upsert=True
    )

# Command to toggle welcome message
@app.on_message(filters.command("awelcome") & ~filters.private)
async def auto_state(_, message):
    user_id = message.from_user.id
    current_time = time()

    last_message_time = user_last_message_time.get(user_id, 0)
    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_last_message_time[user_id] = current_time
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            hu = await message.reply_text(
                f"**{message.from_user.mention} ᴘʟᴇᴀsᴇ ᴅᴏɴᴛ ᴅᴏ sᴘᴀᴍ, ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ 5 sᴇᴄ**"
            )
            await asyncio.sleep(3)
            await hu.delete()
            return
    else:
        user_command_count[user_id] = 1
        user_last_message_time[user_id] = current_time

    usage = "**ᴜsᴀɢᴇ:**\n**⦿ /awelcome [on|off]**"
    if len(message.command) == 1:
        return await message.reply_text(usage)

    chat_id = message.chat.id
    user = await app.get_chat_member(message.chat.id, message.from_user.id)
    if user.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        state = message.text.split(None, 1)[1].strip().lower()
        current_status = await get_awelcome_status(chat_id)

        if state == "off":
            if current_status == "off":
                await message.reply_text("** ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ᴀʟʀᴇᴀᴅʏ ᴅɪsᴀʙʟᴇᴅ!**")
            else:
                await set_awelcome_status(chat_id, "off")
                await message.reply_text(f"**ᴅɪsᴀʙʟᴇᴅ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ɪɴ** {message.chat.title} **ʙʏ ᴀssɪsᴛᴀɴᴛ**")
        elif state == "on":
            if current_status == "on":
                await message.reply_text("**ᴇɴᴀʙʟᴇᴅ ᴀssɪsᴛᴀɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ᴀʟʀᴇᴀᴅʏ!**")
            else:
                await set_awelcome_status(chat_id, "on")
                await message.reply_text(f"**ᴇɴᴀʙʟᴇᴅ ᴀssɪsᴛᴀɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ɪɴ** {message.chat.title}")
        else:
            await message.reply_text(usage)
    else:
        await message.reply("**sᴏʀʀʏ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴇɴᴀʙʟᴇ ᴀssɪsᴛᴀɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ!**")

# Auto-welcome message for new members
@app.on_chat_member_updated(filters.group, group=5)
async def greet_new_members(_, member: ChatMemberUpdated):
    userbot = await get_assistant(member.chat.id)
    try:
        chat_id = member.chat.id
        welcome_status = await get_awelcome_status(chat_id)
        if welcome_status == "off":
            return

        user = member.new_chat_member.user

        if member.new_chat_member and not member.old_chat_member:
            welcome_text = f"[{user.first_name}](tg://user?id={user.id}), {random.choice(champu)}"
            await userbot.send_message(chat_id, text=welcome_text)

    except Exception as e:
        LOGGER.error(e)
        return
        
