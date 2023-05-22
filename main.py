import handles
import time
import credentials
from notion import Notion
from threading import Thread

def processing():
    # Notion
    while True:
        noti = Notion(credentials.DATABASE_ID_NOTION, credentials.KEY_NOTION)
        response =  noti.post()

        #handles.handle_notification_from_email(response)
        handles.handle_in_progress_status(response)
        handles.handle_waiting_for_pr_review_status(response)
        handles.handle_notion_status_blocked(response)

        time.sleep(180)

if __name__ == '__main__':
    print("Start")
    while True:
        processing()
        time.sleep(180)
    