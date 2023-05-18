import requests
import random
import pickle

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
    
    def save_data_to_file(self, filePath, object):
        with open(filePath, 'wb') as f:
            pickle.dump(object, f) 
        print("Save successed")

    def get_data_from_file(self, filePath):
        with open(filePath, 'rb') as f:
            object = pickle.load(f)
        print("Get successed")    
        return object
        
    def dictionary_decoder(self, response):
        return [i for i in response]


# ------------------------------------------------------------------------

class PropertiesNotion(Notion):
    # Properly of database Notion

    def __init__(self):
        self.id = random.randint(5000, 5500)
        self.assign = []
        self.ticket = ""
        self.note = ""
        self.link = ""
        self.owner = ""
        self.status = ""

    def __del__(self):
        self.assign = []
        self.ticket = ""
        self.note = ""
        self.link = ""
        self.owner = ""
        self.status = ""
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

                if pages["properties"]["Status"]["status"] is not None:
                    self.status = pages["properties"]["Status"]["status"]["name"]

                if pages["properties"]['Assignee']['multi_select'] != []:
                    for j in range(len(pages["properties"]["Assignee"]["multi_select"])):
                        assign_user = pages["properties"]["Assignee"]["multi_select"][j]["name"]
                        self.assign.append(assign_user)

                return True
        return False
        
# --------------------------------------------------------------

def data_normalize_by_status(response, status_name):
    new_data_dict = {}

    for element in response:
        if element["properties"]["Ticket"]["title"] != []:
            ticket = element["properties"]["Ticket"]["title"][0]["plain_text"]
        else:
            continue

        if element["properties"]["Status"]["status"] is not None:
            if status_name in element["properties"]["Status"]["status"]["name"]:
                new_data_dict[ticket] = element["properties"]["Status"]["status"]["name"]
        else:
            continue
    
    return new_data_dict

query = {"filter": {"property": "Ticket", "exists": True}}
