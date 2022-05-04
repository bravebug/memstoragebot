#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from random import choice
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Document
from telegram.error import BadRequest
from database import SqLiter
from config import TOKEN, SEPARATORS, SYNONYMS, RE_ITEM_FORMAT, BAD_WORDS, BAD_WORDS_ERROR, ICONS, HELP_TEXT
from datasaver import DataSaver
from typing import Iterable, IO, Generator
from csv import writer
from io import StringIO, BytesIO
from datetime import datetime
from speech_recognition_vosk import speech_to_text
from functools import cache


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


BUTTON_OK = InlineKeyboardButton(text="ОК", callback_data="accept")
BUTTON_CANCEL = InlineKeyboardButton(text="Отмена", callback_data="cancel")
KEYBOARD_OK_CANCEL = [BUTTON_OK, BUTTON_CANCEL]


def text_to_list(text: str, separators: Iterable[str]) -> Generator[str, None, None]:
    text = text + separators[0]
    word = []
    for letter in text:
        if letter in separators:
            if word:
                yield "".join(word)
            word.clear()
        else:
            word.append(letter)


def format_list(data: Iterable[str], uniq=False, sort=False, sep=", ") -> str:
    if uniq:
        data = set(data)
    if sort:
        data = sorted(data)
    return sep.join(data)


def generate_csv(csv_file: IO, data: Iterable, header_row: Iterable) -> IO:
    csv_file.write("\ufeff")  # utf-8 byte order mark
    fwriter = writer(csv_file, dialect="unix", delimiter=";", quotechar="'")
    fwriter.writerow(header_row)
    fwriter.writerows(data)
    csv_file.seek(0)
    return csv_file


def generate_keyboard(data: Iterable, limit_row_length: int = 24):
    """generates a keyboard that makes optimal use of screen space"""
    keyboard = [[]]
    max_button_len = 0
    for data_id, name in data:
        current_button_len = len(name)
        max_button_len = current_button_len if current_button_len > max_button_len else max_button_len
        kb_len = len(keyboard[-1])
        if kb_len > 4 or kb_len * max_button_len > limit_row_length:
            keyboard.append([])
            max_button_len = current_button_len
        keyboard[-1].append(InlineKeyboardButton(text=name, callback_data=data_id))
    keyboard.append([BUTTON_CANCEL])
    return keyboard


def cmd_add_item(update, context):
    msg = update.message
    db = SqLiter(msg.chat_id)
    _, *items = text_to_list(msg.text, SEPARATORS)
    places = db.places()
    if places:
        if items:
            saver = saver_obj(msg.chat_id, msg.from_user.id, msg.message_id)
            saver.func = db.add_items
            saver.data.append(items)
            saver.output_ok = "{items}\nдобавила на место {place}"
            saver.output_ok_data_name = "place"
            saver.output_ok_data_func = db.placename_by_id
            items_text = "\n".join(items)
            saver.output_ok_data.update({"items": items_text})
            keyboard = generate_keyboard(places)
            msg.reply_text(
                "На какое место отнести?",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                reply_to_message_id=msg.message_id,
            )
        else:
            output = "\n\n".join(HELP_TEXT["cmd_add_item"])
            msg.reply_text(f'Нужно ввести хотя бы одну запись\n\nСправка:\n{output}')
    else:
        output = "\n\n".join(HELP_TEXT["cmd_add_place"])
        msg.reply_text(f'Не заданы места хранения\n\nСправка:\n{output}')


@cache
def saver_obj(ci, ui, mi):
    return DataSaver(ci, ui, mi)


def cmd_add_place(update, context):
    msg = update.message
    db = SqLiter(msg.chat_id)
    _, *places = text_to_list(msg.text, SEPARATORS)
    if places:
        saver = saver_obj(msg.chat_id, msg.from_user.id, msg.message_id)
        saver.func = db.add_places
        saver.data.append(places)
        saver.output_ok = "Добавила мест{suffix} хранения: {places}"
        places_text = "\n".join(places)
        saver.output_ok_data.update({"places": places_text})
        suffix = "о" if len(places) == 1 else "а"
        saver.output_ok_data.update({"suffix": suffix})
        keyboard = [KEYBOARD_OK_CANCEL]
        msg.reply_text(
            f'{places_text}\nдобавляю мест{suffix} хранения?',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            reply_to_message_id=msg.message_id,
        )
    else:
        output = "\n\n".join(HELP_TEXT["cmd_add_place"])
        msg.reply_text(f'Нужно ввести хотя бы одно место хранения\n\nСправка:\n{output}')


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
        '',
        '/help - выводит эту справку',
        '',
        ("С более подробной информацией Вы можете ознакомится на странице проекта: "
         "https://github.com/bravebug/memstoragebot"),
    )
    update.message.reply_text("\n".join(help_text))


def cmd_roll(update, context):
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
        date = datetime.now()
        with StringIO(newline="") as csv_file:
            csv_file = generate_csv(csv_file, fields_all, ("Запись", "Место"))
            msg.reply_document(
                csv_file,
                filename=f'memstoragebot--{date:%Y-%m-%d--%H-%M}.csv',
            )
    else:
        msg.reply_text("Моя память сейчас пуста")


def cmd_del_item(update, context):
    msg = update.message
    db = SqLiter(msg.chat_id)
    cmd, *items = text_to_list(update.message.text, SEPARATORS)
    items = {item for item in set(items) if db.accurate_search(item)}
    if items:
        saver = saver_obj(msg.chat_id, msg.from_user.id, msg.message_id)
        saver.func = db.remove_items
        saver.data.append(items)
        saver.output_ok = "{items}\nаннигилировала"
        items_text = "\n".join(items)
        saver.output_ok_data.update({"items": items_text})
        msg.reply_text(
            f'{items_text}\nбудут удалены сразу отовсюду! Ок?',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[KEYBOARD_OK_CANCEL]),
            reply_to_message_id=msg.message_id,
        )


def callback__(update, context):
    query = update.callback_query
    msg = query.message
    chat_id = msg.chat_id
    user_id = query.from_user.id
    msg_id = msg.reply_to_message.message_id
    db = SqLiter(chat_id)
    _, *items = text_to_list(msg.text, SEPARATORS)
    saver = saver_obj(chat_id, user_id, msg_id)
    db = SqLiter(chat_id)
    tmp_data = query.data
    if tmp_data != "cancel":
        if tmp_data != "accept":
            if saver.output_ok_data_func:
                saver.output_ok_data.update({saver.output_ok_data_name: saver.output_ok_data_func(tmp_data)})
            saver.data.append(tmp_data)
        msg.edit_text(saver.execute())
    else:
        msg.edit_text(saver.reset())


def reply(update, context):
    rem = "Стереть"
    msg = update.message
    flag = False
    for operation in SYNONYMS:
        if flag:
            break
        for synonym in SYNONYMS[operation]:
            if msg.text.lower().startswith(synonym.lower()):
                if not synonym.endswith(" "):
                    msg.text = f"{synonym} {msg.text.lstrip(synonym)}"
                import __main__
                __main__.__dict__.get(operation)(update, context)
                flag = True
                break
    if not flag:
        db = SqLiter(msg.chat_id)
        try:
            for search_word in set(text_to_list(msg.text, SEPARATORS)):
                search_set = [x[0] for x in db.inaccurate_search(search_word)]
                if 0 < len(search_set) <= 1:
                    for item in search_set:
                        places = "\n".join([f'{ICONS["box"] * y} ➔ {x}' for x, y in db.search_places(item)])
                        saver = saver_obj(msg.chat_id, msg.from_user.id, msg.message_id)
                        saver.func = db.remove_item
                        saver.data.append(item)
                        saver.output_ok = "{item}\nУдалила"
                        saver.output_ok_data.update({"item": item})
                        markup = InlineKeyboardMarkup(inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text=f'{choice(ICONS["remove"])} {rem} {item}',
                                    callback_data="accept",
                                )
                            ],
                            [BUTTON_CANCEL]
                        ])
                        msg.reply_text(
                            f'{item} расположен:\n{places}',
                            reply_markup=markup,
                            reply_to_message_id=msg.message_id,
                        )
                else:
                    if search_set:
                        partial_match = "\n".join(search_set)
                        msg.reply_text(f'Что-то из этого?:\n{partial_match}')
                    else:
                        msg.reply_text(f'❌ {choice(BAD_WORDS)}')
        except BadRequest:
            msg.reply_text(choice(BAD_WORDS_ERROR))


def reply_voice(update, context):
    msg = update.message
    input_file = BytesIO()
    update.message.voice.get_file().download(out=input_file)
    recognized_text = speech_to_text(input_file)
    if recognized_text:
        msg.reply_text(recognized_text)
        # update.message.text = recognized_text
        # reply(update, context)


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("add_item", cmd_add_item))
    dp.add_handler(CommandHandler("add_place", cmd_add_place))
    dp.add_handler(CommandHandler("csv", cmd_csv))
    dp.add_handler(CommandHandler("del_item", cmd_del_item))
    dp.add_handler(CommandHandler("dev_info", cmd_dev_info))
    dp.add_handler(CommandHandler("help", cmd_help))
    dp.add_handler(CommandHandler("roll", cmd_roll))
    dp.add_handler(CommandHandler("start", cmd_start))
    dp.add_handler(CallbackQueryHandler(callback__, pass_chat_data=True))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply))
    dp.add_handler(MessageHandler(Filters.voice, reply_voice))
    # dp.add_handler(MessageHandler(Filters.voice, reply))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
