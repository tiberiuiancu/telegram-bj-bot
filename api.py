import requests
import json
from entities import Message
import time

with open('api_token.txt', 'r') as f:
    bot_token = f.readline().strip()


last_call = None
remove_keyboard_markup = json.dumps({'remove_keyboard': True})


def send_message(message, chat_id, reply_id=None, reply_markup=None, msg_pause=1):
    if type(message) != str or type(chat_id) != int:
        return False

    # check if msg_pause time has paused since the last message sent; used to not spam the users
    global last_call
    curr_time = time.time()
    if last_call is not None and msg_pause and curr_time - last_call < msg_pause:
        time.sleep(1 - curr_time + last_call)
    last_call = curr_time

    url = "https://api.telegram.org/bot" + bot_token + "/sendMessage?chat_id=" + str(chat_id) + "&text=" + message + '&disable_web_page_preview=true'

    if reply_id is not None:
        url += '&reply_to_message_id=' + str(reply_id)

    if reply_markup is not None:
        url += '&reply_markup=' + reply_markup

    response = requests.get(url)

    if response.text.startswith('{"ok":true'):
        return True

    return False


def remove_custom_keyboards(chat_id, msg='removing keyboards'):
    if type(chat_id) != int:
        return False

    return send_message(msg, chat_id, reply_markup=json.dumps(remove_keyboard_markup))


def filter_message(message, chat_id):
    try:
        if chat_id is not None and message.chat.id != chat_id:
            return False

        return True
    except:
        return False


def update(chat_id=None, offset=None):
    if offset is None:
        url = "https://api.telegram.org/bot" + bot_token + "/getUpdates"
    else:
        url = "https://api.telegram.org/bot" + bot_token + "/getUpdates?offset=" + str(offset)

    response = requests.get(url)

    if not response.text.startswith('{"ok":true'):
        return False

    json_obj = json.loads(response.text)['result']

    to_return = []
    for result in json_obj:
        current = None
        if 'message' in result:
            current = Message(json_obj=result['message'])
        if 'edited_message' in result:
            current = Message(json_obj=result['edited_message'])

        if current is not None and filter_message(current, chat_id):
            to_return.append(current)

    if len(json_obj):
        return int(json_obj[-1]['update_id']) + 1, to_return
    else:
        return offset, to_return


def update_all(chat_id=None, offset=None):
    # update all messages and mark them as read on the telegram server
    to_ret = []
    offset, msgs = update(chat_id=chat_id, offset=offset)
    while len(msgs) != 0:
        to_ret += msgs
        offset, msgs = update(chat_id=chat_id, offset=offset)

    return to_ret
