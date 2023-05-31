import handles
import time
import credentials
from src.notion import Notion

def processing_1():
    # Notion
    while True:
        noti = Notion(credentials.DATABASE_ID_NOTION, credentials.KEY_NOTION)
        response =  noti.post()

        #handles.handle_notification_from_email(response)
        time.sleep(10)
        handles.handle_in_progress_status(response)
        time.sleep(10)
        handles.handle_waiting_for_pr_review_status(response)
        time.sleep(10)
        handles.handle_notion_status_blocked(response)
        time.sleep(270)

if __name__ == '__main__':
    print("Start")
    processing_1()