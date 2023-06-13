import handles
import time
import credentials
from src.notion import Notion

def processing_1():
    # Notion
    while True:
        noti_feature = Notion(credentials.DATABASE_ID_NOTION_FEATURE, credentials.NOTION_API_KEY)
        response_feature =  noti_feature.post()

        noti_task = Notion(credentials.DATABASE_ID_NOTION_TASK, credentials.NOTION_API_KEY)
        response_task =  noti_task.post()

        handles.handle_notification_from_email(response_feature, response_task)
        time.sleep(10)
        handles.handle_in_progress_status(response_task)
        time.sleep(10)
        handles.handle_waiting_for_pr_review_status(response_task)
        time.sleep(10)
        handles.handle_notion_status_blocked(response_task)
        time.sleep(270)

if __name__ == '__main__':
    print("Start")
    processing_1()