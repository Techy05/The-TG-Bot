# Userge Plugin for Torrent Search from torrent-paradise.ml
# Author: Nageen (https://github.com/archie9211) (@archie9211)

import re
import requests


@client.on(events("torrent +(.*)"))
async def torr_search(message):
    await message.edit("`Searching for available Torrents!`")
    input_ = message.pattern_match.group(1)
    max_limit = 10
    query = ""
    for char in input_.split():
        try:
            max_limit = int(char)
        except:
            query = char
    r = requests.get("https://torrent-paradise.ml/api/search?q=" + query)
    try:
        torrents = r.json()
        reply_ = ""
        torrents = sorted(torrents, key=lambda i: i["s"], reverse=True)
        for torrent in torrents[: min(max_limit, len(torrents))]:
            if len(reply_) < 4096 and torrent["s"] > 0:
                try:
                    reply_ = (
                        reply_ + f"\n\n<b>{torrent['text']}</b>\n"
                        f"<b>Size:</b> {humanbytes(torrent['len'])}\n"
                        f"<b>Seeders:</b> {torrent['s']}\n"
                        f"<b>Leechers:</b> {torrent['l']}\n"
                        f"<code>magnet:?xt=urn:btih:{torrent['id']}</code>"
                    )
                except Exception:
                    pass
        if reply_ == "":
            await message.edit(f"No torrents found for {query}!")
        else:
            await message.edit(text=reply_, parse_mode="html")
    except Exception:
        await message.edit("Torrent Search API is Down!\nTry again later")
