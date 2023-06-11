from uuid import uuid4
from pprint import pprint
from datetime import datetime


class TempSorage():
    def __init__(self):
        self.__data = dict()
        self.__data_date = dict()
        self.__data_batchs = dict()
        self.__current_batch = []
        self.__current_chat = None
        self.__current_user = None
        self.__batching = False

    def __enter__(self):
        self.__batching = True
        self.__current_batch = []
        return self

    def __exit__(self, *_):
        self.__batching = False
        self.__current_batch = []
        self.__current_chat = None
        self.__current_user = None

    def batch(self, chat=None, user=None):
        self.__current_chat = chat
        self.__current_user = user
        return self

    def get(self, key, chat=None, user=None):
        chat = chat or self.__current_chat
        user = user or self.__current_user
        try:
            data = self.__data[chat][user][key]
        except KeyError:
            return
        return data

    def remove(self, key, chat=None, user=None):
        chat = chat or self.__current_chat
        user = user or self.__current_user
        if uuids := self.__data_batchs[key]:
            for uuid in uuids:
                del self.__data[chat][user][uuid]
                del self.__data_batchs[uuid]
        else:
            del self.__data[chat][user][key]

    def pop(self, key, chat=None, user=None):
        chat = chat or self.__current_chat
        user = user or self.__current_user
        data = self.get(key, chat, user)
        self.remove(key, chat, user)
        return data

    def add(self, value, chat=None, user=None):
        chat = chat or self.__current_chat
        user = user or self.__current_user
        uuid = str(uuid4())
        data_chat = self.__data[chat] = self.__data.get(chat, dict())
        data_user = data_chat[user] = data_chat.get(user, dict())
        data_user[uuid] = value
        self.__data_date[datetime.utcnow()] = uuid
        if self.__batching:
            self.__current_batch.append(uuid)
            self.__data_batchs[uuid] = self.__current_batch
        return uuid

    @property
    def data(self):
        return self.__data, self.__data_date, self.__data_batchs,

    @data.setter
    def data(self, value):
        self.__data = value


if __name__ == "__main__":
    temp_storage = TempSorage()
    with temp_storage.batch() as batch:
        batch.add("without chat and user")
        batch.add("without chat with user", user="user1")
    temp_storage.add("with chat without user", chat="chat1")
    temp_storage.add("with chat1 and user1", chat="chat1", user="user1")
    test_uuid = temp_storage.add("with chat2 and user2", chat="chat2", user="user2")
    pprint(temp_storage.data)
    pprint(temp_storage.get(test_uuid, chat="chat2", user="user2"))
