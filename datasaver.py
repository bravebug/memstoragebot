#!/usr/bin/env python
# -*- coding: utf-8 -*-

class MetaSingleton(type):
    _instances = {}

    def __call__(cls, chat_id, user_id, msg_id, item_id=None):
        data_id = f"{chat_id}_{user_id}_{msg_id}_{item_id}"
        if data_id not in cls._instances:
            cls._instances[data_id] = super(MetaSingleton, cls).__call__(chat_id, user_id, msg_id, item_id)
        return cls._instances[data_id]


class DataSaver(metaclass=MetaSingleton):
    def __init__(self, chat_id, user_id, msg_id, item_id):
        self.chat_id = chat_id
        self.user_id = user_id
        self.msg_id = msg_id
        self.item_id = item_id
        self.func = None
        self.data = None
        self.output_ok = None
        self.output_cancel = None

    def save(self, func, data=list(), output_ok="Исполнено", output_cancel="Операция отменена"):
        self.func = func
        self.data = data
        self.output_ok = output_ok
        self.output_cancel = output_cancel

    def execute(self):
        output = self.output_ok
        self.func(*self.data)
        self.clear()
        return output

    def __str__(self):
        output = "\n    ".join(f'{str(attr)} = {self.__getattribute__(attr)}' for attr in dir(self) if not attr.startswith("__"))
        return f'<DataSaver:\n    {output}\n>\n'

    def reset(self):
        output = self.output_cancel
        self.clear()
        return output

    def clear(self):
        self.func = None
        self.data.clear()


if __name__ == "__main__":
    saver = DataSaver("135", "975", "t34545")
    saver.func = str.lower
    saver.data = "SgGdFgfG"
    print(saver.chat_id, saver.data)
    print(saver.func(saver.data))
    print(dir(saver))
    pupka = DataSaver("135", "975", "5534")
    print(pupka)
    print(saver.chat_id, saver.data)
    print(saver.func(saver.data))
    print(dir(saver))
