# For The-TG-Bot v3
# Syntax (.approve, .disapprove, .block, .listpms)

import os
import asyncio
import json
from modules.sql.pmpermit_sql import is_approved, approve, disapprove, get_all_approved
from telethon.tl import functions, types

client.storage.PM_WARNS = {}
client.storage.PREV_REPLY_MESSAGE = {}
BAALAJI_TG_USER_BOT = "`My Master hasn't approved you to PM.`"
TG_COMPANION_USER_BOT = "`Wait for my masters response.\nDo not spam his pm if you do not want to get blocked.`"
THETGBOT_USER_BOT_WARN_ZERO = "`Blocked! Thanks for the spam.`"
THETGBOT_USER_BOT_NO_WARN = "\
`Bleep blop! This is a bot. Don't fret.\
\nMy master hasn't approved you to PM.`\
\n`Please wait for my master to look in, he mostly approves PMs.\
As far as I know, he doesn't usually approve retards though.`\
`If you continue sending messages you will be blocked.`\
"

EXCEPTIONS = [777000, 1017305299, 1109396517]

@client.on(events(outgoing=True, func=lambda e: e.is_private))
async def auto_approve(event):
    user = await client(functions.users.GetFullUserRequest(int(event.chat_id)))
    if ("block" in event.text or "disapprove" in event.text or user.user.bot):
        return False
    reason = "auto_approve"
    chat = await event.get_chat()
    if ENV.ANTI_PM_SPAM:
        if not is_approved(chat.id):
            if chat.id in client.storage.PM_WARNS:
                del client.storage.PM_WARNS[chat.id]
            if chat.id in client.storage.PREV_REPLY_MESSAGE:
                await client.storage.PREV_REPLY_MESSAGE[chat.id].delete()
                del client.storage.PREV_REPLY_MESSAGE[chat.id]
            approve(chat.id, reason)
            msg = await client.send_message(
                      event.chat_id,
                      f"__Approved {user.user.first_name}, cuz outgoing message__",
                      silent=True
                  )
            logger.info("Auto approved user: " + str(chat.id))
            await asyncio.sleep(2)
            await msg.delete()


@client.on(events(incoming=True, func=lambda e: e.is_private))
async def monitorpms(event):
    sender = await event.get_sender()
    current_message_text = event.message.message.lower()
    if current_message_text == BAALAJI_TG_USER_BOT or \
            current_message_text == TG_COMPANION_USER_BOT or \
            current_message_text == THETGBOT_USER_BOT_WARN_ZERO:
        # userbot's should not reply to other userbot's
        # https://core.telegram.org/bots/faq#why-doesn-39t-my-bot-see-messages-from-other-bots
        return False
    if (ENV.ANTI_PM_SPAM and not sender.bot and sender.id not in EXCEPTIONS):
        chat = await event.get_chat()
        if not is_approved(chat.id) and chat.id != client.uid:
            logger.info(chat.stringify())
            logger.info(client.storage.PM_WARNS)
            if chat.id in ENV.SUDO_USERS:
                await event.edit("Oh wait, that looks like my master!")
                await event.edit("Approving..")
                approve(chat.id, "SUDO_USER")
            if chat.id not in client.storage.PM_WARNS:
                client.storage.PM_WARNS.update({chat.id: 0})
            if client.storage.PM_WARNS[chat.id] == ENV.MAX_PM_FLOOD:
                r = await event.reply(THETGBOT_USER_BOT_WARN_ZERO)
                await asyncio.sleep(3)
                await client(functions.contacts.BlockRequest(chat.id))
                if chat.id in client.storage.PREV_REPLY_MESSAGE:
                    await client.storage.PREV_REPLY_MESSAGE[chat.id].delete()
                client.storage.PREV_REPLY_MESSAGE[chat.id] = r
                return
            r = await event.reply(f"{THETGBOT_USER_BOT_NO_WARN}\n`Messages remaining: {int(ENV.MAX_PM_FLOOD - client.storage.PM_WARNS[chat.id])} out of {int(ENV.MAX_PM_FLOOD)}`")
            client.storage.PM_WARNS[chat.id] += 1
            if chat.id in client.storage.PREV_REPLY_MESSAGE:
                await client.storage.PREV_REPLY_MESSAGE[chat.id].delete()
            client.storage.PREV_REPLY_MESSAGE[chat.id] = r


@client.on(events("approve ?(.*)"))
async def approve_pm(event):
    if event.fwd_from:
        return
    reason = event.pattern_match.group(1)
    chat = await event.get_chat()
    if ENV.ANTI_PM_SPAM:
        if event.is_private:
            if not is_approved(chat.id):
                if chat.id in client.storage.PM_WARNS:
                    del client.storage.PM_WARNS[chat.id]
                if chat.id in client.storage.PREV_REPLY_MESSAGE:
                    await client.storage.PREV_REPLY_MESSAGE[chat.id].delete()
                    del client.storage.PREV_REPLY_MESSAGE[chat.id]
                approve(chat.id, reason)
                await event.edit("PM accepted.")
                await asyncio.sleep(3)
                await event.delete()


@client.on(events("block ?(.*)"))
async def approve_p_m(event):
    if event.fwd_from:
        return
    reason = event.pattern_match.group(1)
    chat = await event.get_chat()
    if ENV.ANTI_PM_SPAM:
        if event.is_private:
            if is_approved(chat.id):
                disapprove(chat.id)
            await event.edit("Blocked PM.")
            await asyncio.sleep(3)
            await client(functions.contacts.BlockRequest(chat.id))
            logger.info("Blocked user: " + str(chat.id))


@client.on(events("disapprove ?(.*)"))
async def disapprove_pm(event):
    if event.fwd_from:
        return
    input = event.pattern_match.group(1)
    if input:
        id = str(input)
    else:
        if event.is_private:
            id = (await event.get_chat()).id
    if ENV.ANTI_PM_SPAM:
        if is_approved(id):
            disapprove(id)
            await event.edit(f"Disapproved PM from {id}")
            logger.info("Disapproved user: " + str(id))
            await asyncio.sleep(1)
            await event.delete()


@client.on(events("listpms?"))
async def approve_p_m(event):
    if event.fwd_from:
        return
    await event.edit("Fetching approved PMs list...")
    approved_users = get_all_approved()
    APPROVED_PMs = "**Current Approved PMs**\n\n"
    for a_user in approved_users:
        id = a_user.chat_id
        try:
            user = await client(functions.users.GetFullUserRequest(int(id)))
            name = user.user.first_name
        except:
            name = "~~deleted~~"
        userid = str(id)
        if len(userid) < 10:
            userid = userid + " "*(10 - len(userid))
        APPROVED_PMs += f"~ `{userid}`` - `{name}\n"
    
    if len(APPROVED_PMs) > Config.MAX_MESSAGE_SIZE_LIMIT:
        # fixed by authoritydmc
        out_file_name = "approved_pms.txt"
        output_file_ref = None
        with open(out_file_name, "w") as f:
            f.write(APPROVED_PMs)
            output_file_ref = f.name
        await client.send_file(
            event.chat_id,
            output_file_ref,
            force_document=True,
            allow_cache=False,
            caption="Current Approved PMs",
        )
        await event.delete()
        os.remove(output_file_ref)
    else:
        await event.edit(APPROVED_PMs)

ENV.HELPER.update({
    "pmpermit": "\
`.approve`\
\nUsage: Approve a user in PMs.\
\n\n`.disapprove`\
\nUsage: Disapprove a user in PMs.\
\n\n`.block`\
\nUsage: Block a user from your PMs.\
\n\n`.listpms`\
\nUsage: Get approved PMs.\
"
})
