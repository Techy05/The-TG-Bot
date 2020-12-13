# For The-TG-Bot v3
# Syntax .tr <language_name>


from goslate import Goslate


@client.on(events("tr ?(.*)"))
async def translate(event):
    if event.fwd_from:
        return
    args = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if reply:
        lang = args if args else "en"
        text = reply.text
    elif len(args.split()) > 1:
        lang = args.split()[0]
        text = args.split(maxsplit=1)[1]
    else:
        return False

    src = Goslate().detect(text)
    src = Goslate().get_languages()[src]
    translation = Goslate().translate(text, lang)
    await event.edit(f"**Translated from** `{src}` **to** `{lang}`:\n`{translation}`")

ENV.HELPER.update({
    "translate": "\
`.tr [language_code] [reply/input]`\
\nUsage: Translate target message to another language.\
\nClick [here](https://meta.wikimedia.org/wiki/Template:List_of_language_names_ordered_by_code) to see a detailed list of all language codes.\
"
})
