from jira import JIRA
from datetime import datetime
import pytz

class Jira():

    def __init__(self, server, username, pat):
        self.server = server
        self.username = username
        self.pat = pat
        self.jira = JIRA(server=self.server, basic_auth=(self.username, self.pat))
    
    def get_issue(self, issue):
        return self.jira.issue(str(issue), expand='changelog')
    
    def get_latest_comment(self, issue):
        comments = self.jira.comments(issue)
        if comments:
            latest_comment = sorted(comments, key=lambda comment: comment.created)[-1]
            return latest_comment
        else:
            return None
    
    def get_latest_history(self, issue):
        hitories = issue.changelog.histories
        if hitories:
            latest_history = sorted(hitories, key=lambda history: history.created)[-1]
            return latest_history
        else:
            return None

def reformat_time_series(time_series):
    # example: 2023-06-19T16:47:06.138+0900

    time_obj = datetime.strptime(time_series[:-5], '%Y-%m-%dT%H:%M:%S.%f')

    # Get timezone
    time_zone = int(time_series[-5:]) / 100
    time_obj = time_obj.replace(tzinfo=pytz.FixedOffset(time_zone*60))

    # Convert to UTC+0
    utc_tz = pytz.timezone('UTC')
    utc_time = time_obj.astimezone(utc_tz)

    # Reformat time series
    time = utc_time.strftime('%Y-%m-%d %H:%M:%S.%f')

    return time
