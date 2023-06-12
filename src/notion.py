import requests
import random

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

        url = f"{self.base_url}{self.database_id}/query"

        get_all = num_pages is None
        page_size = 100 if get_all else num_pages

        payload = {"page_size": page_size}
        response = requests.post(url, data=payload, headers=self.header)

        data = response.json()

        results = data["results"]
        while data["has_more"] and get_all:
            payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
            response = requests.post(url, json=payload, headers=self.header)
            data = response.json()
            results.extend(data["results"])
        return results
      
    def dictionary_decoder(self, response):
        return [i for i in response]

# ------------------------------------------------------------------------

class TaskPageProperties():
    def __init__(self):
        '''
        ['URL', 'Report', 'Owner', 'Last edited by', 'Summary', 
        'JIRA Status', 'Last edited time', 'Evidence', 'Task name', 
        'Tags', 'Assignee', 'Status', 'Due', 'Priority', 'Sub-tasks', 
        'Estimates', 'Parent-task', 'Feature']
        '''
        self.id = random.randint(2000, 5000)
        self.page_id = None
        self.page_url = None
        self.jira_status= None
        self.status = None
        self.task_name = None
        self.url_jira = None
        self.owner = None
        self.report = None
        self.summary = None
        self.estimates = None
        self.evidence = None
        self.priority = None
        self.tags = None
        self.feature = None
        self.parent_task = None
        self.sub_tasks = None
        self.assignee = None

    def get_data(self, pages):

        self.page_id = pages['id']

        self.page_url = pages['url']

        self.jira_status = pages['properties']['JIRA Status']['status']['name']

        self.status =  pages['properties']['Status']['status']['name']

        if pages["properties"]["Task name"]["title"]:
            self.task_name = pages['properties']["Task name"]["title"][0]["plain_text"]
        
        if pages['properties']['URL']['url']:
            self.url_jira = pages['properties']['URL']['url']

        if pages['properties']['Owner']['select']:
            self.owner = pages['properties']['Owner']['select']['name']
        
        if pages['properties']['Report']['select']:
            self.report = pages['properties']['Report']['select']['name']

        if pages['properties']['Summary']['rich_text']:
            self.summary = pages['properties']['Summary']['rich_text'][0]['plain_text']

        if pages['properties']['Estimates']['select']:
            self.estimates = pages['properties']['Estimates']['select']['name']

        if pages['properties']['Evidence']['files']:
            self.evidence = pages['properties']['Evidence']['files']

        if pages['properties']['Priority']['select']:
            self.priority = pages['properties']['Priority']['select']['name']

        if pages['properties']['Tags']['multi_select']:
            self.tags = [i['name'] for i in pages['properties']['Tags']['multi_select']]

        if pages['properties']['Feature']['relation']:
            self.feature = [i['id'] for i in pages['properties']['Feature']['relation']]
        
        if pages['properties']['Parent-task']['relation']:
            self.parent_task = pages['properties']['Parent-task']['relation'][0]['id']
        
        if pages['properties']['Sub-tasks']['relation']:
            self.sub_tasks = [i['id'] for i in pages['properties']['Sub-tasks']['relation']]
        
        if pages['properties']['Assignee']['people']:
            self.assignee = [i['person']['email'] for i in pages['properties']['Assignee']['people']]
        
        
    def check_ticket_assgin(self, ticket):

        if ticket in self.task_name:
            return True
        return False
    

class FeaturePageProperties():

    def __init__(self):

        '''['Project name', 'Owner', 'Status', 'Completion', 
        'Priority', 'Dates', 'Tasks', 'Is Blocking', 'Blocked By']'''

        self.id = random.randint(6000, 9000)
        self.page_url = None
        self.page_id = None
        self.project_name = None
        self.owner = None
        self.status = None
        self.completion = None
        self.priority = None
        self.is_blocking = None
        self.block_by = None

    def get_data(self, pages):

        self.page_id = pages['id']

        self.page_url = pages['url']

        self.status = pages['properties']['Status']['status']['name']

        if pages['properties']['Project name']['title']:
            self.project_name = pages['properties']['Project name']['title'][0]['plain_text']

        if pages['properties']['Owner']['people']:
            self.owner = [i['person']['email'] for i in pages['properties']['Owner']['people']]

        percent = pages['properties']['Completion']['rollup']['number'] if pages['properties']['Completion']['rollup']['number'] else 0
        #self.completion = f"{round(percent*100, 2)}%"
        self.completion = "{:.0f}%".format(round(percent*100))

        if pages['properties']['Priority']['select']:
            self.priority = pages['properties']['Priority']['select']['name']

        if pages['properties']['Is Blocking']['relation']:
            self.is_blocking = [i['id'] for i in pages['properties']['Is Blocking']['relation']]

        if pages['properties']['Blocked By']['relation']:
            self.block_by = [i['id'] for i in pages['properties']['Blocked By']['relation']]


# --------------------------------------------------------------
# data noramilize to dict: {<ticket>:<status>}
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
