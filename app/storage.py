from uuid import uuid4
from pprint import pprint
from datetime import datetime


class DataNotFoundError(Exception):
    """Raised when there is no data in the storage"""

    def __init__(self, message="There is no data in the storage"):
        self.message = message
        super().__init__(self.message)


class InstanceIdMismatchError(Exception):
    """Raised when an invalid chat ID is provided"""

    def __init__(self, message="Invalid chat ID"):
        self.message = message
        super().__init__(self.message)


class UserIdMismatchError(Exception):
    """Raised when an invalid user ID is provided"""

    def __init__(self, message="Invalid user ID"):
        self.message = message
        super().__init__(self.message)


class TempStorage():
    def __init__(self):
        self.__data = dict()
        self.__current_ids_batch = set()
        self.__current_chat = None
        self.__current_user = None
        self.__batching = False

    def __enter__(self):
        self.__batching = True
        self.__current_ids_batch = set()
        return self

    def __exit__(self, *_):
        self.__batching = False
        self.__current_ids_batch = set()
        self.__current_chat = None
        self.__current_user = None

    def batch(self, chat=None, user=None):
        self.__current_chat = chat
        self.__current_user = user
        return self

    def add(self, data, chat=None, user=None):
        chat = chat or self.__current_chat
        user = user or self.__current_user
        uid = str(uuid4())
        self.__data[uid] = dict(
            data=data,
            chat=chat,
            user=user,
            created=datetime.utcnow(),
        )
        self.__current_ids_batch.add(uid)
        self.__data[uid].update(
            batch=self.__current_ids_batch
        )
        if not self.__batching:
            self.__current_ids_batch = set()
        return uid

    def get(self, key, chat=None, user=None):
        chat = chat or self.__current_chat
        user = user or self.__current_user
        if not (dataset := self.__data.get(key)):
            raise DataNotFoundError()
        else:
            if not dataset.get('chat') == chat:
                raise InstanceIdMismatchError()
            elif not dataset.get('user') == user:
                raise UserIdMismatchError()
            else:
                return dataset.get('data')

    def remove(self, key):
        dataset = self.__data.get(key)
        if uids := dataset.get('batch'):
            for uid in uids:
                del self.__data[uid]

    def pop(self, key, chat=None, user=None):
        chat = chat or self.__current_chat
        user = user or self.__current_user
        data = self.get(key, chat, user)
        if data:
            self.remove(key)
        return data

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        self.__data = value


if __name__ == "__main__":
    pass
