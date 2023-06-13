import os
import pickle
import requests
import dictionaries
import credentials
import time

import src.notion as notion
import src.gmail as gmail
from src.notion import Notion, TaskPageProperties, FeaturePageProperties

def get_id_member_in_directories(username):
    user_dict = dictionaries.user_dict
    for key in user_dict:
        if key == username:
            return user_dict[key]
    return None

def send_message_to_discord(messages, webhook_discord):
    data = {
        "content": messages,
        "username" : "Assetz Bot"
    }
    
    try:
        requests.post(webhook_discord, data = data)
    except Exception as e:
        print(e)

def check_ticket(response_task, ticket):
    for pages in response_task:
        obj_task = TaskPageProperties()
        obj_task.get_data(pages)

        if obj_task.task_name:
            if ticket in obj_task.task_name:
                return obj_task
    return None

# Get object of relation database feture in FeaturePageProperties object 
def get_feature(response, list_id):
    if list_id is None:
        return None
    
    list_feature = []
    for id in list_id:
        for pages in response:
            obj_feature = FeaturePageProperties()
            obj_feature.get_data(pages)

            if id in obj_feature.page_id:
                list_feature.append(obj_feature)

    if list_feature:
        return list_feature
    return None

# Get sub-tasks, parent-task of TaskPageProperties object
def get_tasks(response, list_id):
    if list_id is None:
        return None

    list_task = []
    for id in list_id:
        for pages in response:
            obj_task = TaskPageProperties()
            obj_task.get_data(pages)

            if id in obj_task.page_id:
                list_task.append(obj_task)

    if list_task:
        return list_task
    return None

def gen_messages_for_mention_user(list_members):
    message = ""
    if list_members:
        for member in list_members:
            userid = get_id_member_in_directories(member)
            if userid:
                message += f"<@{userid}> "
            else:
                message += f"@{member}"
    return message

def gen_messages_for_feature(list_object):
    messages = ""
    if list_object:
        for elements in list_object:
            messages += f"**[{elements.project_name}]** - `{elements.status}`\n" \
            + f"- Owner: {gen_messages_for_mention_user(elements.owner)}\n"
    return messages

def gen_messages_for_parent_task(list_object):
    messages = ""
    if list_object:
        for elements in list_object:
            messages += f"\n- {elements.task_name} - `{elements.status}`"
    return messages

def gen_messages_for_sub_tasks(list_object):
    messages = ""
    if list_object:
        for elements in list_object:
            messages += f"\n- {elements.task_name} - `{elements.status}`"
    return messages

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

    return res.json()

def handle_notification_from_email(response_feature, respone_task):
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

            messages = ""

            object = check_ticket(respone_task, ticket)
            if object:
                feature = get_feature(response_feature, object.feature)
                parent_task = get_tasks(respone_task, object.parent_task)
                sub_tasks = get_tasks(respone_task, object.sub_tasks)

                messages_feature = gen_messages_for_feature(feature)
                messages_parent_task = gen_messages_for_parent_task(parent_task)
                messages_sub_tasks = gen_messages_for_sub_tasks(sub_tasks)
                message_mention_assignee =  gen_messages_for_mention_user(object.assignee)
                message_metion_owner = gen_messages_for_mention_user([object.owner])

                messages = f"\n----------------------------------\n" \
                + f"{messages_feature}" \
                + f"**[{object.task_name}]** " \
                + f"- `{object.status}`" \
                + f"- Jira status: `{object.jira_status}`\n" \
                + f"- <{object.url_jira}>\n" \
                + f"- <{object.page_url}>\n" \
                + f"- Owner {message_metion_owner}\n" \
                + f"- Assign {message_mention_assignee}\n" \
                
                if messages_parent_task:
                    messages += f"**[PARENT-TASK]**{messages_parent_task}\n"

                if messages_sub_tasks:
                    messages += f"**[SUB-TASKS]**{messages_sub_tasks}\n" 
            else:
                if ticket in list_ticket:
                    continue

                # Create payload to add item into notion database
                data = {
                    "Task name": {"title": [{ "text": {"content": ticket}}]},
                    'URL': {'url': f"https://astrolab1.atlassian.net/browse/{ticket}"}
                }
                # Create new page for notion
                print("Add item to database notion")
                res = create_page(data, credentials.DATABASE_ID_NOTION_TASK, credentials.NOTION_API_KEY)

                if 400 not in res.values():
                    # Create message to sent to discord
                    messages = f"\n----------------------------------\n" \
                    + f"**[NEW TICKET]** {ticket}\n" \
                    + "Notion ticket created, please update!\n" \
                    + f"- Link ticket: <{res['properties']['URL']['url']}>\n" \
                    + f"- Link notion: <{res['url']}>" \
                    + f"\n<@{694732284116598797}> <@{922319155070378045}>\n"
                else:
                    messages = f"\n----------------------------------\n" \
                    + f"**[NEW TICKET]** {ticket}\n" \
                    + "[ERROR] Auto ticket creation on Notion is faulty\n" \
                    + f"- {res['message']}" \
                    + f"\n<@{694732284116598797}> <@{922319155070378045}>\n"
                
            if ticket not in list_ticket:
                list_ticket[ticket] = messages  

        else:
            print("----------------------------------")
    
    # Sent message to discord
    print("\nStarting sent message...")
    for messages in list_ticket.values():
        send_message_to_discord(messages, credentials.WEBHOOK_TOKEN_DISCORD)
        time.sleep(3)
        print("Done")
    
    print("Sent message success!\n")

def handle_in_progress_status(response_task):
    print("Processing notification from 'In progress' status of notion...")

    new_normalize = notion.data_normalize_by_status(response_task, "In Progress")
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
            + f"**({key})** ---> {value} \n" \
            + "Have a good time at work!\n"

            send_message_to_discord(messages, credentials.WEBHOOK_TOKEN_DISCORD)

    # Save data for again process 
    save_data_to_file(path_file, new_normalize)
   

def handle_waiting_for_pr_review_status(response_task):
    print("Processing notification from 'Watting for PR Review' status of notion...")

    # Get data from notion database
    new_normalize = notion.data_normalize_by_status(response_task, "Waiting For Review")
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
            + f"**({key})** ---> {value} \n" \
            + f"Please review: <@{922319155070378045}>\n"

            send_message_to_discord(messages, credentials.WEBHOOK_TOKEN_DISCORD)

    # Save data for again process 
    save_data_to_file(path_file, new_normalize)

def handle_notion_status_blocked(response_task):
    print("Processing notification from 'Blocked' status of notion...")

    new_normalize = notion.data_normalize_by_status(response_task, "Blocked")

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
            + f"**({key})** ---> {value} \n" \
            + "Oh my god. Help me!!!\n"

            send_message_to_discord(messages, credentials.WEBHOOK_TOKEN_DISCORD)

    # Save data for again process 
    save_data_to_file(path_file, new_normalize)
