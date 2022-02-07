#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3


class MetaSingleton(type):
    _instances = {}

    def __call__(cls, chat_id, *args, **kwargs):
        fname = f"database_id{chat_id}.db"
        if fname not in cls._instances:
            cls._instances[fname] = super(MetaSingleton, cls).__call__(fname, *args, **kwargs)
        return cls._instances[fname]

class SqLiter(metaclass=MetaSingleton):
    def __init__(self, db_file, check_same_thread=False):
        self.conn = sqlite3.connect(db_file, check_same_thread=check_same_thread)
        self.cur = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # self.cur.execute("PRAGMA foreign_keys=on;")
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS place(
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
        );
        """)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS things(
        id INTEGER PRIMARY KEY,
        thing TEXT,
        place_id INTEGER NOT NULL,
        FOREIGN KEY (place_id) REFERENCES place(id)
        );
        """)
        self.conn.commit()

    def add_place(self, name):
        self.cur.execute(
            "INSERT INTO place(name) VALUES(?);",
            [name]
        )
        self.conn.commit()

    def places(self):
        self.cur.execute("SELECT name, id FROM place;")
        return self.cur.fetchall()

    def add(self, thing, place_id):
        self.cur.execute(
            "INSERT INTO things(thing, place_id) VALUES(?, ?);",
            [thing, place_id]
        )
        self.conn.commit()

    def remove(self, id):
        self.cur.execute("DELETE FROM things WHERE id=?;", [id])
        self.conn.commit()

    def search(self, num):
        self.cur.execute("""
                SELECT thing, place.name
                FROM things
                LEFT JOIN place ON place_id=place.id
                WHERE thing LIKE ?
                ORDER BY thing;
                """, [f'%{num}%'])
        return self.cur.fetchall()

if __name__ == "__main__":
    base = SqLiter("-1001565062242")
    # base.add_place("коробка №1")
    # base.add_place("полка сверху")
    # base.add_place("полка снизу")
    # base.add_place("хорошая полка")
    # base.add("7658432", 3)
    # base.add("8567545", 1)
    # base.add("5554667", 2)
    # base.add("5675676", 4)
    # base.add("4657767", 3)
    # base.add("9247555", 1)
    # base.add("2323444", 2)
    # base.add("5675656", 4)
    print(base.places())
