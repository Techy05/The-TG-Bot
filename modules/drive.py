# The below code is based on https://github.com/cyberboysumanjay/Gdrivedownloader/blob/master/gdrive_upload.py
# Licensed under MIT License
# Modified by Priyam Kalra (6/21/2020)
# Rewritten with Drive API v3 by @Techy05
# For The-TG-Bot v3

import os
import math
import time
import asyncio
import requests

from shutil import copyfileobj
from datetime import datetime
from mimetypes import guess_type

from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from apiclient.errors import ResumableUploadError


token_file = ENV.DOWNLOAD_DIRECTORY.rstrip("/") + "/auth_token.txt"
CLIENT_ID = ENV.DRIVE_CLIENT_ID
CLIENT_SECRET = ENV.DRIVE_CLIENT_SECRET
OAUTH_SCOPE = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive.readonly"]
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


@client.on(events(pattern="drive ?(.*)"))
async def handler(event):
    if event.fwd_from:
        return
    if CLIENT_ID is None or CLIENT_SECRET is None:
        await event.edit("This module requires credentials from https://da.gd/so63O. Aborting!\nVisit da.gd/drive for more info.")
        return
    if ENV.LOGGER_GROUP is None:
        await event.edit("Please set the required environment variable `LOGGER_GROUP` for this plugin to work.")
        return

    # Initialise credentials
    if ENV.DRIVE_AUTH_TOKEN_DATA is not None:
        if not os.path.exists(token_file):
            with open(token_file, "w") as f:
                f.write(ENV.DRIVE_AUTH_TOKEN_DATA)
        credentials = Storage(token_file).get()
    else:
        await event.edit("Please goto your `LOGGER GROUP` and complete the setup")
        credentials = await new_token(token_file)
    
    input_str = event.pattern_match.group(1).split('-shared')[0].strip()
    reply = await event.get_reply_message()
    use_shared = True if '-shared' in event.text else False
    t_start = datetime.now()
    
    # Getting the file ready to upload
    file_path = None
    if reply:
        if reply.media is not None and "WebPageEmpty" not in str(reply.media):
            await event.edit("Starting download..")
            try:
                start = datetime.now()
                c_time = time.time()
                downloaded_file_name = await client.download_media(
                    reply,
                    ENV.DOWNLOAD_DIRECTORY,
                    progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                        progress(d, t, event, c_time, "**Downloading to Local**\n")
                    )
                )
            except Exception as e:
                await event.edit(str(e))
                return False
            else:
                end = datetime.now()
                ms = (end - start).seconds
                file_path = downloaded_file_name
                await event.edit(f"Downloaded file to `{file_path}` in {ms} seconds.")
                await asyncio.sleep(2)
        elif (reply.media is None or "WebPageEmpty" in str(reply.media)) and "http" in reply.message:
            for term in reply.message.split():
                if term.lower().startswith("http"):
                    url = term
            start = datetime.now()
            output = await download_url(event, url)
            if output is None:
                return
            else:
                file_path = output
            end = datetime.now()
            await event.edit(f"Downloaded file to `{output}` in {(end - start).seconds} seconds.")
            await asyncio.sleep(2)
        else:
            await event.edit("`Like I care.`")
            return False
    elif input_str:
        if os.path.exists(input_str):
            file_path = input_str
        elif "http" in input_str:
            for term in input_str.split():
                if term.lower().startswith("http"):
                    url = term
            await event.edit("`Getting url info..`")
            start = datetime.now()
            output = await download_url(event, url)
            if output is None:
                return
            else:
                file_path = output
            end = datetime.now()
            await event.edit(f"Downloaded file to `{output}` in {(end - start).seconds} seconds.")
            await asyncio.sleep(2)
        else:
            await event.edit("404: File not found!")
            return False
    
    # Uploading the file to drive
    if file_path:
        file_name, mime_type = file_info(file_path)
        drive_service = build("drive", "v3", credentials=credentials, cache_discovery=False)
        if use_shared is True:
            parent = shared_drive(drive_service)
            if parent is None:
                return await event.edit("No shared drive found!\n`Aborting..`")
        else:
            parent = find_folder(drive_service, "The-TG-Bot")
        try:
            gdrive_link = await upload_file(drive_service, file_path, file_name, mime_type, parent.get('id'), event)
            t_end = datetime.now()
            await event.edit(f"File sucessfully uploaded to {parent.get('name')} in {(t_end - t_start).seconds} seconds.\n\n**Download link:**\n[{file_name}]({gdrive_link})")
        except Exception as e:
            await event.edit(f"Oh snap looks like something went wrong:\n{e}")
    else:
        await event.edit("404: File not found.")


# Get mime type and name of given file
def file_info(file_path):
    mime_type = guess_type(file_path)[0]
    mime_type = mime_type if mime_type else "text/plain"
    file_name = file_path.split("/")[-1]
    return file_name, mime_type


async def download_url(event, url):
    try: 
        r = requests.get(url, stream=True, timeout=20)
    except: 
        await event.edit("`Invalid URL`")
        return None
    else:
        try:
            fname = r.url.split("/")[-1].split("=")[-1]
            size = float(r.headers["content-length"]) / 1024 / 1024
            # Limit max decimal places to 3
            size = str(size)[:5].strip(".") if len(str(size)) > 4 else str(size) 
        except:
            fname = "unknown_file." + fname.split('.')[-1].split('/')[0]
            size = "?"
            await event.edit("`WARNING: This file may not download properly`")
            await asyncio.sleep(2)
        
        fpath = ENV.DOWNLOAD_DIRECTORY.rstrip("/") + "/" + fname
        await event.edit(f"Downloading `{fname}` [{size} MB] to local..")
        try:
            with open(fpath, "wb") as f:
                copyfileobj(r.raw, f)
        except Exception as e:
            await event.edit(f"Whoops! Error:\n\n {str(e)}")
            return None
        else:
            return fpath
            

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
    await event.edit(f"Uploading to GDrive\nFile Name: `{file_name}`")
    
    file = service.files().create(body=file_metadata, 
                                  media_body=media,
                                  supportsAllDrives=True,
                                  fields='id').execute()
    
    file_id = file.get('id')
    service.permissions().create(fileId=file_id, supportsAllDrives=True, body=permissions).execute()
    file = service.files().get(fileId=file_id, supportsAllDrives=True, fields='webContentLink').execute()
    download_url = file.get('webContentLink')
    return download_url


def shared_drive(service):
    response = service.drives().list(fields='drives(id, name)').execute()
    drives = response.get('drives', [])
    if drives: 
        return drives[0]  # Return the most recent drive
    else: 
        return None
        

def find_folder(service, folder_name):
    response = service.files().list(q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'",
                                    supportsAllDrives=True,
                                    fields='files(id, name)',
                                    ).execute()
    if response:
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
    permissions = {
        "role": "reader", 
        "type": "anyone", 
        "allowFileDiscovery": True,
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    parent_id = folder.get('id')
    service.permissions().create(fileId=parent_id, body=permissions).execute()
    return parent_id
    

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
        response = conv.wait_event(events())
        msg = await response
    code = msg.message.message.strip()
    credentials = flow.step2_exchange(code)
    
    # Save the credentials
    Storage(token_file).put(credentials)
    await client.send_message(
        ENV.LOGGER_GROUP, 
        f"Run the below command:\n`.shell cat {token_file}`" + 
        "\n\nCreate a new var `DRIVE_AUTH_TOKEN_DATA` and paste the output " + 
        "of command as its value.\nPlease don't share the output with anyone",
    )
    return credentials



ENV.HELPER.update({
    "drive": "\
`.drive (reply to a file or a message containing download link)`\
\nUsage: Upload a file on telegram to your google drive.\
\n\n`.drive (file location/download link)`\
\nUsage: Downloads a file from url to storage and uploads it to drive.\
\n\nOptional argument: `-shared` to upload the file in shared drive.\
\nExample:  `.drive <input/reply> -shared`\
\n\n\nYou need `DRIVE_CLIENT_ID` and `DRIVE_CLIENT_SECRET` env variables for this to work.\
\nGet the client id and secret from https://console.developers.google.com/\
\nVisit https://da.gd/drive for more info.\
"
})
