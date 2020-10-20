# For The-TG-Bot

import heroku3

api_key = ENV.HEROKU_API_KEY
app_name = ENV.TG_APP_NAME
heroku = heroku3.from_key(api_key) if api_key else None


@client.on(events(pattern="shutdown", allow_sudo=True))
async def scale_zero(e):
    if heroku is None or app_name is None:
        return await e.edit("`Mind reading the help?`")
    await e.edit("`Scaling to worker@0`")
    app = heroku.apps()[app_name]
    app.process_formation()['worker'].scale(0)
    await e.edit(f"`Switched off\nTurn on the `[dynos switch](https://dashboard.heroku.com/apps/{app_name}/resources)` to restart The-TG-Bot`")
     
     
@client.on(events(pattern="restart ?(.*)", allow_sudo=True))
async def _restart(message):
    args = message.pattern_match.group(1)
    if "-h" in args:
        if heroku is None or app_name is None:
            return await message.edit("Read `.help core` first!")
        app = heroku.apps()[app_name]
        app.restart()
        return await message.edit("`The-TG-Bot v3 has been updated and the heroku app has been restarted, it should be back online in a few seconds.`")
    await message.edit("`The-TG-Bot v3 has been restarted.\nTry .alive or .ping to check if its alive.`")
    client.sync(restart)  # await restart() random crash workaround


@client.on(events(pattern="env (get|set|del) ?(.*)"))
async def env_variables(event):
    if event.fwd_from:
        return
    if heroku is None or app_name is None: 
        return await event.edit("`Like I care.`")
    app = heroku.apps()[app_name]
    env = app.config()
    command = event.pattern_match.group(1)
    args = event.pattern_match.group(2)
    if command == "get":
        args = args.upper()
        if args in env:
            await event.edit(f"Key: `{args}`\nValue: `{env[args]}`")
        else:
            await event.edit(f"ENV Variable `{args}` doesn't exist!")
    elif command == "set":
        configs = {}
        message = ""
        # SYNTAX: <key> <value> ; <key> <value> ; <key> <value> ; etc.
        for config in args.split(";"):
            key = config.strip().split()[0]
            value = config.strip().split()[1]
            configs.update({u"{}".format(key) : u"{}".format(value)})
            message += f"Key: `{key}`\nValue: `{value}`\n\n"
        env.update(configs)
        await event.edit("Modified/new env variables:\n\n" + message)
    elif command == "del":
        args = args.upper()
        del env[args]
        await event.edit(f"Deleted env variable `{args}`")
        
        
async def restart():
    await client.disconnect()
    os.execl(sys.executable, sys.executable, *sys.argv)
   
        
        
ENV.HELPER.update({
    "heroku": "\
`.restart`\
\nUsage: Restart the telegram client.\
\n\n`.restart [-h/-heroku]`\
\nUsage: Restart the heroku app and update the bot to the latest version.\
\n\n`.shutdown`\
\nUsage: Turns off the the bot by turning off dynos.\
\n\n`.env get <key>`\
\nUsage: Return the value of an env variable.\
\n\n`.env set <key> <value>`\
\nUsage: Sets a new env variable or updates an existing variable.\
\nSeperate with `;` to set multiple variables at once.\
\n\n`.env del <key>`\
\nUsage: Deletes an env variable.\
\n\n\n**NOTE:** This module requires the following env variables:\
\n\n~ `HEROKU_API_KEY` :  __To get a valid API key, goto https://dashboard.heroku.com/account/__\
\n\n~ `TG_APP_NAME` :  __Simply copy and paste the bot app name in ENV variable TG_APP_NAME__\
"
})
