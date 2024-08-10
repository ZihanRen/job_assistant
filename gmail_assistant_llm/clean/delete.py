#%%
import os
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type
import os
import base64
from gmail_assistant_llm import init_env
from dotenv import load_dotenv
import json


def get_path(env_var):
    path = os.path.join(init_env.dotenv_path,env_var)
    return path
def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

def gmail_authenticate(PATH_credentails, SCOPES):
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists(os.getenv('gmail_token')):
        with open(os.getenv('gmail_token'), "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(PATH_credentails, SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open(os.getenv('gmail_token'), "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# get the Gmail API service
# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
our_email = os.getenv('gmail_address')
PATH_credentails = os.getenv('gmail_credential')
service = gmail_authenticate(PATH_credentails, SCOPES)

all_emails = read_json(
    get_path(os.getenv('ALL_EMAILS'))
    )

gmail_query_state = read_json(
    get_path(os.getenv('QUERY_GMAIL_STATE'))
    )



#%%
def delete_emails(service, email_ids):
    """Delete emails by IDs"""
    for email_id in email_ids:
        service.users().messages().delete(userId='me', id=email_id).execute()

delete_ids = []
for key in gmail_query_state.keys():
    if gmail_query_state[key]['llm_query_status']:
        delete_ids.append(key)

delete_emails(service, delete_ids)
