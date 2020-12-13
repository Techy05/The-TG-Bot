# Based on the plugin of UsergeTeam/Userge-Plugins
# For The-TG-Bot v3

from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.contacts import UnblockRequest


@client.on(events(pattern="history ?(.*)"))
async def handler(event):
    if event.fwd_from:
        return 
    reply = await event.get_reply_message()
    entity = event.pattern_match.group(1).replace("-u", "").strip()
    if reply:
        user = reply.from_id
    elif entity:
        try:
            userObj = await client(GetFullUserRequest(entity))
        except:
            return await event.edit("`This person is yet to be born!`")
        user = userObj.user.id
    else:
        user = client.uid
    await event.edit("`Stealing data from Telegram's database..`")
    bot = "@SangMataInfo_bot"
    await client(UnblockRequest(bot))
    async with client.conversation(bot) as conv:
        await conv.send_message(f"/search_id {user}")
        msg1 = await conv.get_response()
        msg2 = await conv.get_response()
        if "no records found" in msg2.raw_text.lower():
            conv.cancel()
            return await event.edit("`I don't keep biodata of aliens!`")
        msg3 = await conv.get_response()
        await conv.mark_read()
    for msg in [msg1.text, msg2.text, msg3.text]:
        if "Name" in msg:
            names = msg
        elif "Username" in msg:
            usernames = msg
    if "-u" in event.text:
        await event.edit(usernames)
    else:
        await event.edit(names)


ENV.HELPER.update({
    "history": "\
`.history [reply/user]`\
\nUsage: Gets name history of a user. Returns your name history if no user is given.\
\n\n`.history [reply/user] -u`\
\nUsage: Gets username history of a user. Returns your username history if no user is given.\
"
})
