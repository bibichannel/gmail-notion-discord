import requests
import dictionaries
import credentials
from notion import Notion
from notion import PropertiesNotion
import gmail

def get_id_member_in_directories(username):
    user_dict = dictionaries.user_dict
    for key in user_dict:
        if key == username:
            return user_dict[key]
    return None

def get_response_notion(notion_object):
    response = notion_object.post()
    if response is not None:
        return response
    else:
        return None

def send_message_to_discord(response, messages, webhook_discord):
    if response is not None:
        data = {
            "content": messages,
            "username" : "Jira"
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

def handle():
    print("Handles...")

    # Notion
    noti = Notion(credentials.DATABASE_ID_NOTION, credentials.KEY_NOTION)
    response =  get_response_notion(noti)

    # Gmail
    services =  gmail.gmail_authenticate()
    message_list =  gmail.get_message_unread(services)
    if not message_list:
        print("Do not have new message")
        return False
    message_list_reconstruct =  gmail.reconstruct_unread_message_list(services, message_list)

    for messsage in message_list_reconstruct:
        #subject =  gmail.get_message_subject(message_list_reconstruct, messsage['id'])
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
        