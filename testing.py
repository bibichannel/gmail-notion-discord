from src.notion import Notion, TaskPageProperties, FeaturePageProperties, Comments, CommentProperties, Pages
from src.myJira import Jira
from datetime import datetime, timedelta
import src.notion as notion
import src.myJira as myJira


import credentials

# mention user discord: <@!email>
import pickle
import requests
import credentials
import dictionaries
import time

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
        if compare_time(time_series_jira, 15):
            messages = f"**{jira_latest_comment.author}** just commented on JIRA\n"
    return messages

def gen_messages_for_history_jira(jira: object, issue: object):
    jira_latest_history = jira.get_latest_history(issue)
    messages= ''
    if jira_latest_history:
        time_series_jira = myJira.reformat_time_series(jira_latest_history.created)
        if compare_time(time_series_jira, 15):
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

def gen_messages_compare_jira_status(jira_status_notion, jira_status):
    if jira_status_notion in jira_status:
        return True
    else:
        return f"Jira status in notion `{jira_status_notion}` and jira status in atlassian `{jira_status}`"

def handle_notification_from_email(response_feature, response_task, jira: Jira): 
    ticket = "AST-2448"
    print("-----------------------------")  
    print(ticket)

    # Check info ticket in jira
    issue = jira.get_issue(ticket)
    print('Summary:', issue.fields.summary)
    print('Assignee: ', issue.fields.assignee)
    print('Status: ', issue.fields.status)
    print('Priority: ', issue.fields.priority)

    # Get latest comment in jira
    messages_for_comment_jira = gen_messages_for_comment_jira(jira, issue)
    messages_for_history_jira = gen_messages_for_history_jira(jira, issue)

    messages = ""

    object = check_ticket(response_task, ticket)

    if object:
        feature = get_feature(response_feature, object.feature)
        parent_task = get_tasks(response_task, object.parent_task)
        sub_tasks = get_tasks(response_task, object.sub_tasks)

        # Get latest comment in notion
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
        
    # Sent message to discord
    print("\nStarting sent message...")
    send_message_to_discord(messages, credentials.WEBHOOK_TOKEN_DISCORD)
    time.sleep(3)
    print("Done")
    
    print("Sent message success!\n")


# noti_feature = Notion(credentials.DATABASE_ID_NOTION_FEATURE, credentials.NOTION_API_KEY)
# response_feature =  noti_feature.post()

# noti_task = Notion(credentials.DATABASE_ID_NOTION_TASK, credentials.NOTION_API_KEY)
# response_task =  noti_task.post()

# jr = Jira(credentials.JIRA_SERVER, credentials.JIRA_USERNAME, credentials.JIRA_PAT)

# if response_feature is not None and response_task is not None:
#     handle_notification_from_email(response_feature, response_task, jr)
# else: print("Error")

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

def update_page(page_id):
    pages = Pages(credentials.DATABASE_ID_NOTION_TASK, credentials.NOTION_API_KEY)

    data = {
        "Priority": {"select": {"name": "High"}}
    }

    res = pages.update_page(page_id, data)
    return res
  

# res = create_page("AST-7673", "Testing", "High")
page_id = "939911a6-71e3-40f5-a02e-8c1ee7746f35"
upd = update_page(page_id)