# For The-TG-Bot
 
import re
from telethon.tl.functions.users import GetFullUserRequest


@client.on(events(forwards=False))
async def faketag(e):
    string = e.text
    pattern=".*@[^ ]*\|[^ ]*.*"
    if not re.match(pattern, string):
        return False
    for group in string.split():
        if re.match(pattern, group):
            original = group.split("|")[0]
            fake = group.split("|")[1]
            try:
                user = await client(GetFullUserRequest(original))
                link = f"[{fake}](tg://user?id={user.user.id})"
            except:
                # Invalid username
                return False
            string = string.replace(group, link)
    await e.delete()
    await client.send_message(e.chat_id, string, reply_to=e.reply_to_msg_id)

