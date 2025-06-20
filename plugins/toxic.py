import google.generativeai as genai
from pyrogram import filters
from pyrogram.types import Message
from ChampuMusic import app

# Configure Gemini API
genai.configure(api_key="AIzaSyA_a_X6a8vTKjiISMtLDkJ-azfjZg9pIqg")  # Replace with your real key

model = genai.GenerativeModel("gemini-1.5-flash")

# Toxic message checker
async def is_toxic(text: str) -> bool:
    prompt = (
        "Check if the following message contains a clearly abusive or vulgar word "
        "(Hindi or English), even if the word is written using symbols like *, #, @, $ etc. "
        "Ignore tone, sarcasm, jokes, or anger. Only reply 'yes' if the message has a real gaali. "
        "If not, reply 'no'.\n\n"
        f"Message: \"{text}\""
    )
    try:
        response = await model.generate_content_async(prompt)
        result = response.text.strip().lower()
        return "yes" in result
    except Exception:
        return False

# Handler to check and delete message
@app.on_message(filters.text & filters.group, group=9)
async def moderation(_, message: Message):
    if message.from_user and not message.from_user.is_bot:
        if await is_toxic(message.text):
            try:
                await message.delete()
                await message.reply_text(
                     f"🚫 {message.from_user.mention}\nYour Message deleted due to offensive language. Please keep it clean.",
                    quote=True
                )
            except Exception:
                pass
