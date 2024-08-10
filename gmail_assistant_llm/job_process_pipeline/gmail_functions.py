import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from base64 import urlsafe_b64decode, urlsafe_b64encode
import base64
from googleapiclient.errors import HttpError
from gmail_assistant_llm.util import *
import os


class Gmail_Authenticate:
    def __init__(self):
        self.SCOPES = ['https://mail.google.com/']
        self.target_email = os.getenv('gmail_address')
        self.PATH_credentails = os.getenv('gmail_credentials')
        self.service = self.gmail_authenticate()

    def gmail_authenticate(self):
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
                flow = InstalledAppFlow.from_client_secrets_file(self.PATH_credentails, self.SCOPES)
                creds = flow.run_local_server(port=0)
            # save the credentials for the next run
            with open(os.getenv('gmail_token'), "wb") as token:
                pickle.dump(creds, token)
        return build('gmail', 'v1', credentials=creds)



class Gmail_Functions:
    def __init__(self,target_label_list,service):
        '''
        target label should be a list
        '''
        self.service = service
        self.target_label_list = target_label_list
        
        # initialze gmail label system
        self.label_system ={
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
        "job_category": "jobs_applica",
        }

    def find_label_id(self,label_name):
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            for label in labels:
                if label['name'].lower() == label_name.lower():
                    return label['id']
            print(f"Label '{label_name}' not found.")
            return None
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

    def list_messages_all(self,user_id='me',label_names=None):

        try:
            label_ids = []
            if label_names:
                if isinstance(label_names, str):
                    label_names = [label_names]  # Convert single string to list
                for name in label_names:
                    label_id = self.find_label_id(name)
                    if label_id:
                        label_ids.append(label_id)
            
            if not label_ids:
                print("No valid labels found. Fetching all messages.")
                request = self.service.users().messages().list(userId=user_id)
            else:
                request = self.service.users().messages().list(userId=user_id, labelIds=label_ids)
            
            messages = []
            while request is not None:
                response = request.execute()
                messages.extend(response.get('messages', []))
                request = self.service.users().messages().list_next(previous_request=request, previous_response=response)
            
            return messages
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def get_mime_type_part(self,parts,mime_type):
        for part in parts:
            if part['mimeType'] == mime_type:
                return part
            if 'parts' in part:
                nested_part = self.get_mime_type_part(part['parts'], mime_type)
                if nested_part:
                    return nested_part
        return None

    def decode_body(self,body_data):
        return base64.urlsafe_b64decode(body_data).decode('utf-8')

    def get_message(self, user_id, msg_id):

        try:
            message = self.service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
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
                text_part = self.get_mime_type_part(parts, 'text/plain')
                html_part = self.get_mime_type_part(parts, 'text/html')
                
                if text_part and 'data' in text_part['body']:
                    body = self.decode_body(text_part['body']['data'])
                elif html_part and 'data' in html_part['body']:
                    body = self.decode_body(html_part['body']['data'])
            else:
                if 'data' in message['payload']['body']:
                    body = self.decode_body(message['payload']['body']['data'])

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

    
    def get_all_emails_per_label(self,label_names=None):
        messages = self.list_messages_all(label_names=label_names)
        email_data = []
        if messages:
            total = len(messages)
            for i, msg in enumerate(messages, 1):
                try:
                    msg_id = msg['id']
                    message_details = self.get_message('me', msg_id)
                    if message_details:
                        email_data.append(message_details)
                    if i % 100 == 0:
                        print(f"Processed {i}/{total} emails")
                except Exception as e:
                    print(f"Error processing message {msg['id']}: {e}")
        return email_data
    
    def get_all_emails_all_labels(self):
        all_emails = []
        for label in self.target_label_list:
            email_data = self.get_all_emails_per_label(label_names=self.label_system[label])
            all_emails.extend(email_data)
        return all_emails

