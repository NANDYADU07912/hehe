from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPermissions
from pymongo import MongoClient
from ChampuMusic import app
import asyncio
from ChampuMusic.misc import SUDOERS
from config import MONGO_DB_URI
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import (
    ChatAdminRequired,
    UserNotParticipant,
)

fsubdb = MongoClient(MONGO_DB_URI)
forcesub_collection = fsubdb.status_db.status
# New collection for tracking user message counts
user_message_collection = fsubdb.status_db.user_messages

@app.on_message(filters.command(["fsub", "forcesub"]) & filters.group)
async def set_forcesub(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    member = await client.get_chat_member(chat_id, user_id)
    # Allow sudoers, group owner, and group admins
    if not (member.status in ["owner", "administrator"] or user_id in SUDOERS):
        return await message.reply_text("**ᴏɴʟʏ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀs, ᴀᴅᴍɪɴs ᴏʀ sᴜᴅᴏᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.**")

    if len(message.command) == 2 and message.command[1].lower() in ["off", "disable"]:
        forcesub_collection.delete_one({"chat_id": chat_id})
        # Clear all user message counts for this group
        user_message_collection.delete_many({"chat_id": chat_id})
        return await message.reply_text("**ғᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ʜᴀs ʙᴇᴇɴ ᴅɪsᴀʙʟᴇᴅ ғᴏʀ ᴛʜɪs ɢʀᴏᴜᴘ.**")

    if len(message.command) != 2:
        return await message.reply_text("**ᴜsᴀɢᴇ: /ғsᴜʙ <ᴄʜᴀɴɴᴇʟ ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ɪᴅ> ᴏʀ /ғsᴜʙ ᴏғғ ᴛᴏ ᴅɪsᴀʙʟᴇ**")

    channel_input = message.command[1]

    try:
        channel_info = await client.get_chat(channel_input)
        channel_id = channel_info.id
        channel_username = f"{channel_info.username}" if channel_info.username else None

        forcesub_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"channel_id": channel_id, "channel_username": channel_username}},
            upsert=True
        )

        await message.reply_text(f"**🎉 Force subscription set to channel:** [{channel_info.title}](https://t.me/{channel_username})")

    except Exception as e:
        await message.reply_text("**🚫 Failed to set force subscription.**")
        
# Monitor channel member updates for instant unmute
@app.on_chat_member_updated()
async def on_channel_member_updated(client: Client, chat_member_updated):
    # Get all groups where this channel is set for force subscription
    channel_id = chat_member_updated.chat.id
    user_id = chat_member_updated.from_user.id
    
    # Check if this update is from a channel (not a group)
    if chat_member_updated.chat.type not in ["channel", "supergroup"]:
        return
    
    # Find all groups that have this channel as force subscription
    groups_with_forcesub = forcesub_collection.find({"channel_id": channel_id})
    
    new_member = chat_member_updated.new_chat_member
    if new_member and new_member.status == "member":
        # User joined the channel, unmute them in all groups
        for group_data in groups_with_forcesub:
            group_id = group_data["chat_id"]
            channel_username = group_data["channel_username"]
            
            try:
                # Check if user is muted in this group
                user_data = user_message_collection.find_one({"chat_id": group_id, "user_id": user_id})
                if user_data:
                    # Remove user from message tracking
                    user_message_collection.delete_one({"chat_id": group_id, "user_id": user_id})
                    
                    # Unmute the user
                    await client.restrict_chat_member(
                        group_id,
                        user_id,
                        permissions=ChatPermissions(
                            can_send_messages=True,
                            can_send_media_messages=True,
                            can_send_other_messages=True,
                            can_add_web_page_previews=True
                        )
                    )
                    await client.send_message(
                        group_id,
                        f"**🎉 {chat_member_updated.from_user.mention}, you have been unmuted because you joined the [channel](https://t.me/{channel_username}).**",
                        disable_web_page_preview=True
                    )
            except Exception as e:
                print(f"Error unmuting user in group {group_id}: {e}")

@app.on_chat_member_updated()
async def on_group_member_join(client: Client, chat_member_updated):
    chat_id = chat_member_updated.chat.id
    user_id = chat_member_updated.from_user.id
    
    # Check if this is a group update
    if chat_member_updated.chat.type not in ["group", "supergroup"]:
        return
        
    forcesub_data = forcesub_collection.find_one({"chat_id": chat_id})
    if not forcesub_data:
        return  # No force subscription set for this group

    channel_id = forcesub_data["channel_id"]
    
    new_chat_member = chat_member_updated.new_chat_member
    if new_chat_member is None:
        return  # Exit if new_chat_member is None

    # Check if the user joined the group
    if new_chat_member.status == "member":
        try:
            # Check if the user is a member of the channel
            user_member = await app.get_chat_member(channel_id, user_id)
            # If the user is a member of the channel, do nothing
            return
        except UserNotParticipant:
            # User is not a member of the channel, initialize their message count
            user_message_collection.update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {"$set": {"message_count": 0}},
                upsert=True
            )
        except Exception as e:
            # Handle any other exceptions if necessary
            print(f"Error checking channel membership: {e}")
            
@app.on_callback_query(filters.regex("close_force_sub"))
async def close_force_sub(client: Client, callback_query: CallbackQuery):
    await callback_query.answer("ᴄʟᴏsᴇᴅ!")
    await callback_query.message.delete()
    

async def check_forcesub(client: Client, message: Message):
    chat_id = message.chat.id

    # Check if the message has a from_user attribute
    if message.from_user is None:
        return True  # Allow messages without from_user

    user_id = message.from_user.id
    forcesub_data = forcesub_collection.find_one({"chat_id": chat_id})
    if not forcesub_data:
        return True  # No force subscription set

    channel_id = forcesub_data["channel_id"]
    channel_username = forcesub_data["channel_username"]

    try:
        user_member = await app.get_chat_member(channel_id, user_id)
        if user_member:
            # User is a member, remove from tracking if exists
            user_message_collection.delete_one({"chat_id": chat_id, "user_id": user_id})
            return True
    except UserNotParticipant:
        # User is not a member of the channel - DELETE MESSAGE and show warning
        user_data = user_message_collection.find_one({"chat_id": chat_id, "user_id": user_id})
        
        if user_data:
            message_count = user_data.get("message_count", 0)
            
            if message_count >= 3:
                # User has already sent 3 messages, should be muted - DELETE MESSAGE
                return False
            else:
                # Increment message count
                user_message_collection.update_one(
                    {"chat_id": chat_id, "user_id": user_id},
                    {"$inc": {"message_count": 1}}
                )
                
                # Check if this is the 3rd message
                if message_count + 1 >= 3:
                    # Mute the user after 3 messages
                    try:
                        await client.restrict_chat_member(
                            chat_id,
                            user_id,
                            permissions=ChatPermissions(can_send_messages=False)
                        )
                        await client.send_message(
                            chat_id,
                            f"**🚫 {message.from_user.mention}, you have been muted because you didn't join the [channel](https://t.me/{channel_username}) after 3 messages.**",
                            disable_web_page_preview=True
                        )
                    except Exception as e:
                        print(f"Error muting user: {e}")
                    return False  # DELETE MESSAGE
                else:
                    # Show warning message but DELETE the current message
                    remaining_messages = 3 - (message_count + 1)
                    if channel_username:
                        channel_url = f"https://t.me/{channel_username}"
                    else:
                        invite_link = await app.export_chat_invite_link(channel_id)
                        channel_url = invite_link
                    
                    await message.reply_photo(
                        photo="https://envs.sh/Tn_.jpg",
                        caption=(f"**👋 ʜᴇʟʟᴏ {message.from_user.mention},**\n\n**ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴊᴏɪɴ ᴛʜᴇ [ᴄʜᴀɴɴᴇʟ]({channel_url}) ᴛᴏ sᴇɴᴅ ᴍᴇssᴀɢᴇs ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.**\n\n**⚠️ ᴡᴀʀɴɪɴɢ: {remaining_messages} ᴍᴇssᴀɢᴇs ʟᴇғᴛ ʙᴇғᴏʀᴇ ᴍᴜᴛᴇ!**"),
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("๏ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ๏", url=channel_url)]]),
                    )
                    await asyncio.sleep(1)
                
                return False  # DELETE MESSAGE
        else:
            # First message from user, initialize count
            user_message_collection.update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {"$set": {"message_count": 1}},
                upsert=True
            )
            
            if channel_username:
                channel_url = f"https://t.me/{channel_username}"
            else:
                invite_link = await app.export_chat_invite_link(channel_id)
                channel_url = invite_link
            
            await message.reply_photo(
                photo="https://envs.sh/Tn_.jpg",
                caption=(f"**👋 ʜᴇʟʟᴏ {message.from_user.mention},**\n\n**ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴊᴏɪɴ ᴛʜᴇ [ᴄʜᴀɴɴᴇʟ]({channel_url}) ᴛᴏ sᴇɴᴅ ᴍᴇssᴀɢᴇs ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.**\n\n**⚠️ ᴡᴀʀɴɪɴɢ: 2 ᴍᴇssᴀɢᴇs ʟᴇғᴛ ʙᴇғᴏʀᴇ ᴍᴜᴛᴇ!**"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("๏ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ๏", url=channel_url)]]),
            )
            await asyncio.sleep(1)
            return False  # DELETE MESSAGE
            
    except ChatAdminRequired:
        forcesub_collection.delete_one({"chat_id": chat_id})
        user_message_collection.delete_many({"chat_id": chat_id})
        await message.reply_text("**🚫 I'ᴍ ɴᴏ ʟᴏɴɢᴇʀ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ғᴏʀᴄᴇᴅ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴄʜᴀɴɴᴇʟ. ғᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ʜᴀs ʙᴇᴇɴ ᴅɪsᴀʙʟᴇᴅ.**")
        return True

@app.on_message(filters.group, group=30)
async def enforce_forcesub(client: Client, message: Message):
    # Check if user should be allowed to send messages
    allowed = await check_forcesub(client, message)
    
    if not allowed:
        # Delete the message if user is not allowed (muted or not joined)
        try:
            await message.delete()
        except Exception as e:
            print(f"Error deleting message: {e}")
        return


__MODULE__ = "ғsᴜʙ"
__HELP__ = """**
/fsub <ᴄʜᴀɴɴᴇʟ ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ɪᴅ> - sᴇᴛ ғᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ғᴏʀ ᴛʜɪs ɢʀᴏᴜᴘ.
/fsub off - ᴅɪsᴀʙʟᴇ ғᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ғᴏʀ ᴛʜɪs ɢʀᴏᴜᴘ.

**ɴᴏᴛᴇ:** Users get 3 messages before being muted. They are automatically unmuted when they join the channel.**
"""
