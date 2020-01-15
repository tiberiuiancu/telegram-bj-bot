class User:
    def __init__(self, id=None, first_name=None, last_name=None, username=None, json_obj=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username

        if json_obj is not None:
            self.from_json(json_obj)


    def from_json(self, obj):
        self.id = obj['id']
        self.first_name = obj['first_name']
        if 'last_name' in obj:
            self.last_name = obj['last_name']
        if 'username' in obj:
            self.username = obj['username']


class Chat:
    def __init__(self, id=None, type=None, title=None, json_obj=None):
        self.id = id
        self.type = type
        self.title = title

        if json_obj is not None:
            self.from_json(json_obj)

    def from_json(self, obj):
        self.id = obj['id']
        self.type = obj['type']
        if 'title' in obj:
            self.title = obj['title']


class Message:
    def __init__(self, id=None, date=None, chat=None, text=None, user=None, json_obj=None):
        self.id = id
        self.date = date
        self.chat = chat
        self.text = text
        self.user = user

        if json_obj is not None:
            self.from_json(json_obj)

    def from_json(self, obj):
        self.id = obj['message_id']
        self.date = int(obj['date'])
        self.chat = Chat(json_obj=obj['chat'])
        if 'from' in obj:
            self.user = User(json_obj=obj['from'])
        if 'text' in obj:
            self.text = obj['text']

    def __str__(self):
        ret = 'id: ' + str(self.id) + ', date: ' + str(self.date)
        if self.chat.title is not None:
            ret += ', chat: ' + self.chat.title
        else:
            ret += ', char_id: ' + str(self.chat.id)

        if self.user is not None:
            if self.user.username is not None:
                ret += ', from: ' + self.user.username
            else:
                ret += ', from: ' + self.user.first_name

        if self.text is not None:
            ret += ', "' + self.text + '"'

        return ret

