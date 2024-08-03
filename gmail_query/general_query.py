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
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import json
from googleapiclient.errors import HttpError
import os
from datetime import datetime
current_date = datetime.now().strftime('%Y%m%d')
folder_name = os.path.join('../db/raw',current_date)
# Create the folder if it does not exist
if not os.path.exists(folder_name):
    os.makedirs(folder_name)


dotenv_path = os.path.join('..', '.env')
load_dotenv(dotenv_path)

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
our_email = os.getenv('gmail_address')
PATH_credentails = os.getenv('gmail_credential')
# %%
def gmail_authenticate():
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
service = gmail_authenticate()
#%%
def list_messages_all(service, user_id='me', label_names=None):
    try:
        label_ids = []
        if label_names:
            if isinstance(label_names, str):
                label_names = [label_names]  # Convert single string to list
            for name in label_names:
                label_id = find_label_id(service, name)
                if label_id:
                    label_ids.append(label_id)
        
        if not label_ids:
            print("No valid labels found. Fetching all messages.")
            request = service.users().messages().list(userId=user_id)
        else:
            request = service.users().messages().list(userId=user_id, labelIds=label_ids)
        
        messages = []
        while request is not None:
            response = request.execute()
            messages.extend(response.get('messages', []))
            request = service.users().messages().list_next(previous_request=request, previous_response=response)
        
        return messages
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None


def find_label_id(service, label_name):
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        for label in labels:
            if label['name'].lower() == label_name.lower():
                return label['id']
        print(f"Label '{label_name}' not found.")
        return None
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def list_messages_limited(service, user_id='me', label_names=None, max_results=20):
    try:
        label_ids = []
        if label_names:
            if isinstance(label_names, str):
                label_names = [label_names]  # Convert single string to list
            for name in label_names:
                label_id = find_label_id(service, name)
                if label_id:
                    label_ids.append(label_id)
        
        if not label_ids:
            print("No valid labels found. Fetching messages without label filter.")
            response = service.users().messages().list(userId=user_id, maxResults=max_results).execute()
        else:
            response = service.users().messages().list(userId=user_id, labelIds=label_ids, maxResults=max_results).execute()
        
        messages = response.get('messages', [])
        return messages
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def get_mime_type_part(parts, mime_type):
    for part in parts:
        if part['mimeType'] == mime_type:
            return part
        if 'parts' in part:
            nested_part = get_mime_type_part(part['parts'], mime_type)
            if nested_part:
                return nested_part
    return None

def decode_body(body_data):
    return base64.urlsafe_b64decode(body_data).decode('utf-8')

def get_message(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
        headers = message['payload']['headers']
        
        # Extracting necessary fields from headers
        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), '')
        sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), '')
        date = next((header['value'] for header in headers if header['name'].lower() == 'date'), '')
        recipients = next((header['value'] for header in headers if header['name'].lower() == 'to'), '').split(',')
        cc = next((header['value'] for header in headers if header['name'].lower() == 'cc'), '').split(',')
        bcc = next((header['value'] for header in headers if header['name'].lower() == 'bcc'), '').split(',')

        # Extract the main email body
        parts = message['payload'].get('parts', [])
        body = ""
        if parts:
            text_part = get_mime_type_part(parts, 'text/plain')
            html_part = get_mime_type_part(parts, 'text/html')
            
            if text_part and 'data' in text_part['body']:
                body = decode_body(text_part['body']['data'])
            elif html_part and 'data' in html_part['body']:
                body = decode_body(html_part['body']['data'])
        else:
            if 'data' in message['payload']['body']:
                body = decode_body(message['payload']['body']['data'])

        # Extract attachments
        attachments = []
        for part in parts:
            if part.get('filename'):
                attachments.append({
                    'filename': part['filename'],
                    'size': int(part['body'].get('size', 0)),
                    'mime_type': part['mimeType']
                })

        msg_dict = {
            "email_id": message['id'],
            "metadata": {
                "subject": subject,
                "sender": sender,
                "date": date,
                "recipients": recipients,
                "cc": cc,
                "bcc": bcc
            },
            "content": {
                "body": body,
                "attachments": attachments
            },
            "custom_fields": {
                "category": None,
                "tags": None,
                "labels": message.get('labelIds', [])
            }
        }
        return msg_dict
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def get_all_emails(service, label_names=None):
    messages = list_messages_all(service, label_names=label_names)
    email_data = []
    if messages:
        total = len(messages)
        for i, msg in enumerate(messages, 1):
            try:
                msg_id = msg['id']
                message_details = get_message(service, 'me', msg_id)
                if message_details:
                    email_data.append(message_details)
                if i % 100 == 0:
                    print(f"Processed {i}/{total} emails")
            except Exception as e:
                print(f"Error processing message {msg['id']}: {e}")
    return email_data

def get_limited_emails(service, label_names=None, max_results=20):
    messages = list_messages_limited(service, label_names=label_names, max_results=max_results)
    email_data = []
    if messages:
        for msg in messages:
            msg_id = msg['id']
            message_details = get_message(service, 'me', msg_id)
            if message_details:
                email_data.append(message_details)
    return email_data


label_system ={
    "personal": "CATEGORY_PERSONAL",
    "social": "CATEGORY_SOCIAL",
    "promotions": "CATEGORY_PROMOTIONS",
    "updates": "CATEGORY_UPDATES",
    "forums": "CATEGORY_FORUMS",
    "inbox": "INBOX",
    "sent": "SENT",
    "trash": "TRASH",
    "spam": "SPAM",
    "draft": "DRAFT",
    "starred": "STARRED",
    "unread": "UNREAD",
    "job_category": "jobs_applica"
}

# Get the list of messages
label_list = ['inbox', 'job_category','social','promotions','updates']
for label in label_list:
    email_data = get_all_emails(service,label_names=label_system[label])
    with open(os.path.join(folder_name,label+'_all.json'), 'w') as f:
        json.dump(email_data, f, indent=2)



# %%
# from googleapiclient.errors import HttpError



# def list_all_labels(service):
#     try:
#         results = service.users().labels().list(userId='me').execute()
#         labels = results.get('labels', [])

#         if not labels:
#             print('No labels found.')
#             return

#         print('Labels:')
#         for label in labels:
#             print(f"Name: {label['name']}")
#             print(f"ID: {label['id']}")
#             print(f"Type: {label['type']}")
#             print(f"Message List Visibility: {label.get('messageListVisibility', 'Not specified')}")
#             print(f"Label List Visibility: {label.get('labelListVisibility', 'Not specified')}")
#             print(f"Total Messages: {label.get('messagesTotal', 'Not available')}")
#             print(f"Unread Messages: {label.get('messagesUnread', 'Not available')}")
#             print('-' * 50)

#     except HttpError as error:
#         print(f'An error occurred: {error}')

# list_all_labels(service)
# %%
