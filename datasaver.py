#!/usr/bin/env python
# -*- coding: utf-8 -*-

class MetaSingleton(type):
    _instances = {}

    def __call__(cls, chat_id, user_id, msg_id):
        data_id = f"{chat_id}_{user_id}_{msg_id}"
        if data_id not in cls._instances:
            cls._instances[data_id] = super(MetaSingleton, cls).__call__(chat_id, user_id, msg_id)
        return cls._instances[data_id]


class DataSaver:
    def __init__(self, chat_id, user_id, msg_id):
        self.chat_id = chat_id
        self.user_id = user_id
        self.msg_id = msg_id
        self.func = None
        self.data = []
        self.output_ok = "Исполнено"
        self.output_ok_data = {}
        self.output_ok_data_name = None
        self.output_ok_data_func = None
        self.output_cancel = "Операция отменена"

    def execute(self):
        print(self.output_ok_data)
        output = self.output_ok.format(**self.output_ok_data)
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
        if self.data:
            self.data.clear()


if __name__ == "__main__":
    saver = DataSaver("135", "975", "t34545")
    print(saver)
