# For The-TG-Bot v3
# By Priyam Kalra
# Modified by @Techy05 (13/09/20)

from random import choice

LOCATION = ["Mercury", "Venus", "Mars", "Jupiter", "Uranus", 
            "Saturn", "Netune", "Pluto", "Titan", "Europa", 
            "Callisto", "Ganymede", "Luna", "Eris", "Ceres"]
            
@client.on(events(pattern="log$"))
async def handler(event):
    if event.fwd_from:
        return
    rep = await event.get_reply_message()
    link = await log(rep)
    await event.edit(f"**Logged to** [{choice(LOCATION)}]({link})**!**")

async def log(rep):
    LOGGER = ENV.LOGGER_GROUP
    msg = await client.send_message(LOGGER, rep, parse_mode="html")
    link = f"https://t.me/c/{str(LOGGER).replace('-100', '')}/{msg.id}"
    return link
    

ENV.HELPER.update({"log": "\
`.log (as a reply)`\
\nUsage: Simply log the replied msg to logger group.\
"})
