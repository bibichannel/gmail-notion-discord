## Code integrated gmail + notion + discord
### Flow
1. Get the subject of new email with conditions we want
2. Read subject ->  filter email -> move to label -> read the email (with my conditons __Ticket__)
3. With a ticket we can check in database of notion 
4. Generate message we want and send to discord via webhook and mention to the member

### Technology used
- Notion API
- Gmail google API 
- Discord webhook

### After pull, we need create files:
* __credentials.json__ (credentials app desktop of gmail api)
* __credentials.py__
```python
KEY_NOTION = ""
DATABASE_ID_NOTION  = ""
WEBHOOK_TOKEN_DISCORD = ""
```
* __dictionaries.py__ (**user** of notion and **user id** of discord)
```python
user_dict = {
    "Trung": "612976675583688710"
}
```
