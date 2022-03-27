#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from random import choice
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Document
from telegram.error import BadRequest
from database import SqLiter
from config import TOKEN, SEPARATORS, SYNONYMS, RE_ITEM_FORMAT, BAD_WORDS, BAD_WORDS_ERROR, ICONS


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


BUTTON_OK = InlineKeyboardButton(text="ОК", callback_data="accept")
BUTTON_CANCEL = InlineKeyboardButton(text="Отмена", callback_data="cancel")
KEYBOARD_OK_CANCEL = [BUTTON_OK, BUTTON_CANCEL]

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


def iterable_to_text(data: (list, tuple), separators='", "') -> str:
    return f'"{separators.join(data)}"'


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
        keyboard.append([BUTTON_CANCEL])
        update.message.reply_text(str(data[data_id]), reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    else:
        update.message.reply_text("Нужно ввести название хотя бы одного места хранения")


def cmd_del_item(update, context):
    db = SqLiter(update.message.chat_id)
    cmd, *items = text_to_list(update.message.text, SEPARATORS)
    if items:
        items = sorted(set(items))
        for item in items:
            # update.message.reply_text("TEST", reply_markup=InlineKeyboardMarkup(inline_keyboard=KEYBOARD_OK_CANCEL))
            db.remove_item(item)
        # update.message.reply_text(str(data[data_id]), reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    else:
        update.message.reply_text("Нужно ввести название хотя бы один заказ")


def cmd_add_place(update, context):
    db = SqLiter(update.message.chat_id)
    _, *places = text_to_list(update.message.text, SEPARATORS)
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
        "Меня зовут Полочка! Я могу запомнить что и где лежит!",
        "\n"
        "Управляй мной такими командами:",
        f'/add_place МЕСТО … - добавляет МЕСТО. Cинонимы: {iterable_to_text(SYNONYMS["cmd_add_place"])}',
        f'/add_item ОБЪЕКТ … - добавляет ОБЪЕКТ на МЕСТО. Cинонимы: {iterable_to_text(SYNONYMS["cmd_add_item"])}',
        # '/restart - !!!не вводить!!!',
        f'/csv - экспортирует базу. Cинонимы: {iterable_to_text(SYNONYMS["cmd_csv"])}',
        f'/roll ОРЁЛ РЕШКА … - бросает жребий. Cинонимы: {iterable_to_text(SYNONYMS["cmd_roll"])}',
        # '/dice - выбрасывает 2 игральные кости',
        # '/dev_info - выводит информацию, достаточную для взлома вашей учётки',
        '/help - выводит эту справку',
        "\n",
        "С более подробной информацией Вы можете ознакомится на странице проекта: https://github.com/bravebug/memstoragebot",
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
    cmd_help(update, context)


def cmd_csv(update, context):
    db = SqLiter(update.message.chat_id)
    fields_all = db.all()
    if fields_all:
        from csv import writer, QUOTE_ALL
        from io import StringIO
        from datetime import datetime
        temp_file = StringIO()
        fwriter = writer(temp_file, dialect="excel", delimiter=";", quotechar='"', quoting=QUOTE_ALL)
        fwriter.writerow(("Запись", "Место"))
        for row in fields_all:
            fwriter.writerow(row)
        temp_file.seek(0)
        date = datetime.now()
        context.bot.send_document(
            chat_id=update.message.chat.id,
            document=temp_file,
            filename=f'memstoragebot--{date.strftime("%Y-%m-%d--%H-%M")}.csv'
        )
        temp_file.close()
        del writer, QUOTE_ALL, StringIO, datetime
    else:
        update.message.reply_text("нет записей")


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


def cmd_dice(update, context):
    """выбрасывает игральные кости"""
    _, *nums = text_to_list(update.message.text, SEPARATORS)
    if not nums:
        nums = ("2", )
    dices = "⚀⚁⚂⚃⚄⚅"
    counter = 0
    for num in nums:
        if num.isdigit:
            num = int(num)
            if num > 20 or counter > 3:
                update.message.reply_text('🤖 Error!!! 💥')
            else:
                output = "".join(choice(dices) for _ in range(num))
                counter += 1
                update.message.reply_text(f'{output}')


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
    rem = "Выдать"
    flag = False
    for operation in SYNONYMS:
        if flag:
            break
        for synonym in SYNONYMS[operation]:
            if update.message.text.lower().startswith(synonym.lower()):
                if not synonym.endswith(" "):
                    update.message.text = f"{synonym} {update.message.text.lstrip(synonym)}"
                import __main__
                __main__.__dict__.get(operation)(update, context)
                # cmd_add_item(update, context)
                flag = True
                break
    if not flag:
        db = SqLiter(update.message.chat_id)
        try:
            for search_word in set(text_to_list(update.message.text, SEPARATORS)):
                search_set = [x[0] for x in db.search_items(search_word)]
                if 0 < len(search_set) <= 2:
                    for item in search_set:
                        places = "\n".join([f'{ICONS["box"] * y} ➔ {x}' for x, y in db.search_places(item)])
                        markup = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text=f'{choice(ICONS["remove"])} {rem} {item}', callback_data=item)],
                            [BUTTON_CANCEL]
                        ])
                        update.message.reply_text(f'{item} расположен:\n{places}', reply_markup=markup)
                else:
                    if search_set:
                        partial_match = "\n".join(search_set)
                        update.message.reply_text(f'Что-то из этого?:\n{partial_match}')
                    else:
                        update.message.reply_text(f'❌ {choice(BAD_WORDS)}')
        except BadRequest:
            update.message.reply_text(choice(BAD_WORDS_ERROR))


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    commands = {
        "add_item": cmd_add_item,
        "add_place": cmd_add_place,
        "csv": cmd_csv,
        "del_item": cmd_del_item,
        "dev_info": cmd_dev_info,
        "dice": cmd_dice,
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
