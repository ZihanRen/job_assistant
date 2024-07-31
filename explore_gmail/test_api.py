# https://thepythoncode.com/article/use-gmail-api-in-python

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

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
our_email = 'rtopaz2020@gmail.com'
PATH_credentails = '/home/topaz/repo/assistant_job/credentials.json'
# %%
def gmail_authenticate():
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(PATH_credentails, SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# get the Gmail API service
service = gmail_authenticate()
# %%
# Adds the attachment with the given filename to the given message
def add_attachment(message, filename):
    content_type, encoding = guess_mime_type(filename)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        fp = open(filename, 'rb')
        msg = MIMEText(fp.read().decode(), _subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(filename, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(filename, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        fp = open(filename, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()
    filename = os.path.basename(filename)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)

def build_message(destination, obj, body, attachments=[]):
    if not attachments: # no attachments given
        message = MIMEText(body)
        message['to'] = destination
        message['from'] = our_email
        message['subject'] = obj
    else:
        message = MIMEMultipart()
        message['to'] = destination
        message['from'] = our_email
        message['subject'] = obj
        message.attach(MIMEText(body))
        for filename in attachments:
            add_attachment(message, filename)
    return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}

def send_message(service, destination, obj, body, attachments=[]):
    return service.users().messages().send(
      userId="me",
      body=build_message(destination, obj, body, attachments)
    ).execute()




# for i in text_chunk:
#     send_message(service, "@gmail.com", i, 
#                 "meow")


# %%
# def search_messages(service, query):
#     result = service.users().messages().list(userId='me',q=query).execute()
#     messages = [ ]
#     if 'messages' in result:
#         messages.extend(result['messages'])
#     while 'nextPageToken' in result:
#         page_token = result['nextPageToken']
#         result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
#         if 'messages' in result:
#             messages.extend(result['messages'])
#     return messages


# def get_size_format(b, factor=1024, suffix="B"):
#     """
#     Scale bytes to its proper byte format
#     e.g:
#         1253656 => '1.20MB'
#         1253656678 => '1.17GB'
#     """
#     for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
#         if b < factor:
#             return f"{b:.2f}{unit}{suffix}"
#         b /= factor
#     return f"{b:.2f}Y{suffix}"


# def clean(text):
#     # clean text for creating a folder
#     return "".join(c if c.isalnum() else "_" for c in text)

# def parse_parts(service, parts, folder_name, message):
#     """
#     Utility function that parses the content of an email partition
#     """
#     if parts:
#         for part in parts:
#             filename = part.get("filename")
#             mimeType = part.get("mimeType")
#             body = part.get("body")
#             data = body.get("data")
#             file_size = body.get("size")
#             part_headers = part.get("headers")
#             if part.get("parts"):
#                 # recursively call this function when we see that a part
#                 # has parts inside
#                 parse_parts(service, part.get("parts"), folder_name, message)
#             if mimeType == "text/plain":
#                 # if the email part is text plain
#                 if data:
#                     text = urlsafe_b64decode(data).decode()
#                     print(text)
#             elif mimeType == "text/html":
#                 # if the email part is an HTML content
#                 # save the HTML file and optionally open it in the browser
#                 if not filename:
#                     filename = "index.html"
#                 filepath = os.path.join(folder_name, filename)
#                 print("Saving HTML to", filepath)
#                 with open(filepath, "wb") as f:
#                     f.write(urlsafe_b64decode(data))
#             else:
#                 # attachment other than a plain text or HTML
#                 for part_header in part_headers:
#                     part_header_name = part_header.get("name")
#                     part_header_value = part_header.get("value")
#                     if part_header_name == "Content-Disposition":
#                         if "attachment" in part_header_value:
#                             # we get the attachment ID 
#                             # and make another request to get the attachment itself
#                             print("Saving the file:", filename, "size:", get_size_format(file_size))
#                             attachment_id = body.get("attachmentId")
#                             attachment = service.users().messages() \
#                                         .attachments().get(id=attachment_id, userId='me', messageId=message['id']).execute()
#                             data = attachment.get("data")
#                             filepath = os.path.join(folder_name, filename)
#                             if data:
#                                 with open(filepath, "wb") as f:
#                                     f.write(urlsafe_b64decode(data))



# def read_message(service, message):
#     """
#     This function takes Gmail API `service` and the given `message_id` and does the following:
#         - Downloads the content of the email
#         - Prints email basic information (To, From, Subject & Date) and plain/text parts
#         - Creates a folder for each email based on the subject
#         - Downloads text/html content (if available) and saves it under the folder created as index.html
#         - Downloads any file that is attached to the email and saves it in the folder created
#     """
#     msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
#     # parts can be the message body, or attachments
#     payload = msg['payload']
#     headers = payload.get("headers")
#     parts = payload.get("parts")
#     folder_name = "email"
#     has_subject = False
#     if headers:
#         # this section prints email basic info & creates a folder for the email
#         for header in headers:
#             name = header.get("name")
#             value = header.get("value")
#             if name.lower() == 'from':
#                 # we print the From address
#                 print("From:", value)
#             if name.lower() == "to":
#                 # we print the To address
#                 print("To:", value)
#             if name.lower() == "subject":
#                 # make our boolean True, the email has "subject"
#                 has_subject = True
#                 # make a directory with the name of the subject
#                 folder_name = clean(value)
#                 # we will also handle emails with the same subject name
#                 folder_counter = 0
#                 while os.path.isdir(folder_name):
#                     folder_counter += 1
#                     # we have the same folder name, add a number next to it
#                     if folder_name[-1].isdigit() and folder_name[-2] == "_":
#                         folder_name = f"{folder_name[:-2]}_{folder_counter}"
#                     elif folder_name[-2:].isdigit() and folder_name[-3] == "_":
#                         folder_name = f"{folder_name[:-3]}_{folder_counter}"
#                     else:
#                         folder_name = f"{folder_name}_{folder_counter}"
#                 os.mkdir(folder_name)
#                 print("Subject:", value)
#             if name.lower() == "date":
#                 # we print the date when the message was sent
#                 print("Date:", value)
#     if not has_subject:
#         # if the email does not have a subject, then make a folder with "email" name
#         # since folders are created based on subjects
#         if not os.path.isdir(folder_name):
#             os.mkdir(folder_name)
#     parse_parts(service, parts, folder_name, message)
#     print("="*50)

# results = search_messages(service, "Machine Learning Engineer")
# print(f"Found {len(results)} results.")
# # for each email matched, read it (output plain/text to console & save HTML and attachments)
# for msg in results:
#     read_message(service, msg)

# %%
def search_messages(service, query):
    result = service.users().messages().list(userId='me', q=query).execute()
    messages = []
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages

def get_message_content(service, message_id):
    msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    payload = msg['payload']
    headers = payload.get("headers")
    parts = payload.get("parts")
    
    subject = ""
    sender = ""
    for header in headers:
        if header['name'] == 'Subject':
            subject = header['value']
        if header['name'] == 'From':
            sender = header['value']
    
    body = ""
    if parts:
        for part in parts:
            if part['mimeType'] == 'text/plain':
                body = urlsafe_b64decode(part['body']['data']).decode()
                break
    else:
        if payload.get('body') and payload['body'].get('data'):
            body = urlsafe_b64decode(payload['body']['data']).decode()
    
    return {
        'subject': subject,
        'sender': sender,
        'body': body
    }

# Search for LinkedIn Job alerts and Machine Learning Engineer emails
query = "Machine Learning Engineer"
messages = search_messages(service, query)

# Process the found messages
for msg in messages:
    content = get_message_content(service, msg['id'])
    print(f"Subject: {content['subject']}")
    print(f"From: {content['sender']}")
    print(f"Body snippet: {content['body'][:100]}...")  # Print first 100 characters of the body
    print("-------------------")

# %% delete all gmails within folder
def list_emails(service, label_ids='CATEGORY_PROMOTIONS'):
    """List all emails with the given label using pagination."""
    emails = []
    next_page_token = None
    while True:
        results = service.users().messages().list(
            userId='me', 
            labelIds=[label_ids], 
            pageToken=next_page_token,
            maxResults=500
        ).execute()
        messages = results.get('messages', [])
        emails.extend([msg['id'] for msg in messages])
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break
    return emails

def delete_emails(service, email_ids):
    """Delete emails by IDs"""
    for email_id in email_ids:
        service.users().messages().delete(userId='me', id=email_id).execute()

# Get the Gmail API service
service = gmail_authenticate()

# List all Promotion emails
promotion_emails = list_emails(service, 'CATEGORY_SOCIAL')

# %%
delete_emails(service, promotion_emails)
# %% write a function to query all emails
# query include sender, subject, summary of body

def get_emails_details(service, label_ids='INBOX'):
    """Retrieve a list of emails with their IDs, subjects, and sender addresses."""
    emails_details = {}
    next_page_token = None
    
    while True:
        # Fetch the list of messages
        results = service.users().messages().list(
            userId='me', 
            labelIds=[label_ids], 
            pageToken=next_page_token,
            maxResults=100  # Reduce the number to handle detailed queries without hitting quota limits quickly
        ).execute()
        
        messages = results.get('messages', [])
        
        # For each message, get its ID and fetch required details
        for msg in messages:
            msg_id = msg['id']
            message = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['From', 'Subject']).execute()
            
            # Extract the subject and sender's email from the headers
            headers = message.get('payload', {}).get('headers', [])
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), "No Subject")
            from_email = next((header['value'] for header in headers if header['name'] == 'From'), "Unknown Sender")
            
            # Store the details in the dictionary
            emails_details[msg_id] = {'subject': subject, 'from': from_email}
        
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break
    
    return emails_details

email_details = get_emails_details(service)


# %%
def filter_emails_by_sender(service, label_ids='INBOX', target_str=[]):
    """Filter emails by sender patterns provided in target_str list and return their IDs."""
    target_emails = {}
    next_page_token = None
    
    while True:
        results = service.users().messages().list(
            userId='me', 
            labelIds=[label_ids], 
            pageToken=next_page_token,
            maxResults=100  # Optimal number to balance performance and API usage
        ).execute()
        
        messages = results.get('messages', [])
        
        for msg in messages:
            msg_id = msg['id']
            message = service.users().messages().get(
                userId='me', id=msg_id, format='metadata', metadataHeaders=['From']
            ).execute()
            
            headers = message.get('payload', {}).get('headers', [])
            from_email = next((header['value'] for header in headers if header['name'] == 'From'), None)
            
            # Check if 'from_email' contains any of the target strings
            if any(target.lower() in from_email.lower() for target in target_str):
                target_emails[msg_id] = {'from': from_email}
        
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break
    
    return target_emails




def delete_emails(service, email_ids):
    """Delete emails by IDs."""
    for email_id in email_ids:
        service.users().messages().delete(userId='me', id=email_id).execute()

delete_list = ['Kohl','Sam']

emails_delete = filter_emails_by_sender(service,'INBOX',delete_list)
delete_emails_id = list(emails_delete.keys())

# %% delete emails based on id
delete_emails(service, delete_emails_id)

# %% get sender info
def get_unique_senders(service, label_ids='INBOX'):
    """Retrieve unique sender information from emails in the specified label."""
    unique_senders = set()
    next_page_token = None

    while True:
        # Fetch a list of messages
        results = service.users().messages().list(
            userId='me',
            labelIds=[label_ids],
            pageToken=next_page_token,
            maxResults=100  # Adjust as needed based on API limits and performance considerations
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            break

        # For each message, get the 'From' header
        for msg in messages:
            msg_id = msg['id']
            message = service.users().messages().get(
                userId='me', id=msg_id, format='metadata', metadataHeaders=['From']
            ).execute()

            headers = message.get('payload', {}).get('headers', [])
            from_email = next((header['value'] for header in headers if header['name'] == 'From'), None)

            if from_email:
                unique_senders.add(from_email)

        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break

    return unique_senders
unique_senders = get_unique_senders(service)

delete_list = ['Kohl','Sam', 'mala','Banana','adobe',
               'brain','club']

# %%
