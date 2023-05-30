#!/usr/bin/env python
from aiogram.types import InlineKeyboardButton
import unicodedata
from uuid import uuid4


def add_action_button(kb, storage, action, button_text, back_msg, chat_id, from_id):
    uuid = str(uuid4())
    kb.append([InlineKeyboardButton(text=button_text, callback_data=uuid)])
    data = (
        action,
        back_msg,
    )
    storage.update_data(chat=chat_id, user=from_id, data=data)


def remove_extra_spaces(text: str) -> str:
    """Clears the text from extra spaces"""
    return " ".join(text.split())


def remove_accents(text: str) -> str:
    """Clears the text from unicode combining chars"""
    return "".join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))


def split_asterisk_and_sharp(entry: str) -> (str, int, str):
    try:
        entry, comment = entry.split("#", maxsplit=1)
    except ValueError:
        comment = None
    try:
        entry, quantity_text = entry.split("*", maxsplit=1)
    except ValueError:
        quantity_text = None
    return entry, quantity_text, comment


if __name__ == "__main__":
    print(remove_extra_spaces("Привет\n  fdsdl"))
    print(remove_accents('kožušček'))
