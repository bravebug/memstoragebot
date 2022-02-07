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
    base = SqLiter("-1001565062242")
    # base.add_place("коробка №1")
    # base.add_place("полка сверху")
    # base.add_place("полка снизу")
    # base.add_place("хорошая полка")
    # base.add("7658432", 3)
    # base.add("8567545", 1)
    # base.add("5554667", 2)
    # base.add("5675676", 4)
    # base.add("4657767", 3)
    # base.add("9247555", 1)
    # base.add("2323444", 2)
    # base.add("5675656", 4)
    print(base.places())
