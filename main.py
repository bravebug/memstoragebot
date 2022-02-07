#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from random import choice
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database import SqLiter
from datasaver import DataSaver
import devtools


TOKEN = os.environ["TOKEN"]
SEPARATORS = r" ,/;\|"
BAD_WORDS = ("Чип и Дейл!", "Нет парковки!", "Следуй за белым кроликом...")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start_command(update, context):
    update.message.reply_text('Меня зовут Полочка! Я могу запоминать где и что лежит!')
    help_command(update, context)

def help_command(update, context):
    update.message.reply_text('Тут должна быть справка, но её пока нет!')

def dev_info_command(update, context):
    update.message.reply_text(str(update))

def add_command(update, context):
    # print("add_command:", update.message, "\n\n", dir(update.message), "\n\n")
    db = SqLiter(update.message.chat_id)
    data_text = update.message.text.split(" ", 1)[1]
    for sep in SEPARATORS:
        if sep in data_text:
            data_text = data_text.replace(sep, ";")
    print(
        "add_command",
        update.message.chat_id,
        update.message.from_user.id)
    data = DataSaver(
        update.message.chat_id,
        update.message.from_user.id,
        [x.strip() for x in data_text.split(";") if x]
    )
    print(id(data))
    keyboard = []
    counter = 1
    for name, place_id in db.places():
        if counter % 3:
            keyboard.append([])
        keyboard[-1].append(InlineKeyboardButton(text=name, callback_data=place_id))
        counter += 1
    update.message.reply_text(str(data.data), reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

def callback__(update, context):
    # print("callback__:", context.message_id, "\n\n", dir(context))
    print(
        "callback__",
        update.callback_query.message.chat_id,
        update.callback_query.from_user.id)
    data = DataSaver(
        update.callback_query.message.chat_id,
        update.callback_query.from_user.id
    )
    print(id(data))
    # print(data.data)
    db = SqLiter(update.callback_query.message.chat_id)
    update.callback_query.message.reply_text(f'{data.data}\n{update.callback_query.data}: {type(update.callback_query.data)}')
    del data
    update.callback_query.message.delete()

def reply(update, context):
    # print("reply:", dir(update.message.from_user.id))
    # update.message.delete()
    # print(update['message'])
    # print(update.message)
    db = SqLiter(update.message.chat_id)
    search = db.search(update.message.text)
    if search:
        content = "\n".join([f'{num} = {place}' for (num, place) in search])
        update.message.reply_text(f'Значит так:\n{content}')
    else:
        update.message.reply_text(f'{choice(BAD_WORDS)}!!!')


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    commands = {
        "start": start_command,
        "help": help_command,
        "dev_info": dev_info_command,
        "add": add_command,
    }
    for command, func in commands.items():
        dp.add_handler(CommandHandler(command, func))
    dp.add_handler(CallbackQueryHandler(callback__))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
