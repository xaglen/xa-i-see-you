# xa_i_see_you

Tallies photos posted to the xa-i-see-you channel. 

# Methodology

The script retrieves all messages between OPEN_SEASON and CLOSE_SEASON in the #xa-i-see-you Slack channel. If the message has a file attachment, the script ananalyzes the tags and emoji reactions to determine how to tally it. Anything with a target emoji is counted as a successful snipe. Anything with a ninja emoji is counted as a stealthy snipe. Anything with a magnifying glass or a Waldo emoji is treated as disputed (if it has both a target and Waldo, for example) or rejected (if it has only skeptical emoji reactons).

# Limitations
- The script doesn't handle cases where someone posts a photo and then makes a new post with the tag.
- The script  makes no attempt to prevent someone from gaming the system by reacting to their own posts.
- The script doesn't handle variant emojis well.
