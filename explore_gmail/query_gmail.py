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

dotenv_path = os.path.join('..', '.env')
load_dotenv(dotenv_path)

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
our_email = 'zihanren.ds@gmail.com'
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
def list_messages(service, user_id='me', label_ids=['INBOX'], max_results=20):
    try:
        response = service.users().messages().list(userId=user_id, labelIds=label_ids, maxResults=max_results).execute()
        messages = response.get('messages', [])
        return messages
    except Exception as error:
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

def extract_job_details_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    job_details = {}

    # Extract recipient name
    header = soup.find('h1', class_='es-m-txt-c')
    if header:
        name_text = header.get_text(strip=True)
        name = name_text.split(',')[-1].strip()
        job_details['recipient_name'] = name

    # Extract job title and company
    job_info = soup.find('p', style=lambda value: value and 'font-size:16px' in value)
    if job_info:
        strong_tags = job_info.find_all('strong')
        if len(strong_tags) >= 2:
            job_details['job_title'] = strong_tags[0].get_text(strip=True)
            job_details['company'] = strong_tags[1].get_text(strip=True)

    # Extract location
    location = job_info.find('em') if job_info else None
    if location:
        job_details['location'] = location.get_text(strip=True)

    # Extract company description
    company_desc = soup.find('p', style=lambda value: value and 'font-size:16px' in value and 'color:#000000' in value)
    if company_desc:
        job_details['company_description'] = company_desc.get_text(strip=True)

    # Extract job link
    job_link = soup.find('a', class_='es-button es-button-4')
    if job_link and 'href' in job_link.attrs:
        job_details['job_link'] = job_link['href']

    # Extract email preferences
    preferences = soup.find_all('a', style=lambda value: value and 'font-size:14px' in value and 'color:#000000' in value)
    if preferences:
        job_details['email_preferences'] = [pref.get_text(strip=True) for pref in preferences]

    # Extract footer information
    footer = soup.find('p', style=lambda value: value and 'font-size:13px' in value)
    if footer:
        job_details['company_info'] = footer.get_text(strip=True)

    return job_details

def get_message(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
        headers = message['payload']['headers']
        
        # Extracting necessary fields from headers
        subject = next(header['value'] for header in headers if header['name'] == 'Subject')
        sender = next(header['value'] for header in headers if header['name'] == 'From')
        date = next(header['value'] for header in headers if header['name'] == 'Date')

        # Extract the main email body
        parts = message['payload'].get('parts', [])
        body = ""
        if parts:
            # Try to get text/plain or text/html parts
            text_part = get_mime_type_part(parts, 'text/plain')
            html_part = get_mime_type_part(parts, 'text/html')
            
            if text_part and 'data' in text_part['body']:
                body = decode_body(text_part['body']['data'])
            elif html_part and 'data' in html_part['body']:
                html_body = decode_body(html_part['body']['data'])
                job_details = extract_job_details_from_html(html_body)
                body = f"Recipient: {job_details.get('recipient_name', '')}\n"
                body += f"Job Title: {job_details.get('job_title', '')}\n"
                body += f"Company: {job_details.get('company', '')}\n"
                body += f"Location: {job_details.get('location', '')}\n"
                body += f"Company Description: {job_details.get('company_description', '')}\n"
                body += f"Job Link: {job_details.get('job_link', '')}\n"
                body += f"Email Preferences: {', '.join(job_details.get('email_preferences', []))}\n"
                body += f"Company Info: {job_details.get('company_info', '')}"
        else:
            if 'data' in message['payload']['body']:
                body = decode_body(message['payload']['body']['data'])

        msg_dict = {
            'id': message['id'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body,
        }
        return msg_dict
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

# Get the Gmail API service
service = gmail_authenticate()

# Get the list of messages
messages = list_messages(service)

# Retrieve each message's metadata and main contents
email_data = []
for msg in messages:
    msg_id = msg['id']
    message_details = get_message(service, 'me', msg_id)
    if message_details:
        email_data.append(message_details)
# %%
for i in range(20):
    print('---'*10)
    print(i)
    print(email_data[i]['sender'])
# %%
