from src.notion import Notion, TaskPageProperties, FeaturePageProperties
import credentials

noti_feature = Notion(credentials.DATABASE_ID_NOTION_FEATURE, credentials.NOTION_API_KEY)
response_feature =  noti_feature.post()

noti_task = Notion(credentials.DATABASE_ID_NOTION_TASK, credentials.NOTION_API_KEY)
response_task =  noti_task.post()

i = 0

for pages in response_feature:
    obj_f = FeaturePageProperties()
    obj_f.get_data(pages)

    message = f"{obj_f.id}\n" \
    + f"{obj_f.page_url}\n" \
    + f"{obj_f.page_id}\n" \
    + f"{obj_f.project_name}\n" \
    + f"{obj_f.status}\n" \
    + f"{obj_f.priority}\n" \
    + f"{obj_f.completion}\n" \
    + f"{obj_f.is_blocking}\n" \
    + f"{obj_f.block_by}\n"

    print(message)
    i += 1
    if i > 10: break

#  message = f"{obj_f.id}\n" \
#     + f"{}\n" \
#     + f"{}\n" \
#     + f"{}\n" \
#     + f"{}\n" 

for pages in response_task:
    obj_t = TaskPageProperties()
    obj_t.get_data(pages)

    message = f"{obj_t.id}\n" \
    + f"{obj_t.page_url}\n" \
    + f"{obj_t.page_id}\n" \
    + f"{obj_t.status}\n" \
    + f"{obj_t.jira_status}\n" \
    + f"{obj_t.tags}\n" \
    + f"{obj_t.assignee}\n" \
    + f"{obj_t.priority}\n"

    print(message)
    i += 1
    if i > 10: break

# mention user discord: <@!email>