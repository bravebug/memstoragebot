#!/usr/bin/env python
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import BotCommand
from aiogram.types.input_file import InputFile
from config import make_config
from csv import writer
from database import DataBase
from datetime import datetime
from functools import partial
from io import StringIO
from messages import MESSAGES
from random import choice
from storage import TempSorage
from typing import IO, Iterable
from utils import split_asterisk_and_sharp
from utils import remove_extra_spaces as clear_text
import inspect
import re

logging.basicConfig(level=logging.INFO)
conf = make_config()
bot = Bot(token=conf.TOKEN, parse_mode="HTML")
db = DataBase(
        database_uri=conf.SQLALCHEMY_DATABASE_URI,
        echo=conf.SQLALCHEMY_DATABASE_ECHO,
        deployment_key=conf.SQLALCHEMY_DATABASE_DEPLOYMENT_KEY,
        clear_text=clear_text,
    )
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
temp_storage = TempSorage()
input_state = {}

ITEM_NAME_ADD_PATTERN = re.compile(conf.RE_ITEM_ADD_FORMAT)
ITEM_NAME_SEARCH_PATTERN = re.compile(conf.RE_ITEM_SEARCH_FORMAT)
SEPARATORS = re.compile(conf.SEPARATORS)

BUTTON_CANCEL_TEXT = f'{MESSAGES["cancel_icon"]} {MESSAGES["cancel"]}'
BUTTON_OK_TEXT = f'{MESSAGES["successful_action_icon"]} {MESSAGES["ok"]}'
BUTTON_REMOVE_TEXT = f'{MESSAGES["remove_icon"]} {MESSAGES["remove"]}'


class Order(StatesGroup):
    waiting_for_input = State()


class OrderLocation(StatesGroup):
    waiting_for_input = State()


class OrderThing(StatesGroup):
    waiting_for_input = State()


class OrderLocationNewName(StatesGroup):
    waiting_for_input = State()


async def setup_bot_commands(dispatcher):
    bot_commands = [
        BotCommand(command="/add", description=MESSAGES['add_command_menu_item_description']),
        BotCommand(command="/add_location", description=MESSAGES['add_location_command_menu_item_description']),
        BotCommand(command="/manage_locations", description=MESSAGES['manage_locations_command_menu_item_description']),
        # BotCommand(command="/config", description=MESSAGES['config_command_menu_item_description']),
        BotCommand(command="/csv", description=MESSAGES['csv_command_menu_item_description']),
        BotCommand(command="/roll", description=MESSAGES['roll_command_menu_item_description']),
        BotCommand(command="/about", description=MESSAGES['about_command_menu_item_description'])
    ]
    await bot.set_my_commands(bot_commands)


@dp.message_handler(Text(equals=BUTTON_CANCEL_TEXT, ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply(
        text=MESSAGES['cancelled'],
        reply_markup=types.ReplyKeyboardRemove(),
    )


@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    await message.answer("\n".join(MESSAGES['help_text']))


@dp.message_handler(commands=['about'])
async def about(message: types.Message):
    await message.answer("\n".join(MESSAGES['about_text']))


async def manage_location(message: types.Message, state: FSMContext, location):
    kb = types.InlineKeyboardMarkup(row_width=1)
    with temp_storage.batch(message.chat.id, message.from_id) as batch:
        kb.insert(
            types.InlineKeyboardButton(
                text=MESSAGES['clear_location'],
                callback_data=batch.add(
                    partial(clean_location, message, state, location=location)
                )
            )
        )
        kb.insert(
            types.InlineKeyboardButton(
                text=MESSAGES['rename_location'],
                callback_data=batch.add(
                    partial(rename_location_start, message, state, location=location)
                )
            )
        )
        kb.insert(
            types.InlineKeyboardButton(
                text=MESSAGES['remove_location'],
                callback_data=batch.add(
                    partial(remove_location, message, state, location=location)
                )
            )
        )
        kb.insert(
            types.InlineKeyboardButton(
                text=MESSAGES['move_entries'],
                callback_data=batch.add(
                    partial(move_entries, message, location=location)
                )
            )
        )
        kb.add(
            types.InlineKeyboardButton(
                text=BUTTON_CANCEL_TEXT,
                callback_data=batch.add(
                    partial(action_with_output, None, MESSAGES['cancelled'])
                )
            )
        )
    return 'выберите действие', kb


@dp.message_handler(commands=['manage_locations'])
async def manage_locations(message: types.Message, state: FSMContext):
    if not (locations := db.get_locations(message.chat.id)):
        await message.reply(MESSAGES['need_location_msg'])
    else:
        kb = types.InlineKeyboardMarkup(row_width=3)
        with temp_storage.batch(message.chat.id, message.from_id) as batch:
            for name, i in locations:
                kb.insert(
                    types.InlineKeyboardButton(
                        text=name,
                        callback_data=batch.add(
                            partial(manage_location, message, state, location=(i, name)),
                        )
                    )
                )
            kb.add(
                types.InlineKeyboardButton(
                    text=BUTTON_CANCEL_TEXT,
                    callback_data=batch.add(
                        partial(action_with_output, None, MESSAGES['cancelled']),
                    )
                )
            )
        await message.reply(
            text=MESSAGES['choose_location'],
            reply_markup=kb,
        )


async def move_entries(message: types.Message, location=None, entry_ids=None):
    if not (locations := db.get_locations(message.chat.id)):
        await message.reply(MESSAGES['need_location_msg'])
    else:
        kb = types.InlineKeyboardMarkup(row_width=3)
        location_from_id = location[0] if location else None
        with temp_storage.batch(message.chat.id, message.from_id) as batch:
            for name, i in locations:
                kb.insert(
                    types.InlineKeyboardButton(
                        text=name,
                        callback_data=batch.add(
                            partial(
                                action_with_output,
                                partial(
                                    db.move_entries,
                                    location_from_id=location_from_id,
                                    entry_ids=entry_ids,
                                    location_to_id=i,
                                ),
                                f'{MESSAGES["successful_action_icon"]} {MESSAGES["entries_moved"]}'
                            )
                        )
                    )
                )
            kb.add(
                types.InlineKeyboardButton(
                    text=BUTTON_CANCEL_TEXT,
                    callback_data=batch.add(
                        partial(action_with_output, None, MESSAGES['cancelled']),
                    )
                )
            )
    return MESSAGES['choose_location'], kb


@dp.message_handler(state=OrderLocation.waiting_for_input)
async def add_location_process(message: types.Message, state: FSMContext):
    if not (names := re.split(SEPARATORS, message.get_args() if message.is_command() else message.text.lstrip('++'))):
        return await message.reply(MESSAGES['try_again'])
    else:
        output_names = []
        for name in names:
            if name := clear_text(name):
                db.add_location(name, message.chat.id)
                output_names.append(name)
        output_names_string = '\n'.join(sorted(output_names))
        await message.reply(
            text=f'{MESSAGES["successful_action_icon"]} {MESSAGES["added"]}\n{output_names_string}',
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.finish()


@dp.message_handler(Command(commands=['add_location'], ignore_case=True), state='*')
@dp.message_handler(Text(startswith='++', ignore_case=True))
async def add_location_start(message: types.Message, state: FSMContext):
    if message.get_args() if message.is_command() else message.text.lstrip('++'):
        await add_location_process(message, state)
    else:
        await OrderLocation.waiting_for_input.set()
        await message.reply(
            text=MESSAGES["send_new_name_or_names_locations"],
            reply_markup=types.ReplyKeyboardMarkup(
                [[BUTTON_CANCEL_TEXT]],
                resize_keyboard=True,
                one_time_keyboard=True,
                selective=True,
            ),
        )


@dp.message_handler(state=OrderLocationNewName.waiting_for_input)
async def rename_location_process(message: types.Message, state: FSMContext):
    if not (name := clear_text(message.text)):
        return await message.reply(MESSAGES['try_again'])
    else:
        async with state.proxy() as data:
            id = data.get("id")
        if db.get_locations(instance_name=message.chat.id, location_name=name):
            await message.reply(
                text=MESSAGES["name_is_taken"].format(name=name),
                reply_markup=types.ReplyKeyboardRemove(),
            )
        else:
            db.rename_location(id=id, name=name, instance_name=message.chat.id)
            await message.reply(
                text=f'{MESSAGES["successful_action_icon"]} {MESSAGES["name_changed"]}',
                reply_markup=types.ReplyKeyboardRemove(),
            )
        await state.finish()


async def rename_location_start(message: types.Message, state: FSMContext, location):
    await OrderLocationNewName.waiting_for_input.set()
    _id, name = location
    async with state.proxy() as data:
        data['id'] = _id
    output = MESSAGES['send_new_name'].format(location_name=name)
    kb = types.ReplyKeyboardMarkup(
        [[BUTTON_CANCEL_TEXT]],
        resize_keyboard=True,
        one_time_keyboard=True,
        selective=True,
    )
    await message.reply(text=output, reply_markup=kb)
    return None, None


async def remove_location(message: types.Message, state: FSMContext, location):
    kb = types.InlineKeyboardMarkup(row_width=2)
    with temp_storage.batch(message.chat.id, message.from_id) as batch:
        kb.insert(
            types.InlineKeyboardButton(
                text=BUTTON_OK_TEXT,
                callback_data=batch.add(
                    partial(
                        action_with_output,
                        partial(db.remove_location_by_id, location_id=location[0]),
                        f'{MESSAGES["successful_action_icon"]} {MESSAGES["location_removed"].format(location_name=location[1])}!',
                    )
                )
            )
        )
        kb.insert(
            types.InlineKeyboardButton(
                text=BUTTON_CANCEL_TEXT,
                callback_data=batch.add(
                    partial(action_with_output, None, MESSAGES['cancelled'])
                )
            )
        )
    await message.reply(
        text='Удаляю расположение вместе со всеми объектами на нём?',
        reply_markup=kb,
    )
    return None, None


async def clean_location(message: types.Message, state: FSMContext, location):
    _id, name = location
    output = MESSAGES['accept_clear_location'].format(location_name=name)
    kb = types.InlineKeyboardMarkup(row_width=2)
    with temp_storage.batch(message.chat.id, message.from_id) as batch:
        kb.insert(
            types.InlineKeyboardButton(
                text=BUTTON_OK_TEXT,
                callback_data=batch.add(
                    partial(
                        action_with_output,
                        partial(db.remove_entries_by_location_id, location_id=_id),
                        f'{MESSAGES["successful_action_icon"]} {MESSAGES["location_cleared"]}'.format(location_name=name))
                )
            )
        )
        kb.insert(
            types.InlineKeyboardButton(
                text=BUTTON_CANCEL_TEXT,
                callback_data=batch.add(
                    partial(action_with_output, None, MESSAGES['cancelled'])
                )
            )
        )
    return output, kb


@dp.message_handler(state=OrderThing.waiting_for_input)
async def add_entry_process(message: types.Message, state: FSMContext):
    if not db.get_locations(message.chat.id):
        await message.reply(MESSAGES['need_location_msg'])
    else:
        if not (entries := re.split(SEPARATORS, message.get_args() if message.is_command() else message.text.lstrip('+'))):
            await message.reply(MESSAGES['try_again'])
        else:
            correct_entries = []
            for entry in entries:
                if entry := clear_text(entry):
                    entry_name, quantity_text, description = split_asterisk_and_sharp(entry)
                    if not re.match(ITEM_NAME_ADD_PATTERN, entry_name):
                        await message.reply(
                            text=MESSAGES['invalid_entry_msg'].format(
                                invalid_entry=entry.strip(),
                                pattern=ITEM_NAME_ADD_PATTERN.pattern,
                            ),
                        )
                        continue
                    if quantity_text:
                        try:
                            quantity = int(quantity_text)
                        except ValueError:
                            await message.reply(
                                text=MESSAGES['invalid_quantity_msg'].format(
                                    entry=entry.strip(),
                                    quantity=quantity_text
                                ),
                            )
                            continue
                    else:
                        quantity = 1
                    correct_entries.append([entry_name, quantity, description])
            correct_entries_list = []
            for name, quantity, description in correct_entries:
                boxes = MESSAGES["box"] * quantity
                if description:
                    description_formated = MESSAGES['description_format'].format(description=description)
                else:
                    description_formated = ''
                correct_entry = MESSAGES["added_entry_template"].format(
                    name=name,
                    quantity=quantity,
                    boxes=boxes,
                    description_formated=description_formated
                )
                correct_entries_list.append(correct_entry)
            if correct_entries_list:
                correct_entries_listing = "\n".join(correct_entries_list)
                kb = types.InlineKeyboardMarkup(row_width=3)
                with temp_storage.batch(message.chat.id, message.from_id) as batch:
                    for name, i in db.get_locations(message.chat.id):
                        kb.insert(
                            types.InlineKeyboardButton(
                                text=name,
                                callback_data=batch.add(
                                    partial(
                                        action_with_output,
                                        partial(
                                            db.add_entries,
                                            things=correct_entries,
                                            instance_name=message.chat.id,
                                            location_id=i,
                                        ),
                                        (
                                            f'{MESSAGES["successful_action_icon"]} {MESSAGES["added"]}\n'
                                            f'{correct_entries_listing}\n➡️ <b>{name}</b>\n'
                                        ),
                                    )
                                )
                            )
                        )
                    kb.add(
                        types.InlineKeyboardButton(
                            text=BUTTON_CANCEL_TEXT,
                            callback_data=batch.add(
                                partial(action_with_output, None, MESSAGES['cancelled'])
                            )
                        )
                    )
                await message.reply(
                    text=MESSAGES['choose_location'],
                    reply_markup=kb,
                )
            else:
                await message.reply(
                    text=MESSAGES['cancelled'],
                    reply_markup=types.ReplyKeyboardRemove(),
                )
            await state.finish()


@dp.message_handler(commands=['add'])
@dp.message_handler(Text(startswith='+', ignore_case=True))
async def add_entry_start(message: types.Message, state: FSMContext):
    if message.get_args() if message.is_command() else message.text.lstrip('+'):
        await add_entry_process(message, state)
    else:
        await OrderThing.waiting_for_input.set()
        await message.reply(
            text=MESSAGES['send_new_name_or_names_things'],
            reply_markup=types.ReplyKeyboardMarkup(
                [[BUTTON_CANCEL_TEXT]],
                resize_keyboard=True,
                one_time_keyboard=True,
                selective=True,
            ),
        )


async def generate_csv(csv_file: IO, data: Iterable, header_row: Iterable) -> IO:
    csv_file.write("\ufeff")  # utf-8 byte order mark
    fwriter = writer(csv_file, dialect="excel", delimiter=";")
    fwriter.writerow(header_row)
    fwriter.writerows(data)
    csv_file.seek(0)
    return csv_file


@dp.message_handler(commands=['csv'])
@dp.message_handler(Text(equals=MESSAGES['csv_hot_words'].split(), ignore_case=True))
async def export_csv(message: types.Message):
    if data := db.search_entries(instance_name=message.chat.id):
        data = ((i,) + d[1:] for i, d in enumerate(data, start=1))
        with StringIO(newline="") as csv_file:
            csv_file = await generate_csv(
                csv_file,
                data,
                (
                    MESSAGES["number_sign"],
                    MESSAGES["entry"],
                    MESSAGES["location"],
                    MESSAGES["quantity"],
                    MESSAGES["description"],
                ),
            )
            await message.reply_document(
                document=InputFile(csv_file, filename=f'memstoragebot--{datetime.now():%Y-%m-%d--%H-%M}.csv'),
            )
    else:
        await message.reply(
            text=MESSAGES["memory_is_empty"]
        )


@dp.message_handler(commands=['roll'])
@dp.message_handler(Text(startswith=['roll'], ignore_case=True))
async def cmd_roll(message: types.Message):
    if msg := (message.get_args() if message.is_command() else message.text.lstrip('roll')):
        win_msg = MESSAGES['win']
        if '=' in msg:
            msg, win_msg = msg.rsplit('=', 1)
        names = re.split(SEPARATORS, msg)
        if names:
            if len(names) == 1:
                output = MESSAGES['choosing_from_one'].format(name=names[0])
            else:
                output = choice(names)
            await message.reply(text=f'{win_msg.strip().upper()}: {output}')
        else:
            await message.reply(text=MESSAGES['friendship_won'])


async def action_with_output(action, output):
    if action:
        if inspect.iscoroutinefunction(action):
            await action()
        else:
            action()
    return output, None


async def search_entries(message: types.Message, entry_name):
    entries = db.search_entries(equals=entry_name, instance_name=message.chat.id)

    correct_entries_list = []
    for i, name, location, quantity, description in entries:
        if description:
            description_formated = MESSAGES['description_format'].format(description=description)
        else:
            description_formated = ''
        correct_entry = MESSAGES["found_entry_template"].format(
            location=location,
            quantity=quantity,
            boxes=MESSAGES["box"] * quantity,
            description_formated=description_formated
        )
        correct_entries_list.append(correct_entry)
    output_entries = "\n".join(correct_entries_list)
    output = f'<i>{entries[0][1]}</i>:\n{output_entries}'
    kb = types.InlineKeyboardMarkup(row_width=1)
    entry_ids = [item[0] for item in entries]
    with temp_storage.batch(message.chat.id, message.from_id) as batch:
        kb.insert(
            types.InlineKeyboardButton(
                text=BUTTON_REMOVE_TEXT,
                callback_data=batch.add(
                    partial(
                        action_with_output,
                        partial(db.remove_entries_by_ids, entry_ids),
                        f'{output}\n{MESSAGES["removed"]}',
                    )
                )
            )
        )
        kb.insert(
            types.InlineKeyboardButton(
                text=f'{MESSAGES["move_entries_icon"]} {MESSAGES["move_entries"]}',
                callback_data=batch.add(
                    partial(move_entries, message, entry_ids=entry_ids)
                )
            )
        )
        kb.add(
            types.InlineKeyboardButton(
                text=BUTTON_CANCEL_TEXT,
                callback_data=batch.add(
                    partial(action_with_output, None, f'{output}\n{MESSAGES["cancelled"]}')
                )
            )
        )
    return output, kb


@dp.message_handler()
async def search(message: types.Message):
    for word in re.findall(ITEM_NAME_SEARCH_PATTERN, message.text):
        entries_names = db.search_things(search_string=word, instance_name=message.chat.id)
        if not entries_names:
            await message.reply(
                text=MESSAGES['thing_not_found'],
            )
        else:
            match len(entries_names):
                case l if l > 5:
                    await message.reply(
                        text=MESSAGES['request exactly'],
                    )
                case 1:
                    entry_name = entries_names[0][0]
                    output, kb = await search_entries(message, entry_name)
                    await message.reply(
                        text=f'{MESSAGES["found"]} {output}',
                        reply_markup=kb,
                    )
                case _:
                    kb = types.InlineKeyboardMarkup(row_width=2)
                    with temp_storage.batch(message.chat.id, message.from_id) as batch:
                        for name in entries_names:
                            kb.insert(
                                types.InlineKeyboardButton(
                                    text=name[0],
                                    callback_data=batch.add(
                                        partial(
                                            search_entries,
                                            message=message,
                                            entry_name=name[0],
                                        )
                                    )
                                )
                            )
                        kb.add(
                            types.InlineKeyboardButton(
                                text=BUTTON_CANCEL_TEXT,
                                callback_data=batch.add(
                                    partial(action_with_output, None, MESSAGES['cancelled'])
                                )
                            )
                        )
                    await message.reply(
                        text=MESSAGES['choose'],
                        reply_markup=kb,
                    )


@dp.callback_query_handler()
async def callback_handler(callback: types.CallbackQuery):
    msg = callback.message.reply_to_message
    try:
        action = temp_storage.get(callback.data, chat=msg.chat.id, user=msg.from_id)
        output = None
        kb = None
        if action:
            if inspect.iscoroutinefunction(action):
                output, kb = await action()
            else:
                output, kb = action()
            if output or kb:
                await callback.message.edit_text(
                    text=output,
                    reply_markup=kb,
                )
            else:
                await callback.message.delete()
        else:
            await callback.message.edit_text(f'{callback.message.text}\n{MESSAGES["button_broken"]}')
    except KeyError:
        await callback.message.edit_text(f'{callback.message.text}\n{MESSAGES["button_broken"]}')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=setup_bot_commands)
