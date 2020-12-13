# This Source Code Form is subject to the terms of the GNU
# General Public License, v.3.0. If a copy of the GPL was not distributed with this
# file, You can obtain one at https://www.gnu.org/licenses/gpl-3.0.en.html
# For The-TG-Bot-3.0

import os
import time
import aria2p
import asyncio
import subprocess
from datetime import datetime
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from telethon.tl.types import DocumentAttributeVideo, DocumentAttributeAudio


cmd = "aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port 6800  --max-connection-per-server=10 --rpc-max-request-size=1024M --seed-time=0.01 --min-split-size=10M --follow-torrent=mem --split=10 --daemon=true"
aria2_is_running = os.system(cmd)
aria2 = aria2p.API(aria2p.Client(
    host="http://localhost", port=6800, secret=""))
EDIT_SLEEP_TIME_OUT = 10
thumb_image_path = ENV.DOWNLOAD_DIRECTORY + "/thumb_image.jpg"


@client.on(events(pattern="leech ?(.*)"))
async def magnet_download(event):
    if event.fwd_from:
        return
    var = event.pattern_match.group(1)
    if not var:
        rep = await event.get_reply_message()
        var = rep.text
    uris = [var]
    # Add URL Into Queue
    try:
        download = aria2.add_uris(uris, options=None, position=None)
    except Exception as e:
        await log(str(e))
        return await event.delete()

    gid = download.gid
    complete = None
    await progress_status(gid=gid, event=event, previous=None)
    file = aria2.get_download(gid)
    if file.followed_by_ids:
        new_gid = await check_metadata(gid)
        await progress_status(gid=new_gid, event=event, previous=None)
    while complete != True:
        file = aria2.get_download(gid)
        complete = file.is_complete
        try:
            msg = "**Leeching:** "+str(file.name) + "\n\n**Speed:** " + str(file.download_speed_string())+"\n**Progress:** "+str(
                file.progress_string())+"\n**Total Size:** "+str(file.total_length_string())+"\n**ETA:**  "+str(file.eta_string())+"\n\n"
            await event.edit(msg)
            await asyncio.sleep(10)
        except Exception as e:
            await log(str(e))
            pass

    await event.edit(f"`{file.name}` leeched successfully!")


def get_video_thumb(file, output=None, width=90):
    metadata = extractMetadata(createParser(file))
    p = subprocess.Popen([
        'ffmpeg', '-i', file,
        '-ss', str(int((0, metadata.get('duration').seconds)
                       [metadata.has('duration')] / 2)),
        '-filter:v', 'scale={}:-1'.format(width),
        '-vframes', '1',
        output,
    ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if not p.returncode and os.path.lexists(file):
        return output


def get_lst_of_files(input_directory, output_lst):
    filesinfolder = os.listdir(input_directory)
    for file_name in filesinfolder:
        current_file_name = os.path.join(input_directory, file_name)
        if os.path.isdir(current_file_name):
            return get_lst_of_files(current_file_name, output_lst)
        output_lst.append(current_file_name)
    return output_lst


async def log(text):
    LOGGER = ENV.LOGGER_GROUP
    await client.send_message(LOGGER, text)


async def check_metadata(gid):
    file = aria2.get_download(gid)
    new_gid = file.followed_by_ids[0]
    logger.info("Changing GID "+gid+" to "+new_gid)
    return new_gid


async def progress_status(gid, event, previous):
    global req_file
    try:
        file = aria2.get_download(gid)
        req_file = str(file.name)
        if not file.is_complete:
            if not file.error_message:
                msg = "**Leeching**: `"+str(file.name) + "`\n**Speed**: " + str(file.download_speed_string())+"\n**Progress**: "+str(file.progress_string(
                ))+"\n**Total Size**: "+str(file.total_length_string())+"\n**Status**: "+str(file.status)+"\n**ETA**:  "+str(file.eta_string())+"\n\n"
                if previous != msg:
                    await event.edit(msg)
                    previous = msg
            else:
                logger.info(str(file.error_message))
                await log("Error : `{}`".format(str(file.error_message)))
                return
            await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
            await progress_status(gid, event, previous)
        else:
            await event.edit(f"`{file.name}` leeched successfully!")
            return
    except Exception as e:
        if " not found" in str(e) or "'file'" in str(e):
            await log(str(e))
            return await event.delete()
        elif " depth exceeded" in str(e):
            file.remove(force=True)
            await log(str(e))
        else:
            await log(str(e))
            return await event.delete()

ENV.HELPER.update({
    "leech": "\
`.leech <magnet-link> (or as a reply to a magnet link)`\
\nUsage: Downloads the torrent to the local machine.\
"
})
