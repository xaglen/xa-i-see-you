"""
Generates an I See You summmary for Slack.
"""
#import json
#import pprint
import logging
import sys, os
import re
import time
from collections import Counter
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

#from systemd.journal import JournaldLogHandler

import settings


def fetch_candidates():
    candidates = []
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', settings.SCOPES)
    else:
        creds = service_account.Credentials.from_service_account_file(
            settings.SERVICE_ACCOUNT_FILE, scopes=settings.SCOPES)
        try:
             service = build('sheets', 'v4', credentials=creds)
             # Call the Sheets API
             sheet = service.spreadsheets()
             result = sheet.values().get(spreadsheetId=settings.GOOGLE_SPREADSHEET_ID,
                                         range=settings.BIRTHDAY_RANGE_NAME).execute()
             values = result.get('values', [])
        except:
            pass

        if not values:
            print('No data found.')
            return candidates

        for value in values:
            #print(value[2]) # format is First Name, Last Name, Slack ID, Birthday
            candidates.append(value[2])

    return candidates

def fetch_activity(client = None, channel=None, open_season=None, close_season=None):
    """
    Retrieves posts from slack channel.

    Retrieves all posts from the given slack channel between open_season and close_season.
    """
    try:
        #data = json.loads(request.body.decode('utf-8'))
        result = client.conversations_history(
                channel=channel,
                oldest=open_season.timestamp(),
                latest=close_season.timestamp())
        conversation_history = []
        conversation_history += result['messages']
        ts_list = [item['ts'] for item in conversation_history]
        last_ts = ts_list[:-1]
        while result['has_more']:
            result = client.conversations_history(
                channel=channel,
                cursor=result['response_metadata']['next_cursor'],
                latest=last_ts,
                oldest=open_season.timestamp())
            conversation_history+=result['messages']
         #logger.info(repr(data))
    except SlackApiError as e:
        print(repr(e))
        return conversation_history

    return conversation_history

def generate_message(season_title, tally):
    """
    Creates BlockKit message to post to Slack.
    """
#    close_season=close_season-timedelta(seconds=1) #moves back from midnight the following day

    season_short_title = season_title.split(' ', 1)[0]

    title = "Overlooked in I-See-You: "+ season_title

    slack_message = ""

    for person in overlooked:
        slack_message += person

    slack_message = '''
	[
        {"type": "section",
        "text": {
        "type": "mrkdwn",
        "text": 
        '''
    slack_message+= '"*'+title+'*"'
    slack_message+= '''
        }
        },
        {"type": "divider"},
        {"type": "section",
        "text": {
        "type":"mrkdwn",
        "text":
        '''
    slack_message+='"'

    slack_message+='''
        }
        },
        '''
    slack_message+= '''
        {"type": "section",
        "text": {
        "type": "mrkdwn",
        "text": ":camera_with_flash: *The Snipers*"}},
        {"type":"section",
        "text": {
        "type": "mrkdwn",
        '''
    slack_message+='"text": "'
    for name in leaderboard:
        slack_message+="<@"+name[0]+'> *'+str(name[1])+'* '
    slack_message+='"}},'

    if len(tally['stealthy'])>0:
        slack_message += '''
            {"type": "divider"},
            {"type": "section",
            "text": {
            "type": "mrkdwn",
            "text": ":ninja2: *The Sneakiest*"}},
            {"type":"section",
            "text": {
            "type": "mrkdwn",
            '''
        slack_message+='"text": "'
        for name in ninjas:
            slack_message+="<@"+name[0]+'> *'+str(name[1])+'* '
        slack_message+='"}},'

    slack_message += '''
        {"type": "divider"},
        {"type": "section",
        "text": {
        "type": "mrkdwn",
        "text": ":duck: *The Most Sniped*"}},
        {"type": "section",
        "text": {
        "type": "mrkdwn",
        '''
    slack_message+='"text": "'

    for name in ducks:
        slack_message+="<@"+name[0]+'> *'+str(name[1])+'* '
    slack_message+='"}}'

    slack_message += ']'

    return slack_message

def main():
    """
    Generates a post for Slack based upon history in the channel.
    """
    start_time = time.time()

    logger = logging.getLogger(__name__)
    #journald_handler = JournaldLogHandler()
    #journald_handler.setFormatter(logging.Formatter('[%(levelname)s] %message)s'))
    #logger.addHandler(journald_handler)
    logger.setLevel(logging.INFO)

    open_season = settings.OPEN_SEASON
    close_season = settings.CLOSE_SEASON
    season_title = settings.SEASON_TITLE
    season_short_title = settings.SEASON_SHORT_TITLE

    client = WebClient(token=settings.SLACK_TOKEN)

    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(conversation_history)
    #exit()
    #print(conversation_history)

    overlooked=fetch_candidates()

    print("Potential: {}".format(len(overlooked)))
    print("Type of items in the list: {}".format(type(overlooked[0])))

    conversation_history = fetch_activity(
            client,
            settings.READ_CHANNEL_ID,
            settings.OPEN_SEASON,
            settings.CLOSE_SEASON
            )
    for message in conversation_history:
        ts = int(message['ts'].split('.')[0])
        #timestamp = datetime.fromtimestamp(ts)
        if open_season.timestamp() <= ts < close_season.timestamp():
            if 'user' in message and 'files' in message:
                try:
                    overlooked.remove(message['user'])
                except:
                    print(message['user'])
            if 'text' in message:
                if '@' in message['text']:
                    regex = r'\<\@(.*?)\>'
                    hits = re.findall(regex, message['text'])
                    for hit in hits:
                        try:
                            overlooked.remove(hit)
                        except:
                            #print(hit)
                            pass
                #else was a bot

    print ("Overlooked: {}".format(len(overlooked)))
    print("Type of hits attempting to remove from the list: {}".format(type(hit)))
    print("Type of users attempting to remove from the list: {}".format(type(message['user'])))


    exit()
    slack_message = generate_message(season_title, tally)

    print("JSON:\n"+str(slack_message))

    #data = json.loads(slack_message)

    #print(str(data))

    try:
        title = "I See You Leaderboard: "+ season_title
        resp=client.chat_postMessage(
            channel=settings.WRITE_CHANNEL_ID,
            blocks=slack_message,
            text=title
        )
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        message = "\nSlackApiError: Slack error posting tally\n"
        message += " "+repr(e)+"\n"
        message += " "+repr(e.response)+"\n"
        logger.info(message)
        print(message)
        print(e)
    except TypeError as e:
        message = "TypeError posting tally: "+ repr(e)
        logger.info(message)
        #    print(message+": "+repr(e))
    except:# pylint: disable=bare-except
        e = repr(sys.exc_info()[0])
        message = "Error posting tally: "+ e
        logger.info(message)

    try: # pylint: disable=bare-except
        print(message)
    except: # pylint: disable=bare-except
        pass

    execution_time = (time.time() - start_time)
    print('Execution time in seconds: ' + str(execution_time))

if __name__ == '__main__':
    main()

