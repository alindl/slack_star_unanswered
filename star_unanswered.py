#!/usr/bin/python3
""" Goes through all channels,
looks for unanswered threads (reply or emoji)
and saves them if not already saved
"""

import argparse
import inspect
from slackclient import SlackClient

PARSER = argparse.ArgumentParser(description='Star unanswered threads.')
PARSER.add_argument('user', type=str, choices=['panda', 'erika'],
                    help="Your name dummy.")
PARSER.add_argument('slack_token', metavar='slack_token', type=str,
                    help="The Slack token you can get from \
                            https://api.slack.com/custom-integrations/legacy-tokens")

ARGS = PARSER.parse_args()
SLACK_BOT_TOKEN = ARGS.slack_token
USER = ARGS.user

def get_id():
    """ Getting the correct ID for the specific user """
    if USER.lower() == 'erika':
        return 'UPA1W86N8'
    if USER.lower() == 'panda':
        return 'UNXCVUYHY'
    return ''

def get_channels(self):
    """
    Gets the list of all channels, returns the ids

    API CALL conversations.list has a limit of 20 per minute
    It is used used once
    """
    res = self.api_call("conversations.list")
    channels = []
    if not res.get('ok'):
        print(inspect.currentframe().f_code.co_name)
        return False
    json_list = res.get('channels')
    for ch_info in json_list:
        channels.append((ch_info.get('id'), ch_info.get('name')))
    return channels


def get_threads(self, ch_id):
    """
    Gets the list of the timestamps of all threads of a specific channel
    If there is no thread, it takes the 'normal' timestamp

    API CALL conversations.history has a limit of 50 per minute
    It is used about once per channel (100 messages per page)
    """
    res = self.api_call("conversations.history", channel=ch_id[0])
    timestamps = set()

    if not res.get('ok'):
        print(inspect.currentframe().f_code.co_name)
        return False

    json_list = res.get('messages')
    for msg in json_list:
        if msg.get('thread_ts') is not None:
            timestamps.add(msg.get('thread_ts'))
        else:
            timestamps.add(msg.get('ts'))
    while res.get('has_more'):
        next_cursor = res.get('response_metadata').get('next_cursor')
        res = self.api_call("conversations.history", channel=ch_id[0], cursor=next_cursor)
        if not res.get('ok'):
            print(inspect.currentframe().f_code.co_name)
        else:
            json_list = res.get('messages')
            for msg in json_list:
                if msg.get('thread_ts') is not None:
                    timestamps.add(msg.get('thread_ts'))
                else:
                    timestamps.add(msg.get('ts'))
    return timestamps

def get_last_reply(self, ch_id, thread_ts):
    """
    Gets the last reply from the reply-tree (needs channel + timestamp)

    API CALL conversations.replies has a limit of 50 per minute
    It is used about once per thread
    """
    res = self.api_call("conversations.replies", channel=ch_id[0], ts=thread_ts, limit=1)
    if not res.get('ok'):
        print(inspect.currentframe().f_code.co_name)
        return False
    if len(res.get('messages')) > 1:
        return res.get('messages')[1]
    return res.get('messages')[0]


def check_yourself_before_you_wreck_yourself(reply):
    """
    Checks if the reply was by me, is uninteresting, got a reaction or is already saved.
    """
    if reply.get('user') == get_id():
        return False
    if reply.get('subtype') == 'channel_join':
        return False
    if reply.get('reactions') is not None:
        return False
    if reply.get('is_starred') is not None:
        if reply.get('is_starred'):
            return False
    return True

def add_star(self, ch_id, reply_ts):
    """
    Puts a star on it (needs channel + timestamp to)

    API CALL conversations.replies has a limit of 20 per minute
    It is used depending on how many bananas are washed.
    """
    res = self.api_call("stars.add", channel=ch_id[0], timestamp=reply_ts)
    if not res.get('ok'):
        if res.get('error') == 'already_starred':
            return False
        print(inspect.currentframe().f_code.co_name)
        print(res)
        return True
    return False


# Initialize the connection to the slackbot
SLACK_CLIENT = SlackClient(SLACK_BOT_TOKEN)
CHANNELS = get_channels(SLACK_CLIENT)
if CHANNELS:
    for channel in CHANNELS:
        if channel == "CR4REP6E4":
            print('skipped')
            continue
        print("Checking: ", channel[1])
        THREADS = get_threads(SLACK_CLIENT, channel)
        for thread in THREADS:
            last_reply = get_last_reply(SLACK_CLIENT, channel, thread)
            if check_yourself_before_you_wreck_yourself(last_reply):
                if add_star(SLACK_CLIENT, channel, last_reply.get('ts')):
                    print(last_reply)
