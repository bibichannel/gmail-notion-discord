import requests
import random

"""
1. Connect to Notion data
    - Created a Notion integration key
    - Save key in my_secrets.py file
    - Allow the Notion Integration key to access the page we want to share
2. Connect to Discord
3. Push data to Discord 
"""


class Notion:
    base_url = "https://api.notion.com/v1/databases/"

    def __init__(self, database_id, key):
        self.database_id = database_id
        self.key = key
        self.header = {"Authorization": self.key,
                       "Notion-Version": "2022-06-28"}

    def get(self):
        response = requests.get(self.base_url + self.database_id, headers=self.header)
        return response

    def post(self, num_pages=None):
        """
        If num_pages is None, get all pages, otherwise just the defined number.
        """
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"

        get_all = num_pages is None
        page_size = 100 if get_all else num_pages

        payload = {"page_size": page_size}
        response = requests.post(url, data=payload, headers=self.header)

        data = response.json()

        results = data["results"]
        while data["has_more"] and get_all:
            payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
            url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
            response = requests.post(url, json=payload, headers=self.header)
            data = response.json()
            results.extend(data["results"])

        return results

    def dictionary_decoder(self, response):
        return [i for i in response]


# ------------------------------------------------------------------------

class PropertiesNotion(Notion):
    # Properly of database Notion

    def __init__(self):
        self.id = random.randint(5000, 5500)
        
        self.ticket = ""
        self.note = ""
        self.link = ""
        self.owner = ""
        self.assign = []

    def __del__(self):
        self.assign = []
        self.ticket = ""
        self.note = ""
        self.link = ""
        self.owner = ""
        print("Delete object successed")

    def check_ticket_assgin(self, response, ticket):

        for pages in response:
            if pages["properties"]["Ticket"]["title"] != []:
                self.ticket = pages["properties"]["Ticket"]["title"][0]["plain_text"]

            if ticket in self.ticket:
                if pages["properties"]["Note"]["rich_text"] != []:
                    self.note = pages["properties"]["Note"]["rich_text"][0]["plain_text"]

                if pages["properties"]["Link"]["formula"] != []:
                    self.link = pages["properties"]["Link"]["formula"]["string"]

                if pages["properties"]["Owner"]["select"] is not None:
                    self.owner = pages["properties"]["Owner"]["select"]["name"]

                if pages["properties"]['Assignee']['multi_select'] != []:
                    for j in range(len(pages["properties"]["Assignee"]["multi_select"])):
                        assign_user = pages["properties"]["Assignee"]["multi_select"][j]["name"]
                        self.assign.append(assign_user)
                return True
        return False

# --------------------------------------------------------------


query = {"filter": {"property": "Ticket", "exists": True}}
