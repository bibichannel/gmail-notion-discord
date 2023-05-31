import os
import pickle
import requests
import dictionaries
import credentials
import time

import src.notion as notion
import src.gmail as gmail
from src.notion import PropertiesNotion

def get_id_member_in_directories(username):
    user_dict = dictionaries.user_dict
    for key in user_dict:
        if key == username:
            return user_dict[key]
    return None

def send_message_to_discord(response, messages, webhook_discord):
    if response is not None:
        data = {
            "content": messages,
            "username" : "Assetz Bot"
        }
        
        try:
            requests.post(webhook_discord, data = data)
        except Exception as e:
            print(e)

def mention_owner(list_members):
    message = ""
    for member in list_members:
        user_id =  get_id_member_in_directories(member)
        if user_id is not None:
            message += f"<@{user_id}> "
        else:
            message += f"@{member} "
    return message

def save_data_to_file(filePath, object):
    with open(filePath, 'wb') as f:
        pickle.dump(object, f) 
    print("Save successed")

def get_data_from_file(filePath):
    with open(filePath, 'rb') as f:
        object = pickle.load(f)
    print("Get successed")    
    return object

def create_page(data: dict, DATABASE_ID, NOTION_TOKEN):
    create_url = "https://api.notion.com/v1/pages"

    headers = {
        "Authorization": NOTION_TOKEN,
        "Notion-Version": "2022-06-28"
        }

    payload = {"parent": {"database_id": DATABASE_ID}, "properties": data}

    res = requests.post(create_url, headers=headers, json=payload)
    print(f"Status code: {res.status_code}")


def handle_notification_from_email(response):
    print("Handles notification from email...")

    # Gmail
    services =  gmail.gmail_authenticate()
    message_list =  gmail.get_message_unread(services)
    if not message_list:
        print("Do not have new message")
        return False
    message_list_reconstruct =  gmail.reconstruct_unread_message_list(services, message_list)

    list_ticket = {}

    for messsage in message_list_reconstruct:
        subject =  messsage['subject']
        ticket =  gmail.get_ticket(subject)
        
        if ticket is not None:
            print("-----------------------------")  
            print(ticket)

            gmail.move_to_label(services, messsage['id'], credentials.NAME_LABEL_GMAIL)
            gmail.mark_as_read(services, messsage['id'])

            object = PropertiesNotion()
            print(f"ID object: {object.id}")

            messages = ""

            if object.check_ticket_assgin(response, ticket):
                message_mention_assignee =  mention_owner(object.assign)
                link = object.link.replace('*', '\\*')

                messages = f"\n----------------------------------\n" \
                + f"[JIRA] ({object.ticket}):\n" \
                + f"- Owner: {object.owner}\n" \
                + f"- Link: <{link}>\n" \
                + f"- Assign: {message_mention_assignee}\n" \
                + f"- {object.note}\n"
            else:
                if ticket in list_ticket:
                    continue                

                messages = f"\n----------------------------------\n" \
                + f"New ticket {ticket}\n" \
                + "I created a ticket on the notion, go there and update (^-^)" \
                + f" <@{612976675583688710}> <@{612976675583688710}>\n"

                data = {
                    "Ticket": {"title": [{ "text": {"content": ticket}}]},
                    "Note": {"rich_text": [{"text": {"content": "This is the new ticket, update please!"}}]},
                    "Status": {"status": {"name": "Todo"} },
                }
                # Create new page for notion
                print("Add item to database notion")
                create_page(data, credentials.DATABASE_ID_NOTION, credentials.KEY_NOTION)                
                
            if ticket not in list_ticket:
                list_ticket[ticket] = messages  

        else:
            print("-----------------------------")
            print("Get ticket fuction return None")
    
    # Sent message to discord
    print("\nStarting sent message...")
    for messages in list_ticket.values():
        send_message_to_discord(response, messages, credentials.WEBHOOK_TOKEN_DISCORD)
        time.sleep(3)
        print("Done")
    
    print("Sent message success!")

        

def handle_in_progress_status(response):
    print("Processing notification from 'In progress' status of notion...")

    new_normalize = notion.data_normalize_by_status(response, "In progress")
    path_file = r'.\storage\in_progress.pickle'

    # Check file exist
    if not os.path.exists(path_file):
        print("File in_progress.pickle not exist. Processcing save data to file")
        save_data_to_file(path_file, new_normalize)
        return True

    # Get data from file
    pre_normalize = get_data_from_file(path_file)

    # Iterate over all elements of new_normalize
    for key, value in new_normalize.items():
        if key not in pre_normalize:
            messages = f"\n----------------------------------\n" \
            + f"({key}) ---> {value} \n" \
            + "Have a good time at work!\n"

            send_message_to_discord(response, messages, credentials.WEBHOOK_TOKEN_DISCORD)

    # Save data for again process 
    save_data_to_file(path_file, new_normalize)
   

def handle_waiting_for_pr_review_status(response):
    print("Processing notification from 'Watting for PR Review' status of notion...")

    # Get data from notion database
    new_normalize = notion.data_normalize_by_status(response, "Waiting for PR Review")
    path_file = r'.\storage\waiting_for_pr_review.pickle'

    # Check file exist
    if not os.path.exists(path_file):
        print("File waiting_for_pr_review.pickle not exist. Processcing save data to file")
        save_data_to_file(path_file, new_normalize)
        return True

    # Get data from file
    pre_normalize = get_data_from_file(path_file)

    # Iterate over all elements of new_normalize
    for key, value in new_normalize.items():
        if key not in pre_normalize:
            messages = f"\n----------------------------------\n" \
            + f"({key}) ---> {value} \n" \
            + f"Please review: <@{612976675583688710}>\n"

            send_message_to_discord(response, messages, credentials.WEBHOOK_TOKEN_DISCORD)

    # Save data for again process 
    save_data_to_file(path_file, new_normalize)

def handle_notion_status_blocked(response):
    print("Processing notification from 'Blocked' status of notion...")

    new_normalize = notion.data_normalize_by_status(response, "Blocked")

    path_file = r'.\storage\blocked.pickle'

    # Check file exist
    if not os.path.exists(path_file):
        print("File Blocked.pickle not exist. Processcing save data to file")
        save_data_to_file(path_file, new_normalize)
        return True

    # Get data from file
    pre_normalize = get_data_from_file(path_file)

    # Iterate over all elements of new_normalize
    for key, value in new_normalize.items():
        if key not in pre_normalize:
            messages = f"\n----------------------------------\n" \
            + f"({key}) ---> {value} \n" \
            + "Oh my god. Help me!!!\n"

            send_message_to_discord(response, messages, credentials.WEBHOOK_TOKEN_DISCORD)

    # Save data for again process 
    save_data_to_file(path_file, new_normalize)
