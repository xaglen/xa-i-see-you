from datetime import datetime

SLACK_TOKEN="xoxb-######"

READ_CHANNEL_ID="C0########" # got from "About Channel" at the bottom
WRITE_CHANNEL_ID = READ_CHANNEL_ID
#WRITE_CHANNEL_ID="C0##########"
# use this for debugging - create a test channel, give the Slack bot access to it
# and post results there until you like the way things look

OPEN_SEASON = datetime(2021, 9, 11) # retrieve no posts earlier than this date
CLOSE_SEASON = datetime.now() # retrieve no posts later than this date
#close_season = datetime(2022, 6, 10)
SEASON_TITLE = "Academic Year 21-22" # can be anything
