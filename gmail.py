# https://developers.google.com/gmail/api/quickstart/python
# https://developers.google.com/gmail/api/reference/rest

from __future__ import print_function

import os.path
import re
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://mail.google.com/']

def gmail_authenticate():

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                './credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        # Call the Gmail API
        return build('gmail', 'v1', credentials=creds)

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')
        return None

def get_message_unread(services):
    results = services.users().messages().list(userId='me', labelIds='INBOX', q="is:unread").execute()
    message_list = results.get('messages', [])
    
    if not message_list:
        return None
    else:
        return message_list

def reconstruct_unread_message_list(services, message_list):
    new_message_list = []

    for message in message_list:
        message = services.users().messages().get(userId='me', id=message["id"], format='metadata', metadataHeaders=['Subject']).execute()

        for header in message['payload']['headers']:
            if header['name'] == 'Subject':
                new_dict = {'id': message['id'], 'subject': header['value']}
                new_message_list.append(new_dict)
                break
    return new_message_list

# def get_message_subject(message_list, message_id):
#     for message in message_list:
#         if message['id'] == message_id :
#             return message['subject']

def get_ticket(message_subject):
    matches = re.findall(r'\b(?:AST|JIRA|\*AST)\b', message_subject, flags=re.IGNORECASE)
    if not matches:
        return None
    # Get elements
    return re.search(r'\b(?:AST|JIRA|\*AST)-\d+\b', message_subject, flags=re.IGNORECASE).group()

def move_to_label(services, message_id, label_name):
    try:
        # search id of "Jira" label
        labels = services.users().labels().list(userId='me').execute().get('labels', [])
        label_id = None
        for label in labels:
            if label['name'] == label_name:
                label_id = label['id']
                break

        # move email to "Jira" label
        if label_id:
            message = services.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id], 'removeLabelIds': ['INBOX']}
            ).execute()
            print(f"Message {message_id} moved to {label_name} label.")
        else:
            print(f"{label_name} label not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def mark_as_read(services, message_id):
    try:
        message = services.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        print(f"Message {message_id} marked as read.")
    except Exception as e:
        print(f"An error occurred: {e}")



