#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from random import choice
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Document
from telegram.error import BadRequest
from database import SqLiter
from config import TOKEN, SEPARATORS, SYNONYMS, RE_ITEM_FORMAT, BAD_WORDS, BAD_WORDS_ERROR, ICONS, HELP_TEXT


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


def cmd_add_item(update, context):
    tg_help = "testcmdaddhelp"
    Q = ("Куда ставить-то?", "На какое место записываю?", "Размещаю где?", "Куда?")
    msg = update.message
    chat_id = msg.chat_id
    user_id = msg.from_user.id
    data_id = f"{chat_id}{user_id}"
    db = SqLiter(chat_id)
    cmd, *items = text_to_list(msg.text, SEPARATORS)
    if items:
        data[data_id] = items
        keyboard = print_place(update, context)
        msg.reply_text(f'{", ".join(sorted(set(items)))}\n{choice(Q)}', reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    else:
        output = "\n\n".join(HELP_TEXT["cmd_add_item"])
        msg.reply_text(f'Нужно ввести хотя бы одну запись\n\nСправка:\n{output}')


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
    msg = update.message
    db = SqLiter(msg.chat_id)
    _, *places = text_to_list(msg.text, SEPARATORS)
    if places:
        db.add_places(places)
        output = "\n".join(places)
        msg.reply_text(f'Добавлен{"ы" if len(places) > 1 else "о"} мест{"а" if len(places) > 1 else "о"} хранения: \n{output}')
    else:
        msg.reply_text("Бывает...")


def cmd_check_place(update, context):
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
        "Управляй мной такими командами:",
        '',
        f'/add_place МЕСТО … - добавляет МЕСТО.',
        f'Вместо команды /add_place ты также можешь просто начать сообщение с: {", ".join(SYNONYMS["cmd_add_place"])}',
        '',
        f'/add_item ОБЪЕКТ … - добавляет ОБЪЕКТ на МЕСТО.',
        f'Вместо команды /add_item ты также можешь просто начать сообщение с: {", ".join(SYNONYMS["cmd_add_item"])}',
        '',
        f'/csv - экспортирует данные в файл csv.',
        f'Вместо команды /csv ты также можешь просто написать: {", ".join(SYNONYMS["cmd_csv"])}',
        '',
        f'/roll - бросает жребий.',
        f'Вместо команды /roll ты также можешь просто начать сообщение с: {", ".join(SYNONYMS["cmd_roll"])}',
        'Например:',
        '➡️ /roll Федя Петя Вася = пойдёт за лимонадом',
        '⬅ ️Пойдёт за лимонадом: Петя',
        '',
        f'➡ /roll Гена Жора',
        f'⬅ Победил: Гена',
        # '/dice - выбрасывает 2 игральные кости',
        # '/dev_info - выводит информацию, достаточную для взлома вашей учётки',
        '',
        '/help - выводит эту справку',
        '',
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
    print(context.args)
    msg = update.message.text
    win = "Победил"
    if "=" in msg:
        msg, comment = msg.rsplit("=", 1)
        comment = comment.strip()
        if comment:
            win = f"{comment[0].upper()}{comment[1:]}"
    cmd, *names = text_to_list(msg.strip(), SEPARATORS)
    if names:
        if len(names) == 1:
            output = f'{names[0]}…\n…в чём тут подвох?'
        else:
            output = choice(names)
        update.message.reply_text(f'{win}: {output}')
    else:
        update.message.reply_text(f'Победила дружба!')


def cmd_start(update, context):
    cmd_help(update, context)


def cmd_csv(update, context):
    msg = update.message
    db = SqLiter(msg.chat_id)
    fields_all = db.take_all()
    if fields_all:
        from csv import writer, QUOTE_ALL
        from io import StringIO
        from datetime import datetime
        temp_file = StringIO(newline="")
        fwriter = writer(temp_file, dialect="excel", delimiter=";", quotechar='"')
        fwriter.writerow(("Запись", "Место"))
        fwriter.writerows(fields_all)
        temp_file.seek(0)
        date = datetime.now()
        msg.reply_document(
            temp_file,
            filename=f'memstoragebot--{date.strftime("%Y-%m-%d--%H-%M")}.csv',
        )
        temp_file.close()
        del writer, QUOTE_ALL, StringIO, datetime
    else:
        msg.reply_text("нет записей")


def cmd_test(update, context):
    update.message.reply_text(dir(context))


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
    keyboard = [[]]
    max_button_len = 0
    for place_id, name in db.places():
        # name = num_to_emoji_replace(name)
        current_button_len = len(name)
        max_button_len = current_button_len if current_button_len > max_button_len else max_button_len
        if (len(keyboard[-1]) + 1) * max_button_len > 26:
            keyboard.append([])
            max_button_len = current_button_len
        keyboard[-1].append(InlineKeyboardButton(text=name, callback_data=place_id))
    keyboard.append([BUTTON_CANCEL])
    return keyboard


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
        update.callback_query.message.reply_text(
            f'{", ".join(sorted(set(data[data_id])))}\nдобавлены на место {db.placename_by_id(update.callback_query.data)[0]}'
        )
        del data[data_id]
    else:
        db.remove_item(tmp_data)
        update.callback_query.message.reply_text(f'{tmp_data}\nудалено')
    update.callback_query.message.delete() 


def reply(update, context):
    rem = "Стереть"
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
    dp.add_handler(CommandHandler("add_item", cmd_add_item))
    dp.add_handler(CommandHandler("add_place", cmd_add_place))
    dp.add_handler(CommandHandler("csv", cmd_csv))
    dp.add_handler(CommandHandler("del_item", cmd_del_item))
    dp.add_handler(CommandHandler("dev_info", cmd_dev_info))
    dp.add_handler(CommandHandler("dice", cmd_dice))
    dp.add_handler(CommandHandler("help", cmd_help))
    dp.add_handler(CommandHandler("restart", cmd_restart_service))
    dp.add_handler(CommandHandler("roll", cmd_roll))
    dp.add_handler(CommandHandler("start", cmd_start))
    dp.add_handler(CommandHandler("test", cmd_test))
    dp.add_handler(CallbackQueryHandler(callback__))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
