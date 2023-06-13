from src.notion import Notion, TaskPageProperties, FeaturePageProperties
import credentials

# mention user discord: <@!email>
import pickle
import requests
import credentials
import dictionaries
import time

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

def check_ticket(response, ticket):
    for pages in response:
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
            messages += f"\n- {elements.project_name} -> {elements.status} \n - Owner: {gen_messages_for_mention_user(elements.owner)}"
    return messages

def gen_messages_for_parent_task(list_object):
    messages = ""
    if list_object:
        for elements in list_object:
            messages += f"\n- {elements.task_name} -> {elements.status}"
    return messages

def gen_messages_for_sub_tasks(list_object):
    messages = ""
    if list_object:
        for elements in list_object:
            messages += f"\n- {elements.task_name} -> {elements.status}"
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

def handle_notification_from_email(response_feature, response_task): 
    ticket = "AST-2391"
    print("-----------------------------")  
    print(ticket)

    messages = ""

    object = check_ticket(response_task, ticket)
    if object:
        feature = get_feature(response_feature, object.feature)
        parent_task = get_tasks(response_task, object.parent_task)
        sub_tasks = get_tasks(response_task, object.sub_tasks)

        messages_feature = gen_messages_for_feature(feature)
        messages_parent_task = gen_messages_for_parent_task(parent_task)
        messages_sub_tasks = gen_messages_for_sub_tasks(sub_tasks)
        message_mention_assignee =  gen_messages_for_mention_user(object.assignee)
        message_metion_owner = gen_messages_for_mention_user([object.owner])

        link = object.url_jira.replace('*', '\\*')

        messages = f"\n----------------------------------\n" \
        + f"**[PROJECT NAME]**{messages_feature}\n" \
        + f"**[PARENT-TASK]**{messages_parent_task}\n" \
        + f"**[SUB-TASKS]**{messages_sub_tasks}\n" \
        + f"**[CURRENT-TASK]**\n- {object.task_name}\n\t" \
        + f"- Owner {message_metion_owner}\t|" \
        + f"\tAssign {message_mention_assignee}\n\t" \
        + f"- Link Jira: <{link}>\n\t" \
        + f"- Link Notion: <{object.page_url}>\n\t" \
        + f"- Status: {object.status}\n\t" \
        + f"- Jira status: {object.jira_status}\n" 
        
    # Sent message to discord
    print("\nStarting sent message...")
    send_message_to_discord(messages, credentials.WEBHOOK_TOKEN_DISCORD)
    time.sleep(3)
    print("Done")
    
    print("Sent message success!\n")


noti_feature = Notion(credentials.DATABASE_ID_NOTION_FEATURE, credentials.NOTION_API_KEY)
response_feature =  noti_feature.post()

noti_task = Notion(credentials.DATABASE_ID_NOTION_TASK, credentials.NOTION_API_KEY)
response_task =  noti_task.post()
if response_feature is not None and response_task is not None:
    handle_notification_from_email(response_feature, response_task)
else: print("Error")