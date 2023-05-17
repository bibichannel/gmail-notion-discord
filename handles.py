import requests
import dictionaries
import credentials
from notion import Notion
from notion import PropertiesNotion
import gmail


async def get_id_member_in_directories(username):
    user_dict = dictionaries.user_dict
    for key in user_dict:
        if key == username:
            return user_dict[key]
    return None

async def get_response_notion(notion_object):
    response = notion_object.post()
    if response is not None:
        return response
    else:
        return None

async def send_message_to_discord(response, messages, webhook_discord):
    if response is not None:
        data = {
            "content": messages,
            "username" : "Jira"
        }
        
        try:
            await requests.post(webhook_discord, data = data)
        except Exception as e:
            print(e)


async def mention_owner(list_members):
    message = ""
    for member in list_members:
        user_id = await get_id_member_in_directories(member)
        if user_id is not None:
            message += f"<@{user_id}> "
        else:
            message += f"@{member} "
    return message

async def handle():
    print("Handles...")

    # Notion
    noti = Notion(credentials.DATABASE_ID_NOTION, credentials.KEY_NOTION)
    response = await get_response_notion(noti)

    # Gmail
    services = await gmail.gmail_authenticate()
    message_list = await gmail.get_message_unread(services)
    if not message_list:
        print("Do not have new message")
        return False
    message_list_reconstruct = await gmail.reconstruct_unread_message_list(services, message_list)

    # Check each mesage in the list after normalized
    for messsage in message_list_reconstruct:
        subject = await gmail.get_message_subject(message_list_reconstruct, messsage['id'])
        ticket = await gmail.get_ticket(subject)

        if ticket is not None:  
            print(ticket)
            print("-----------------------------")
            await gmail.move_to_label(services, messsage['id'], 'JIRA')
            await gmail.mark_as_read(services, messsage['id'])
        
            object = PropertiesNotion()
            print(f"ID object: {object.id}")
            messages = ""

            if object.check_ticket_assgin(response, ticket):
                message_mention_assignee = await mention_owner(object.assign)
                link = object.link.replace('*', '\\*')
                messages = f"\n----------------------------------\n[JIRA] ({object.ticket}):\n- Owner: {object.owner}\n- Link: <{link}>\n- Assign: {message_mention_assignee}\n- {object.note}\n"
            else:
                messages = f"\n----------------------------------\nNew ticket {ticket}\n"

            await send_message_to_discord(response, messages, credentials.WEBHOOK_TOKEN_DISCORD)

        else:
            print("Get ticket fuction return None")
        