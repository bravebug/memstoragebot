#!/usr/bin/env python
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SQLALCHEMY_COMMIT_ON_TEARDPWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_DEPLOYMENT_KEY = os.environ["DEPLOYMENT_KEY"]

    MSG_NOT_FOUND = 'Поищи в ячейке по номеру заказа'  # добавить в редактируемое поле в настройки инстанса

    RE_ITEM_ADD_FORMAT = r'^[\d]{7,8}$'
    RE_ITEM_SEARCH_FORMAT = r'^[\d]{4,8}$'
    SEPARATORS = r'[,;\n\t]'
    NAME_CHARS = r'[\w_-]+'
    START_TEXT = (
        "Меня зовут Полочка! Я могу запомнить что и где лежит!",
        "Управляй мной такими командами:",
        "/add_location [РАСПОЛОЖЕНИЕ …] - добавляет РАСПОЛОЖЕНИЕ.",
        "/add [ОБЪЕКТ1 ОБЪЕКТ2 …] - добавляет ОБЪЕКТЫ в РАСПОЛОЖЕНИЕ.",
        "- [ОБЪЕКТ1 ОБЪЕКТ2 …] - удаляет ОБЪЕКТ со всех МЕСТ.",
        "/csv - экспортирует данные в файл csv.",
        "/roll УЧАСТНИК1 УЧАСТНИК2 … - бросает жребий между участниками.",
        "/help - выводит эту справку.",
    )
    HELP_TEXT = (
        "Меня зовут Полочка! Я могу запомнить что и где лежит!",
        "Управляй мной такими командами:",
        "/add_location [РАСПОЛОЖЕНИЕ …] - добавляет РАСПОЛОЖЕНИЕ.",
        "/add [ОБЪЕКТ1 ОБЪЕКТ2 …] - добавляет ОБЪЕКТЫ в РАСПОЛОЖЕНИЕ.",
        "- [ОБЪЕКТ1 ОБЪЕКТ2 …] - удаляет ОБЪЕКТ со всех МЕСТ.",
        "/csv - экспортирует данные в файл csv.",
        "/roll УЧАСТНИК1 УЧАСТНИК2 … - бросает жребий между участниками.",
        "/help - выводит эту справку.",
    )
    ABOUT_TEXT = (
        "memstoragebot - бот telegram для создания каталога хранения чего либо где либо.",
        "С более подробной информацией Вы можете ознакомится на странице проекта:",
        "http://io.org.ru/o/KfxfAm",
        "Поддержать проект можно по ссылке: http://io.org.ru/o/MomKfx"
    )


class DevelopmentConfig(Config):
    DEBUG = True
    TOKEN = os.environ["DEV_TOKEN"]
    SQLALCHEMY_DATABASE_URI = os.environ.get("DEV_DATABASE_URL") or \
        f"sqlite:///{os.path.join(basedir, 'db/data_dev.sqlite')}"
    SQLALCHEMY_DATABASE_ECHO = False


class ProductionConfig(Config):
    DEBUG = True
    TOKEN = os.environ["TOKEN"]
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        f"sqlite:///{os.path.join(basedir, 'db/data.sqlite')}"
    SQLALCHEMY_DATABASE_ECHO = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

if __name__ == "__main__":
    conf = DevelopmentConfig()
