from api import update_all

for message in update_all():
    print(message.chat.title + ': ' + str(message.chat.id))
