import requests
import dictionaries
import credentials
import notion
from notion import Notion
from notion import PropertiesNotion
import gmail
import os
import pickle

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

def handle_notification_from_email(response):
    print("Handles notification from email...")

    # Gmail
    services =  gmail.gmail_authenticate()
    message_list =  gmail.get_message_unread(services)
    if not message_list:
        print("Do not have new message")
        return False
    message_list_reconstruct =  gmail.reconstruct_unread_message_list(services, message_list)

    for messsage in message_list_reconstruct:
        subject =  messsage['subject']
        ticket =  gmail.get_ticket(subject)

        if ticket is not None:  
            print(ticket)
            print("-----------------------------")
            gmail.move_to_label(services, messsage['id'], 'Astrolab')
            gmail.mark_as_read(services, messsage['id'])
        
            object = PropertiesNotion()
            print(f"ID object: {object.id}")
            messages = ""

            if object.check_ticket_assgin(response, ticket):
                message_mention_assignee =  mention_owner(object.assign)
                link = object.link.replace('*', '\\*')
                messages = f"\n----------------------------------\n[JIRA] ({object.ticket}):\n- Owner: {object.owner}\n- Link: <{link}>\n- Assign: {message_mention_assignee}\n- {object.note}\n"
            else:
                messages = f"\n----------------------------------\nNew ticket {ticket}\n <@{694732284116598797}> <@{361429367932583938}>\n"

            send_message_to_discord(response, messages, credentials.WEBHOOK_TOKEN_DISCORD)

        else:
            print("Get ticket fuction return None")
        

def handle_in_progress_status(response):
    print("Processing notification from 'In progress' status of notion...")

    new_normalize = notion.data_normalize_by_status(response, "In progress")

    # Check file exist
    if not os.path.exists('.\storage\in_progress.pickle'):
        print("File in_progress.pickle not exist. Processcing save data to file")
        save_data_to_file(".\storage\in_progress.pickle", new_normalize)
        return True

    # Get data from file
    pre_normalize = get_data_from_file(".\storage\in_progress.pickle")

    # Iterate over all elements of new_normalize
    for key, value in new_normalize.items():
        if key not in pre_normalize:
            messages = f"\n----------------------------------\nTicket {key} has changed to: {value} \nHave a good time at work!\n"
            send_message_to_discord(response, messages, credentials.WEBHOOK_TOKEN_DISCORD)

    # Save data for again process 
    save_data_to_file(".\storage\in_progress.pickle", new_normalize)
   

def handle_waiting_for_pr_review_status(response):
    print("Processing notification from 'Watting for PR Review' status of notion...")

    # Get data from notion database
    new_normalize = notion.data_normalize_by_status(response, "Waiting for PR Review")

    # Check file exist
    if not os.path.exists('.\storage\waiting_for_pr_review.pickle'):
        print("File waiting_for_pr_review.pickle not exist. Processcing save data to file")
        save_data_to_file(".\storage\waiting_for_pr_review.pickle", new_normalize)
        return True

    # Get data from file
    pre_normalize = get_data_from_file(".\storage\waiting_for_pr_review.pickle")

    # Iterate over all elements of new_normalize
    for key, value in new_normalize.items():
        if key not in pre_normalize:
            messages = f"\n----------------------------------\nTicket ({key}) has changed to: {value} \nPlease review: <@{612976675583688710}>\n"
            send_message_to_discord(response, messages, credentials.WEBHOOK_TOKEN_DISCORD)

    # Save data for again process 
    save_data_to_file(".\storage\waiting_for_pr_review.pickle", new_normalize)

def handle_notion_status_blocked(response):
    print("Processing notification from 'Blocked' status of notion...")

    new_normalize = notion.data_normalize_by_status(response, "Blocked")

    # Check file exist
    if not os.path.exists('.\storage\Blocked.pickle'):
        print("File Blocked.pickle not exist. Processcing save data to file")
        save_data_to_file(".\storage\Blocked.pickle", new_normalize)
        return True

    # Get data from file
    pre_normalize = get_data_from_file(".\storage\Blocked.pickle")

    # Iterate over all elements of new_normalize
    for key, value in new_normalize.items():
        if key not in pre_normalize:
            messages = f"\n----------------------------------\nTicket {key} has changed to: {value} \nOmg \\U0001F625 \\U0001F625 \\U0001F625. help me!!!\n"
            send_message_to_discord(response, messages, credentials.WEBHOOK_TOKEN_DISCORD)

    # Save data for again process 
    save_data_to_file(".\storage\Blocked.pickle", new_normalize)