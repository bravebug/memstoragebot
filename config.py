#!/usr/bin/env python
import os

basedir = os.path.abspath(os.path.dirname(__file__))

TRUE_SYNONYMS = (
    '1',
    'on',
    't',
    'true',
    'y',
    'yes',
)

FALSE_SYNONYMS = (
    '0',
    'f',
    'false',
    'n',
    'no',
    'off',
)

class Config:
    SQLALCHEMY_COMMIT_ON_TEARDPWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_DEPLOYMENT_KEY = os.environ.get('DEPLOYMENT_KEY') or "memstoragebot secret"

    RE_ITEM_ADD_FORMAT = r'^[\d]{7,8}$'
    RE_ITEM_SEARCH_FORMAT = r'^[\d]{4,8}$'
    SEPARATORS = r'[,;\n\t]'


class DevelopmentConfig(Config):
    DEBUG = True
    TOKEN = os.environ.get('DEV_TOKEN') or os.environ.get('TOKEN')
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DEV_DATABASE_URL')
        or os.environ.get('DATABASE_URL')
        or f'sqlite:///{os.path.join(basedir, "db/data_dev.sqlite")}'
    )
    SQLALCHEMY_DATABASE_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    TOKEN = os.environ.get('TOKEN')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "db/data.sqlite")}'
    SQLALCHEMY_DATABASE_ECHO = False


def make_config():
    if os.environ.get('DEV_MODE', '').lower() in TRUE_SYNONYMS:
        return DevelopmentConfig()
    else:
        return ProductionConfig()
