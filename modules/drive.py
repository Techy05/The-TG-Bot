# The below code is based on https://github.com/cyberboysumanjay/Gdrivedownloader/blob/master/gdrive_upload.py
# Licensed under MIT License
# Modified by Priyam Kalra (6/21/2020)
# Rewritten with Drive API v3 by @Techy05
# For The-TG-Bot v3

import os
import time
import asyncio
import heroku3
import requests

from datetime import datetime
from pySmartDL import SmartDL
from mimetypes import guess_type

from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from telethon.errors.rpcerrorlist import MessageNotModifiedError


token_file = ENV.DOWNLOAD_DIRECTORY.rstrip("/") + "/auth_token.txt"
CLIENT_ID = ENV.DRIVE_CLIENT_ID
CLIENT_SECRET = ENV.DRIVE_CLIENT_SECRET
OAUTH_SCOPE = ["https://www.googleapis.com/auth/drive"]
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
PARENT_ID = ENV.DRIVE_PARENT_ID
INDEX_URL = ENV.INDEX_URL


# Initialise credentials on boot
if ENV.DRIVE_AUTH_TOKEN_DATA:
    if not os.path.exists(token_file):
        with open(token_file, "w") as f:
            f.write(ENV.DRIVE_AUTH_TOKEN_DATA)
    credentials = Storage(token_file).get()
else:
    credentials = None


@client.on(events(pattern="drive ?(.*)", forwards=False))
async def handler(event):
    if CLIENT_ID is None or CLIENT_SECRET is None:
        return await event.edit("This module requires credentials from https://da.gd/so63O. Aborting!\nVisit https://da.gd/drive for more info.")
    if ENV.LOGGER_GROUP is None:
        return await event.edit("Please set the required environment variable `LOGGER_GROUP` for this plugin to work.")
    if credentials is None:
        await event.edit("Please goto your `LOGGER GROUP` and complete the setup")
        return await new_token(token_file)

    input_str = event.pattern_match.group(1).split()
    reply = await event.get_reply_message()
    t_start = datetime.now()

    # Downloading the file on server
    file_path, directory = None, None
    if reply:
        if reply.media and "WebPage" not in str(reply.media):
            await event.edit("Starting download..")
            try:
                start = datetime.now()
                c_time = time.time()
                downloaded_file_name = await client.download_media(
                    reply.media,
                    ENV.DOWNLOAD_DIRECTORY,
                    progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                        progress(d, t, event, c_time, "**Downloading**\n")
                    )
                )
            except Exception as e:
                return await event.edit(str(e))
            else:
                end = datetime.now()
                ms = (end - start).seconds
                file_path = downloaded_file_name
                await event.edit(f"Downloaded file to `{file_path}` in {ms} seconds.")
                await asyncio.sleep(2)
        elif "http" in reply.message:
            url = [term.strip() for term in reply.message.split() if term.lower().startswith("http")][0]
            await event.edit("`Starting download`")
            fpath = await download_url(event, url)
            if fpath is None:
                return False
            else:
                file_path = fpath
            await asyncio.sleep(2)
        else:
            await event.edit("`Nothing to download in replied message`")
    elif input_str:
        path = input_str[0]
        if os.path.isfile(path):
            file_path = path
        elif os.path.isdir(path):
            directory = path
        elif "http" in input_str[0]:
            url = input_str[0]
            await event.edit("`Starting download`")
            fpath = await download_url(event, url)
            if fpath is None:
                return False
            else:
                file_path = fpath
            await asyncio.sleep(2)
        else:
            return await event.edit("404: File not found!")
    else:
        return False

    drive_service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    if "shared" in input_str:
        parent = shared_drive(drive_service)
        if parent is None:
            return await event.edit("No shared drive found!\n`Aborting..`")
    elif len(input_str) == 1 and "http" not in str(input_str):  # workaround 
        folder = input_str[0].split("/")[-1]
        parent = find_folder(drive_service, folder)
    elif len(input_str) > 1:
        folder = input_str[-1].split("/")[-1]
        parent = find_folder(drive_service, folder)
    elif PARENT_ID:
        parent = {"name": "drive", "id": PARENT_ID}
    else:
        parent = find_folder(drive_service, "The-TG-Bot")
            
    # Uploading
    if file_path:
        file_name, mime_type = file_info(file_path)
        try:
            await event.edit(f"Uploading to GDrive\nFile Name: `{file_name}`")
            drive_link = await upload_file(drive_service, file_path, file_name, mime_type, parent.get('id'), event)
            t_end = datetime.now()
            await event.edit(f"File sucessfully uploaded to {parent.get('name')} in {(t_end - t_start).seconds} seconds.\n\n{drive_link}", parse_mode="html")
        except Exception as e:
            await event.edit(f"**Oh snap looks like something went wrong:**\n\n`{e}`")
    elif directory:
        batch = []
        size = 0
        await event.edit("`Preparing a list of files..`")
        for dir, subdir, files in os.walk(directory):
            for file in files:
                batch.append(os.path.join(dir, file))
                size += os.path.getsize(os.path.join(dir, file))
        await event.edit(f"Uploading directory [{humanbytes(size)}]\n\nTotal files: {len(batch)}")
        await asyncio.sleep(2)
        uploaded = 0
        error = 0
        for file_path in sorted(batch):
            file_name, mime_type = file_info(file_path)
            try:
                drive_link = await upload_file(drive_service, file_path, file_name, mime_type, parent.get('id'), event)
                await event.edit(f"Uploading directory [{humanbytes(size)}]\n\n`Total files: {len(batch)}\nFiles uploaded: {uploaded}`\n\nUploading: {file_name}")
                os.remove(file_path)
                uploaded += 1           
            except Exception as e:
                error += 1
                with open("error_log.txt", "a") as er:
                    er.write(f"\n\n\n<< {str(error)} >>\n{str(e)}")
            await asyncio.sleep(1 if size < 100*1024*1024 else 5)
        t_end = datetime.now()
        file = "error_log.txt" if error > 0 else None
        await event.reply(
            f"Uploaded directory **{directory}** to drive in {(t_end - t_start).seconds} seconds\n" +
            f"\n`Files uploaded: {uploaded}\nErrors: {error}`\n" +
            f"\n[Drive Link](https://drive.google.com/drive/u/0/folders/{parent.get('id')})" +
            f" | [Index Link]({INDEX_URL}/{directory.split('/')[-1]})" if PARENT_ID and INDEX_URL else "" +
            f"  [`{humanbytes(size)}`]",
            file=file,
            silent=True)
        await event.delete()
    else:
        await event.edit("404: File not found.")


@client.on(events(pattern="copy +(.*)", forwards=False))
async def copy(event):
    if CLIENT_ID is None or CLIENT_SECRET is None:
        return await event.edit("This module requires credentials from https://da.gd/so63O. Aborting!\nVisit https://da.gd/drive for more info.")
    if ENV.LOGGER_GROUP is None:
        return await event.edit("Please set the required environment variable `LOGGER_GROUP` for this plugin to work.")
    if credentials is None:
        await event.edit("Please goto your `LOGGER GROUP` and complete the setup")
        return await new_token(token_file)
    
    input_str = event.pattern_match.group(1)
    if not "drive.google.com" in input_str:
        return await event.edit("`Provide a google drive link`")
    for term in input_str.split()[0].split("/"):
        if len(term) > 25:
            file_id = term.replace("uc?id=", "").replace("&export=download", "")
    
    drive_service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    if "shared" in input_str:
        parent = shared_drive(drive_service)
        if parent is None:
            return await event.edit("No shared drive found!\n`Aborting..`")
    elif len(input_str) == 1 and "http" not in str(input_str):  # workaround 
        folder = input_str[0].split("/")[-1]
        parent = find_folder(drive_service, folder)
    elif len(input_str) > 1:
        folder = input_str[-1].split("/")[-1]
        parent = find_folder(drive_service, folder)
    elif PARENT_ID:
        parent = {"name": "drive", "id": PARENT_ID}
    else:
        parent = find_folder(drive_service, "The-TG-Bot")
    try:
        msg = copy_file(event, drive_service, file_id, parent.get('id'))
        await event.edit(f"File successfully copied to {parent.get('name')}\n\n{msg}", parse_mode="html")
    except Exception as e:
        await event.edit(f"**Looks like something went wrong:**\n\n`{str(e)}`")


def file_info(file_path):
    mime_type = guess_type(file_path)[0]
    mime_type = mime_type if mime_type else "text/plain"
    file_name = file_path.split("/")[-1]
    return file_name, mime_type


async def upload_file(service, file_path, file_name, mime_type, parent, event):
    file_metadata = {
        "name": file_name,
        "description": "Uploaded using The-TG-Bot",
        "mimeType": mime_type,
        "parents": [parent]
    }
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    permissions = {
        "role": "reader",
        "type": "anyone",
        "allowFileDiscovery": True,
        "permissionDetails[].role": "reader"
    }
    
    file = service.files().create(body=file_metadata, 
                                  media_body=media,
                                  supportsAllDrives=True,
                                  fields='id, name, webContentLink, size').execute()
    file_id = file.get('id')
    try: service.permissions().create(fileId=file_id, supportsAllDrives=True, body=permissions).execute()
    except: pass
    download_url = file.get('webContentLink')
    size = file.get('size')
    msg = f"<strong>Download link:</strong>\n<a href=\"{download_url}\">{file.get('name')}</a>  [<code>{humanbytes(int(size))}</code>]"
    if INDEX_URL and parent == PARENT_ID:
        index_link = INDEX_URL + "/" + file.get('name')
        msg += f"  |  <a href=\"{index_link}\">Index link</a>"
    return msg


def copy_file(event, service, file_id, parent):
    file_metadata = {
        "parents": [parent]
    }
    permissions = {
        "role": "reader",
        "type": "anyone",
        "allowFileDiscovery": True,
        "permissionDetails[].role": "reader"
    }
    file = service.files().copy(fileId=file_id, body=file_metadata, 
                                supportsAllDrives=True,
                                fields='id, name, webContentLink, size').execute()
    service.permissions().create(fileId=file.get('id'), supportsAllDrives=True, body=permissions).execute()
    download_url = file.get('webContentLink')
    name = file.get('name')
    size = int(file.get('size'))
    msg = f"<strong>Download link:</strong>\n<a href=\"{download_url}\">{name}</a>  [<code>{humanbytes(size)}</code>]"
    if INDEX_URL and parent == PARENT_ID:
        index_link = INDEX_URL + "/" + name
        msg += f"  |  <a href=\"{index_link}\">Index link</a>"
    return msg


def shared_drive(service):
    response = service.drives().list(fields='drives(id, name)').execute()
    drives = response.get('drives', [])
    if drives: 
        return drives[0]  # Use the first drive
    else: 
        return None
        

def find_folder(service, folder_name):
    response = service.files().list(q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'",
                                    supportsAllDrives=True,
                                    fields='files(id, name)',
                                    ).execute()
    if response.get("files"):
        parent_id = response.get('files')[0].get('id')
    else:
        parent_id = create_folder(service, folder_name)
    parent = {'name': 'My Drive', 'id': parent_id}
    return parent


def create_folder(service, folder_name):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if PARENT_ID:
        file_metadata.update({'parents': [PARENT_ID]})
    permissions = {
        "role": "reader", 
        "type": "anyone", 
        "allowFileDiscovery": True,
        "permissionDetails[].role": "reader"
    }
    folder = service.files().create(body=file_metadata, supportsAllDrives=True, fields='id').execute()
    parent_id = folder.get('id')
    service.permissions().create(fileId=parent_id, body=permissions, supportsAllDrives=True).execute()
    return parent_id
    

async def download_url(event, url):
    try:
        r = requests.get(url, stream=True, timeout=10)
        url = r.url
    except:
        await event.edit("`Invalid URL!`")
        return None
    start = datetime.now()
    download_dir = ENV.DOWNLOAD_DIRECTORY
    if "github" in url: # Workaround
        fname = r.headers["content-disposition"].split("name=")[-1]
        download_dir = os.path.join(download_dir, fname)
    Download = SmartDL(url, download_dir, threads=1, progress_bar=False)
    fpath = Download.get_dest()
    fname = os.path.basename(fpath)
    try: 
        bsize = int(r.headers['content-length'])
    except: 
        bsize = 0
    size = humanbytes(bsize) if bsize else "?"
    interval = 1.5 if bsize < 400*1024*1024 else 5
    status = f"**Downloading..**\n\n**File Name:** `{fname}`\n"
    await event.edit(status + f"**Size:** `{size}`")
    Download.start(blocking=False)
    while not Download.isFinished():
        progress = humanbytes(Download.get_dl_size()) if Download.get_dl_size() else "0.00 MiB"
        percentage = Download.get_progress() * 100
        new_msg = status + f"**Downloaded:**\n`{progress}`  of  `{size}`  [{round(percentage, 1)}%]"
        try:
            await event.edit(new_msg)
        except MessageNotModifiedError:
            continue
        await asyncio.sleep(interval)
    end = datetime.now()
    if Download.isSuccessful():
        await event.edit(f"**Downloaded {size} file in {(end - start).seconds} seconds.**\n\n`{fpath}`")
        return fpath
    else:
        await event.edit(f"`Failed to download {fname} [{size}]`!")
        return None
            

async def new_token(token_file):
    flow = OAuth2WebServerFlow(
        CLIENT_ID,
        CLIENT_SECRET,
        OAUTH_SCOPE,
        redirect_uri=REDIRECT_URI
    )
    authorize_url = flow.step1_get_authorize_url()
    async with client.conversation(ENV.LOGGER_GROUP) as conv:
        await conv.send_message(f"Go to the following link in your browser and reply the code:\n\n{authorize_url}")
        response = conv.wait_event(events(func=lambda e: e.chat_id == ENV.LOGGER_GROUP))
        msg = await response
    code = msg.message.message.strip()
    credentials = flow.step2_exchange(code)
    
    # Save the credentials
    Storage(token_file).put(credentials)
    if ENV.HEROKU_API_KEY and ENV.TG_APP_NAME:
        env = heroku3.from_key(ENV.HEROKU_API_KEY).apps()[ENV.TG_APP_NAME].config()
        with open(token_file, "r") as t:
            token_str = t.read()
        env.update({"DRIVE_AUTH_TOKEN_DATA": token_str})
        await client.send_message(ENV.LOGGER_GROUP, "`Drive credentials have been automatically saved.\nThe-TG-Bot will now restart..`")
    else:
        await client.send_message(
            ENV.LOGGER_GROUP, 
            f"Run the below command:\n`$cat {token_file}`" + 
            "\n\nCreate a new var `DRIVE_AUTH_TOKEN_DATA` and paste the output " + 
            "of command as its value.\nDon't share the output with anyone!")


ENV.HELPER.update({
    "drive": "\
`.drive [reply -> media/url] [folder]`\
\nUsage: Upload a file from telegram to your google drive.\
\n\n`.drive [path/url] [folder]`\
\nUsage: Downloads a file from url to storage and uploads it to drive.\
\n\n`.copy [drive url]`\
\nUsagd: Makes a copy of a file to your drive (or shared drive).\
\n\nOptional argument: `shared` to upload the file in shared drive.\
\n\n\nYou need `DRIVE_CLIENT_ID` and `DRIVE_CLIENT_SECRET` env variables for this module to work.\
\nGet the client id and secret from https://console.developers.google.com/\
\nVisit https://da.gd/drive for more info.\
"
})
