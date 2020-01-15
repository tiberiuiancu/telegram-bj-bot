from api import update_all

for message in update_all():
    if message.chat.title is not None:
        print(message.chat.title + ': ' + str(message.chat.id))
    else:
        print('Private message from ' + str(message.chat.id))
