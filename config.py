#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


TOKEN = os.environ["TOKEN"]
SEPARATORS = r" ,/;\|" + "\n"
ADD_SYNONYMS = (
    "+",
    "add ",
    "добавить ",
    "добавь ",
)
RE_ITEM_FORMAT = r""
BAD_WORDS = ("❌", "один сломали, другой потеряли", "не нашёл", "и мне бы хотелось, но нет")
BAD_WORDS_ERROR = ("Воу, Воу! Полегче!", "Жгёшь! Давай ещё!", "Сервера легли!", "Даже Дуров охренел")
