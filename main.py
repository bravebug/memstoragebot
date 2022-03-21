#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from random import choice
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from database import SqLiter
from config import TOKEN, SEPARATORS, ADD_SYNONYMS, RE_ITEM_FORMAT, BAD_WORDS, BAD_WORDS_ERROR


CANCEL_BUTTON = InlineKeyboardButton(text="Отмена", callback_data="cancel")


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


data = {}


def text_to_list(text: str, separators) -> list:
    text = text + separators[0]
    word = []
    for letter in text:
        if letter in separators:
            if word:
                yield "".join(word)
            word.clear()
        else:
            word.append(letter)


def cmd_add_item(update, context):
    db = SqLiter(update.message.chat_id)
    cmd, *items = text_to_list(update.message.text, SEPARATORS)
    if items:
        data_id = f"{update.message.chat_id}{update.message.from_user.id}"
        data[data_id] = items
        keyboard = [[]]
        max_button_len = 0
        for place_id, name in db.places():
            current_button_len = len(name)
            max_button_len = current_button_len if current_button_len > max_button_len else max_button_len
            if (len(keyboard[-1]) + 1) * max_button_len > 26:
                keyboard.append([])
                max_button_len = current_button_len
            keyboard[-1].append(InlineKeyboardButton(text=name, callback_data=place_id))
        keyboard.append([CANCEL_BUTTON])
        update.message.reply_text(str(data[data_id]), reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    else:
        update.message.reply_text("Бывает...")


def cmd_add_place(update, context):
    db = SqLiter(update.message.chat_id)
    cmd, *places = text_to_list(update.message.text, SEPARATORS)
    if places:
        db.add_places(places)
        output = "\n".join(places)
        update.message.reply_text(f'Добавлен{"ы" if len(places) > 1 else "о"} мест{"а" if len(places) > 1 else "о"} хранения: \n{output}')
    else:
        update.message.reply_text("Бывает...")


def cmd_dev_info(update, context):
    update.message.reply_text(str(update))


def cmd_help(update, context):
    help_text = (
        '/add_item *это* *вон-то* - добавляет *это* и *вон-то* на место хранения',
        '/add_place *полка* *ящик* - добавляет места хранения *полка* и *ящик*',
        # '/restart - !!!не вводить!!!',
        '/roll *я* *он* *ты* - бросает жребий между *я* *ты* и *он*',
        # '/dev_info - выводит информацию, достаточную для взлома вашей учётки',
        '/help - выводит эту справку'
    )
    update.message.reply_text("\n".join(help_text))


def cmd_restart_service(update, context):
    if update.message.from_user.id == 350999238:
        import subprocess

        update.message.reply_text("будет исполнено...")
        subprocess.run("sudo supervisorctl restart polochka".split())
    else:
        update.message.reply_text("Ай! Не делай так больше...")


def cmd_roll(update, context):
    cmd, *names = text_to_list(update.message.text, SEPARATORS)
    if names:
        update.message.reply_text(f'Победил: {choice(names)}')
    else:
        update.message.reply_text(f'Победила дружба!')


def cmd_start(update, context):
    update.message.reply_text('Меня зовут Полочка! Я могу запоминать что где лежит!')
    cmd_help(update, context)


def cmd_test(update, context):
    pass
    # cmd, *items = text_to_list(update.message.text, SEPARATORS)
    # if items:
        # keyboard = [[]]
        # for word in items:
            # keyboard[-1].append(InlineKeyboardButton(text=word, callback_data="Error"))
        # update.message.reply_text("OK:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    # else:
        # update.message.reply_text("Бывает...")
    

def print_place(update, context):
    db = SqLiter(update.message.chat_id)
    # db.add_places(places)
    update.message.reply_text(f'Добавлены места хранения: \n{output}')


def callback__(update, context):
    data_id = f"{update.callback_query.message.chat_id}{update.callback_query.from_user.id}"
    db = SqLiter(update.callback_query.message.chat_id)
    tmp_data = update.callback_query.data
    if tmp_data == "cancel":
        try:
            del data[data_id]
        except KeyError:
            pass
        # update.callback_query.message.reply_markup = None
        # print(dir())
    elif data.get(data_id):
        db.add(data[data_id], int(tmp_data))
        items = "\n".join(data[data_id])
        update.callback_query.message.reply_text(
            f'{items}\nдобавлены на место {db.placename_by_id(update.callback_query.data)[0]}'
        )
        del data[data_id]
    else:
        db.remove_item(tmp_data)
        update.callback_query.message.reply_text(f'{tmp_data}\nудалено')
    update.callback_query.message.delete() 


def reply(update, context):
    rem = "➖ Выдать"
    for word in ADD_SYNONYMS:
        if update.message.text.lower().startswith(word.lower()):
            if not word.endswith(" "):
                update.message.text = f"{word} {update.message.text.lstrip(word)}"
            cmd_add_item(update, context)
            break
    else:
        db = SqLiter(update.message.chat_id)
        # try:
        for search_word in set(text_to_list(update.message.text, SEPARATORS)):
            # search = db.search(search_word)
            # content = "\n".join([f'{num} = {place}' for (num, place) in search])
            # update.message.reply_text(f'Значит так:\n{content}')
            # search_set = sorted(set([x for x, _ in search]))
            search_set = [x[0] for x in db.search_items(search_word)]
            if 0 < len(search_set) <= 3:
                for item in search_set:
                    places = "\n".join([f'{"📦" * y} ➔ {x}' for x, y in db.search_places(item)])
                    markup = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text=f'{rem} {item}', callback_data=item)],
                        [CANCEL_BUTTON]
                    ])
                    update.message.reply_text(f'{item} расположен:\n{places}', reply_markup=markup)
            else:
                if search_set:
                    partial_match = "\n".join(search_set)
                    update.message.reply_text(f'Что-то из этого?:\n{partial_match}')
                else:
                    update.message.reply_text(f'...{choice(BAD_WORDS)}...')
        # except BadRequest:
            # update.message.reply_text(choice(BAD_WORDS_ERROR))


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    commands = {
        "add_item": cmd_add_item,
        "add_place": cmd_add_place,
        "dev_info": cmd_dev_info,
        "help": cmd_help,
        "restart": cmd_restart_service,
        "roll": cmd_roll,
        "start": cmd_start,
        # "test": cmd_test,
    }
    for command, func in commands.items():
        dp.add_handler(CommandHandler(command, func))
    dp.add_handler(CallbackQueryHandler(callback__))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
