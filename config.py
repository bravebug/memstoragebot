#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


# BAD_WORDS = ("❌", "один сломали, другой потеряли", "не нашёл", "и мне бы хотелось, но нет")
BAD_WORDS = ("не нашёл", "и мне бы хотелось, но нет", "ищи пакет", "в ящиках с пакетами")

BAD_WORDS_ERROR = ("Воу, Воу! Полегче!", "Походу сервера легли!", "Или что-то случилось, или… одно из двух!")

ICONS = {
    "box": "📦",
    "remove": "🆗🗑🟢🟩✅✍️💥🔥🎖🏆🚀🛸💰💎🛒🎁🚮⏏️",
}

RE_ITEM_FORMAT = r""

SEPARATORS = r" ,/;\|" + "\n"

SYNONYMS = {
    "cmd_add_place": (
        "add_place",
        "добавить_место",
        "добавь_место",
    ),
    "cmd_add_item": (
        "+",
        "add",
        "добавить",
        "добавь",
    ),
    "cmd_del_item": (
        "-",
        "del",
        "удалить",
        "удали",
    ),
    "cmd_csv": (
        "csv",
        "экспорт",
        "в файл",
    ),
    "cmd_roll": (
        "жребий",
        "каменцы",
        "судьбина",
    ),
}

HELP_TEXT = {
        "cmd_start": (
            "Меня зовут Полочка! Я могу запомнить что и где лежит!",
            "Управляй мной такими командами:",
        ),
        "cmd_add_place": (
            f'/add_place МЕСТО … - добавляет МЕСТО.',
            f'Вместо команды /add_place ты также можешь просто начать сообщение с: {", ".join(SYNONYMS["cmd_add_place"])}',
        ),
        "cmd_add_item": (
            f'/add_item ОБЪЕКТ … - добавляет ОБЪЕКТ на МЕСТО.',
            f'Вместо команды /add_item ты также можешь просто начать сообщение с: {", ".join(SYNONYMS["cmd_add_item"])}',
        ),
        "cmd_csv": (
            f'/csv - экспортирует данные в файл csv.',
            f'Вместо команды /csv ты также можешь просто написать: {", ".join(SYNONYMS["cmd_csv"])}',
        ),
        "cmd_roll": (
            f'/roll - бросает жребий.',
            f'Вместо команды /roll ты также можешь просто начать сообщение с: {", ".join(SYNONYMS["cmd_roll"])}',
            'Например:',
            '➡️ /roll Федя Петя Вася = пойдёт за лимонадом',
            '⬅ ️Пойдёт за лимонадом: Петя',
            '',
            f'➡ /roll Гена Жора',
            f'⬅ Победил: Гена',
        ),
        "cmd_help": (
            '/help - выводит эту справку',
            ("С более подробной информацией Вы можете ознакомится на странице проекта: "
             "https://github.com/bravebug/memstoragebot"),
        ),
    }

TOKEN = os.environ["TOKEN"]


if __name__ == "__main__":
    print("\n\n".join("\n".join(text) for text in HELP_TEXT.values()))