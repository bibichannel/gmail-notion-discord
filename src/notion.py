import requests
import random
from datetime import datetime

class Notion:
    base_url = "https://api.notion.com/v1/databases/"
    version = "2022-06-28"

    def __init__(self, database_id, key):
        self.database_id = database_id
        self.key = key
        self.header = {"Authorization": self.key,
                       "Notion-Version": self.version}

    def get(self):
        response = requests.get(self.base_url + self.database_id, headers=self.header)
        return response

    def post(self, num_pages=None):

        url = f"{self.base_url}{self.database_id}/query"

        get_all = num_pages is None
        page_size = 100 if get_all else num_pages

        payload = {"page_size": page_size}
        response = requests.post(url, data=payload, headers=self.header)
        if response.status_code != 200:
            print(f"Status code {response.status_code}")
            return None

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
            self.parent_task = [i['id'] for i in pages['properties']['Parent-task']['relation']]
        
        if pages['properties']['Sub-tasks']['relation']:
            self.sub_tasks = [i['id'] for i in pages['properties']['Sub-tasks']['relation']]
        
        if pages['properties']['Assignee']['people']:
            self.assignee = [i['person']['email'] for i in pages['properties']['Assignee']['people']]
        
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

class Comments():
    version = "2022-06-28"

    def __init__(self, key):
        self.key = key
        self.header = {"Authorization": self.key,
                       "Notion-Version": self.version}

    def get_comments(self, page_id):
        endpoint = "https://api.notion.com/v1/comments?block_id={page_id}"
        response = requests.get(endpoint.format(page_id=page_id), headers=self.header)
        data = response.json()
        data = data['results']
        return data
    
    def get_latest_comment(self, data):
        if data:
            data.sort(key=lambda x: x['last_edited_time'], reverse=True)
            latest_comment = data[0]
            return latest_comment # return dictionary have latest last_edited_time

class CommentProperties():
    def __init__(self):
        self.last_edited_time = None
        self.created_by = None
        self.content = None
    
    def get_data(self, comment_obj):
        if comment_obj:
            self.content = comment_obj['rich_text'][0]['plain_text']
            self.created_by = comment_obj['created_by']['id']
            self.last_edited_time = comment_obj['last_edited_time']


class Pages():
    base_url = "https://api.notion.com/v1/pages"
    version = "2022-06-28"

    def __init__(self, database_id, notion_api_key):
        self.database_id = database_id
        self.notion_api_key = notion_api_key
        self.header = {"Authorization": self.notion_api_key,
                       "Notion-Version": self.version}

    def create_page(self, properties_data, children_data=None):
        if children_data:
            payload = {"parent": {"database_id": self.database_id}, "properties": properties_data, "children": children_data}
        else:
            payload = {"parent": {"database_id": self.database_id}, "properties": properties_data}
        
        res = requests.post(self.base_url, headers=self.header, json=payload)
        print(f"Status code: {res.status_code}")
        if res.status_code != 200:
            print(res.json()['message'])

        return res.json()

    def update_page(self, page_id, data):
        url = f"{self.base_url}/{page_id}"
        payload = {"properties": data}
        res = requests.patch(url, headers=self.header, json=payload)

        print(f"Status code: {res.status_code}")
        if res.status_code != 200:
            print(res.json()['message'])

        return res.json()
    
# --------------------------------------------------------------
# data noramilize to dict: {<ticket>:<status>}
def data_normalize_by_status(response_task, status_name=None):
    new_data_dict = {}

    for element in response_task:
        if element["properties"]["Task name"]["title"] != []:
            ticket = element["properties"]["Task name"]["title"][0]["plain_text"]
        else:
            continue

        if element["properties"]["Status"]["status"] is not None:
            if status_name is None:
                new_data_dict[ticket] = element["properties"]["Status"]["status"]["name"]
            elif status_name in element["properties"]["Status"]["status"]["name"]:
                new_data_dict[ticket] = element["properties"]["Status"]["status"]["name"]
        else:
            continue
    
    return new_data_dict

def reformat_time_series(time_series):
    # Example "2023-06-16T03:50:00.000Z" -> "2023-06-16 03:50:00.000"

    # Reformat time series
    time = datetime.fromisoformat(time_series.replace('Z', ''))
    return time