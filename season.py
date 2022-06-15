"""
Generates an I See You summmary for Slack.
"""
#import json
#import pprint
import logging
import sys
import re
import time
from datetime import datetime, timedelta
from collections import Counter
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
#from systemd.journal import JournaldLogHandler

import settings

def fetch_snipes(client = None, channel=None, open_season=None, close_season=None):
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

    leaderboard = Counter(tally['posters']).most_common(3)
    ninjas = Counter(tally['stealthy']).most_common(3)
    ducks = Counter(tally['sniped']).most_common(3)

    print("Leaderboard: " + str(leaderboard))
    print("Ninjas: " + str(ninjas))
    print("Ducks: " + str(ducks))

    title = "I See You Leaderboard: "+ season_title

    slack_message = '''
        [{"type": "section",
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
    if tally['num_snipes'] > 0:
        if tally['dubious_snipes']==0:
            slack_message+='"*{}* total confirmed snipes in {}: (:dart:)'.format(
                    tally['num_snipes'], season_title
                    )
        else:
            slack_message+=('"*{}* total confirmed snipes in {}:'
                            '(:dart:), including *{}* dubious snipes'
                            '(:waldo-6066: :magnify:)').format(
                                tally['num_snipes'], season_title, tally['dubious_snipes']
                                )
        if tally['fake_snipes']>0:
            slack_message+= (r"\XNEWLINE _and also {} rejected snipes"
                             "(:waldo-6066: or :magnify: instead of :dart:)_").format(
                                str(tally['fake_snipes'])
                                )
        slack_message = slack_message.replace('XNEWLINE','n')
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

    slack_token=settings.SLACK_TOKEN

    open_season = settings.OPEN_SEASON
    close_season = settings.CLOSE_SEASON
    season_title = settings.SEASON_TITLE

    client = WebClient(token=slack_token)

    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(conversation_history)
    #exit()
    #print(conversation_history)

    tally={}
    tally['posters']=[]
    tally['stealthy']=[]
    tally['sniped']=[]
    tally['num_snipes']=0
    tally['dubious_snipes']=0
    tally['fake_snipes']=0

    conversation_history = fetch_snipes(
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
                if 'reactions' in message:
                    for reaction in message['reactions']:
                        if 'dart' in reaction['name']:
                            tally['num_snipes'] = tally['num_snipes']+1
                            tally['posters'].append(message['user'])
                            if 'waldo' in reaction['name'] or 'mag' in reaction['name']:
                                tally['dubious_snipes'] = tally['dubious_snipes'] +1
                        elif 'waldo' in reaction['name'] or 'mag' in reaction['name']:
                            tally['fake_snipes'] = tally['fake_snipes']+1
                        if 'ninja' in reaction['name']:
                            tally['stealthy'].append(message['user'])
            if 'text' in message:
                if '@' in message['text']:
                    regex = r'\<\@(.*?)\>'
                    hits = re.findall(regex, message['text'])
                    for hit in hits:
                        tally['sniped'].append(hit)
                #else was a bot


    slack_message = generate_message(season_title, tally)

    print(str(slack_message))

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
        message = "Slack error posting tally"
        message += " "+repr(e)
        message += " "+repr(e.response)
        logger.info(message)
        #        print(message)
        #        print(e)
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

# Here's our payoff idiom!
if __name__ == '__main__':
    main()
