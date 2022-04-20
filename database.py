#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
# import sqlite_icu


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
        # self.conn.enable_load_extension(True)
        # self.conn.load_extension(sqlite_icu.extension_path().replace('.so', ''))
        self.cur = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cur.execute("PRAGMA foreign_keys=on;")
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS place(
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
        );
        """)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS things(
        id INTEGER PRIMARY KEY,
        thing TEXT NOT NULL COLLATE NOCASE,
        place_id INTEGER NOT NULL,
        FOREIGN KEY (place_id) REFERENCES place(item_id)
        );
        """)
        self.conn.commit()

    def add_places(self, places):
        for place in places:
            self.cur.execute(
                "INSERT INTO place(name) VALUES (?);",
                [place]
            )
        self.conn.commit()

    def places(self):
        self.cur.execute("SELECT id, name FROM place ORDER BY name;")
        return self.cur.fetchall()
    
    def placename_by_id(self, place_id):
        self.cur.execute("SELECT name FROM place WHERE id=?;", [place_id])
        return self.cur.fetchone()

    def add(self, items, place_id):
        for item in items:
            self.cur.execute(
                "INSERT INTO things(thing, place_id) VALUES(?, ?);",
                (item, place_id)
            )
        self.conn.commit()

    def remove_id(self, item_id):
        self.cur.execute("DELETE FROM things WHERE id=?;", [item_id])
        self.conn.commit()

    def remove_item(self, item):
        self.cur.execute("DELETE FROM things WHERE thing=?;", [item])
        self.conn.commit()

    def remove_items(self, items):
        for item in items:
            self.remove_item(item)

    def search(self, item):
        self.cur.execute("""
                SELECT thing, place.name
                FROM things
                LEFT JOIN place ON place_id=place.id
                WHERE LOWER(thing) LIKE LOWER(?)
                ORDER BY thing;
                """, [f'%{item}%'])
        return self.cur.fetchall()

    def take_all(self):
        self.cur.execute("""
                SELECT thing, place.name
                FROM things
                LEFT JOIN place ON place_id=place.id
                ORDER BY place.name, thing;
                """)
        return self.cur.fetchall()

    def inaccurate_search(self, item):
        return self.accurate_search(f"%{item}%")

    def accurate_search(self, item):
        self.cur.execute("""
                SELECT DISTINCT thing
                FROM things
                WHERE LOWER(thing) LIKE LOWER(?)
                ORDER BY thing;
                """, [item])
        return self.cur.fetchall()

    def search_places(self, item):
        self.cur.execute("""
                SELECT place.name, COUNT(place.id)
                FROM things
                LEFT JOIN place ON place_id=place.id
                WHERE LOWER(thing) = LOWER(?)
                GROUP BY place.id
                ORDER BY place.name;
                """, [item])
        return self.cur.fetchall()


if __name__ == "__main__":
    base = SqLiter("350999238")
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
    print(base.accurate_search("8243427"))
    # print(base.search_places("8116560"))
    # print(base.places())
    # print(base.search("Дима"))
    # print(base.add_places(["1-2", "1-3"]))
