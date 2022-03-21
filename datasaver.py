#!/usr/bin/env python
# -*- coding: utf-8 -*-

class MetaSingleton(type):
    _instances = {}

    def __call__(cls, chat_id, user_id, *args, **kwargs):
        data_id = f"data_{chat_id}_{user_id}"
        if data_id not in cls._instances:
            cls._instances[data_id] = super(MetaSingleton, cls).__call__(chat_id, user_id, *args, **kwargs)
        return cls._instances[data_id]


class DataSaver(metaclass=MetaSingleton):
    def __init__(self, chat_id, user_id, data=False):
        if data:
            self.data = data


if __name__ == "__main__":
    saver = DataSaver("135", "975", data="Spam and Eggs")
    print(saver.data)
