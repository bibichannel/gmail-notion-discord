import os
import pickle
import requests
import dictionaries
import credentials
import time

import src.notion as notion
import src.myJira as myJira
import src.gmail as gmail
from src.myJira import Jira
from src.notion import TaskPageProperties, FeaturePageProperties, Comments, CommentProperties, Pages
from datetime import datetime, timedelta

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

def create_page(ticket, summary, piority):
    pages = Pages(credentials.DATABASE_ID_NOTION_TASK, credentials.NOTION_API_KEY)

    if not summary:
        summary = ""

    if not piority:
        piority = "High"
    elif str(piority) == "Highest":
        piority = "High"
    elif str(piority) == "Lowest":
        piority = "Low"

    data = {
        "Task name": {"title": [{ "text": {"content": ticket}}]},
        'URL': {'url': f"https://astrolab1.atlassian.net/browse/{ticket}"},
        "Summary": {"rich_text":[{ "text": { "content": summary}}]},
        "Priority": {"select": {"name": piority}}
    }

    res = pages.create_page(data)
    return res

def update_page_status(page_id, status):
    pages = Pages(credentials.DATABASE_ID_NOTION_TASK, credentials.NOTION_API_KEY)
    if not status:
        return None
    
    if status.upper() == "In Progress".upper():
        data = {
            "Status": {"status":{"name": "In Progress" }},
            "JIRA Status": {"status":{"name": "In progress" }}
        }
        res = pages.update_page(page_id, data)
        return res
    elif status.upper()  == "waiting for pr review".upper():
        data = {
            "JIRA Status": {"status":{"name": "Waiting For PR Review" }}
        }
        res = pages.update_page(page_id, data)
        return res
    elif status.upper()  == "Waiting for QA".upper():
        data = {
            "JIRA Status": {"status":{"name": "Waiting for QA" }}
        }
        res = pages.update_page(page_id, data)
        return res
    else:
        return None
  
def compare_time(time_series, range_time):
    # Compare time in previous range_time minutes

    time_now = datetime.utcnow()
    ten_minutes_ago = time_now - timedelta(minutes=range_time)

    print(f"Ten minutes ago: {ten_minutes_ago}")
    print(f"Time comment   : {time_series}")
    print(f"Time now       : {time_now}")

    if str(ten_minutes_ago) <= str(time_series) <= str(time_now):
        return True
    else:
        return False

def gen_messages_for_comment_jira(jira: object, issue: object):
    jira_latest_comment = jira.get_latest_comment(issue)
    messages = ''
    if jira_latest_comment:
        time_series_jira = myJira.reformat_time_series(jira_latest_comment.created)
        if compare_time(time_series_jira, 10):
            messages = f"**{jira_latest_comment.author}** just commented on JIRA\n"
    return messages

def gen_messages_for_history_jira(jira: object, issue: object):
    jira_latest_history = jira.get_latest_history(issue)
    messages= ''
    if jira_latest_history:
        time_series_jira = myJira.reformat_time_series(jira_latest_history.created)
        if compare_time(time_series_jira, 10):
            messages= f"**{jira_latest_history.author}** has just changed "
            for item in jira_latest_history.items:
                if item.field == "description":
                    messages += "`description`\n"
                else:
                    messages += f"`{item.field}` from {item.fromString} -> {item.toString}\n"  
    return messages

def gen_messages_for_comment_notion(page_id):
    commnets = Comments(credentials.NOTION_API_KEY)
    notion_comments = commnets.get_comments(page_id)
    notion_comment_properties = CommentProperties()
    notion_comment_properties.get_data(commnets.get_latest_comment(notion_comments))

    messages = ''
    if notion_comment_properties.last_edited_time is not None:
        time_series_jira = notion.reformat_time_series(notion_comment_properties.last_edited_time)
        if compare_time(time_series_jira, 5):
            messages = "**Someone** just commented on Notion\n"
    return messages


def handle_notification_from_email(response_feature, respone_task, jira: Jira ):
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

            # Handle in jira project
            issue = jira.get_issue(ticket)
            messages_for_comment_jira = gen_messages_for_comment_jira(jira, issue)
            messages_for_history_jira = gen_messages_for_history_jira(jira, issue)

            gmail.move_to_label(services, messsage['id'], credentials.NAME_LABEL_GMAIL)
            gmail.mark_as_read(services, messsage['id'])

            messages = ""

            object = check_ticket(respone_task, ticket)
            if object:
                # synchronized status from jira to notion
                print("Synchronous processing...")
                synch_status = update_page_status(object.page_id ,str(issue.fields.status))
                if synch_status:
                    print("Synchronous successed")
                else:
                    print("Nothing to sync")

                feature = get_feature(response_feature, object.feature)
                parent_task = get_tasks(respone_task, object.parent_task)
                sub_tasks = get_tasks(respone_task, object.sub_tasks)

                messages_for_comment_notion =  gen_messages_for_comment_notion(object.page_id)
                messages_feature = gen_messages_for_feature(feature)
                messages_parent_task = gen_messages_for_parent_task(parent_task)
                messages_sub_tasks = gen_messages_for_sub_tasks(sub_tasks)
                message_mention_assignee =  gen_messages_for_mention_user(object.assignee)
                message_metion_owner = gen_messages_for_mention_user([object.owner])

                messages = f"\n----------------------------------\n" \
                + f"{messages_for_comment_jira}" \
                + f"{messages_for_history_jira}" \
                + f"{messages_for_comment_notion}" \
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

                # Create new page for notion
                print("Add item to database notion")
                res = create_page(ticket, 
                                  str(issue.fields.summary), 
                                  str(issue.fields.priority))

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

def check_exist_status_file(response_task, path_status_file):
    if not os.path.exists(path_status_file):
        print("File status.pickle not exist. Processcing save data to file")
        new_normalize = notion.data_normalize_by_status(response_task)
        save_data_to_file(path_status_file, new_normalize)

def save_latest_data_to_status_file(response_task, path_status_file):
    new_normalize = notion.data_normalize_by_status(response_task)
    save_data_to_file(path_status_file, new_normalize)

def handle_in_progress_status(response_task, path_status_file):
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
    all_ticket_status= get_data_from_file(path_status_file)

    # Iterate over all elements of new_normalize
    for key, value in new_normalize.items():
        if key not in pre_normalize:
            object = check_ticket(response_task, key)
            messages_for_comment_notion =  gen_messages_for_comment_notion(object.page_id)
            messages = f"\n----------------------------------\n" \
            + f"{messages_for_comment_notion}" \
            + f"**({key})**: {all_ticket_status[key]} ---> {value} \n" \
            + "Have a good time at work!\n"

            send_message_to_discord(messages, credentials.WEBHOOK_TOKEN_DISCORD)

    # Save data for again process 
    save_data_to_file(path_file, new_normalize)
   

def handle_waiting_for_pr_review_status(response_task, path_status_file):
    print("Processing notification from 'Watting for PR Review' status of notion...")

    # Get data from notion database
    new_normalize = notion.data_normalize_by_status(response_task, "Code Review")
    path_file = r'.\storage\code_review.pickle'

    # Check file exist
    if not os.path.exists(path_file):
        print("File code_review.pickle not exist. Processcing save data to file")
        save_data_to_file(path_file, new_normalize)
        return True

    # Get data from file
    pre_normalize = get_data_from_file(path_file)
    all_ticket_status= get_data_from_file(path_status_file)

    # Iterate over all elements of new_normalize
    for key, value in new_normalize.items():
        if key not in pre_normalize:
            object = check_ticket(response_task, key)
            messages_for_comment_notion =  gen_messages_for_comment_notion(object.page_id)
            messages = f"\n----------------------------------\n" \
            + f"{messages_for_comment_notion}" \
            + f"**({key})**: {all_ticket_status[key]}  ---> {value} \n" \
            + f"Please review: <@{922319155070378045}>\n"

            send_message_to_discord(messages, credentials.WEBHOOK_TOKEN_DISCORD)

    # Save data for again process 
    save_data_to_file(path_file, new_normalize)

def handle_notion_status_blocked(response_task, path_status_file):
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
    all_ticket_status= get_data_from_file(path_status_file)

    # Iterate over all elements of new_normalize
    for key, value in new_normalize.items():
        if key not in pre_normalize:
            object = check_ticket(response_task, key)
            messages_for_comment_notion =  gen_messages_for_comment_notion(object.page_id)
            messages = f"\n----------------------------------\n" \
            + f"{messages_for_comment_notion}" \
            + f"**({key})**: {all_ticket_status[key]} ---> {value} \n" \
            + "Oh my god. Help me!!!\n"

            send_message_to_discord(messages, credentials.WEBHOOK_TOKEN_DISCORD)

    # Save data for again process 
    save_data_to_file(path_file, new_normalize)
