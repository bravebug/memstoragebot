#!/usr/bin/env python

from models import Description, Entry, Instance, InstanceConfig, LocationName, Location, Thing, NoResultFound
from models import delete, select, update, create_session

from datetime import datetime
from functools import lru_cache
from hashlib import blake2s
from typing import Callable


class DataBase:
    def __init__(self, database_uri, echo, deployment_key, clear_text: Callable = lambda s: s):
        self.Session = create_session(database_uri=database_uri, echo=echo)
        self.clear_text = clear_text
        self.deployment_key_digest = blake2s(
            str(deployment_key).encode(),
            digest_size=8,
        ).digest()

    @lru_cache
    def hasher(self, identifier):
        return blake2s(
            str(identifier).encode(),
            person=self.deployment_key_digest,
        ).hexdigest()

    def __get_or_add_item(self, params: dict, model: [Description, Location, Thing], session):
        try:
            item = session.query(model).filter_by(**params).one()
            item.last_queried = datetime.utcnow()
        except NoResultFound:
            item = model(**params)
            session.add(item)
        finally:
            return item

    def add_location(self, name: str, instance_name: str):
        instance_name = self.hasher(instance_name)
        name = self.clear_text(name)
        with self.Session.begin() as session:
            instance = self.__get_or_add_item(params=dict(name=instance_name), model=Instance, session=session)
            location_name = self.__get_or_add_item(params=dict(name=name), model=LocationName, session=session)
            location = self.__get_or_add_item(
                params=dict(name=location_name, instance=instance),
                model=Location,
                session=session,
            )

    def rename_location(self, id: str, name: str, instance_name: str):
        instance_name = self.hasher(instance_name)
        name = self.clear_text(name)
        with self.Session.begin() as session:
            instance = self.__get_or_add_item(params=dict(name=instance_name), model=Instance, session=session)
            location_name = self.__get_or_add_item(params=dict(name=name), model=LocationName, session=session)
            location = self.__get_or_add_item(params=dict(id=id, instance=instance), model=Location, session=session)
            location.name = location_name
            return location

    def add_entry(self, thing_name: str, quantity: int, description_text: str, location_id: int, instance_name, session):
        thing = self.__get_or_add_item(params=dict(name=thing_name), model=Thing, session=session)
        instance = self.__get_or_add_item(params=dict(name=instance_name), model=Instance, session=session)
        entry = self.__get_or_add_item(
            params=dict(thing=thing, location_id=location_id, instance=instance),
            model=Entry,
            session=session,
        )
        if not entry.quantity:
            entry.quantity = quantity
        elif entry.quantity + quantity >= 1:
            entry.quantity += quantity
        else:
            session.delete(entry)
            return
        if description_text and (description_text := self.clear_text(description_text)):
            if entry.description and entry.description.text != description_text:
                description_text = f"{entry.description.text}, {description_text}"
            entry.description = self.__get_or_add_item(
                params=dict(text=description_text),
                model=Description,
                session=session,
            )

    def add_entries(self, things: (str, int, str), location_id: int, instance_name):
        instance_name = self.hasher(instance_name)
        with self.Session.begin() as session:
            for thing_name, quantity, description_text in things:
                self.add_entry(thing_name, quantity, description_text, location_id, instance_name, session)

    def get_locations(self, instance_name, location_name=None):
        instance_name = self.hasher(instance_name)
        with self.Session.begin() as session:
            query = select(LocationName.name, Location.id)
            query = query.join(LocationName)
            query = query.join(Location.instance).where(Instance.name == instance_name)
            if location_name:
                query = query.where(LocationName.name == location_name)
            query = query.order_by(LocationName.name)
            return session.execute(query).all()

    def search_things(self, search_string, instance_name):
        instance_name = self.hasher(instance_name)
        with self.Session.begin() as session:
            query = select(
                Thing.name,
            )
            query = query.join(Entry)
            query = query.join(Entry.instance).where(Instance.name == instance_name)
            query = query.where(Thing.name.ilike(f"%{search_string}%"))
            query = query.group_by(Thing.name)
            return session.execute(query).fetchall()

    def search_entries(self, instance_name, equals=None, like=None, location_id=None):
        instance_name = self.hasher(instance_name)
        if not (equals and like):
            with self.Session.begin() as session:
                query = select(
                    Entry.id,
                    Thing.name,
                    LocationName.name,
                    Entry.quantity,
                    Description.text,
                )
                query = query.join(Thing).join(Location).join(Location.name).outerjoin(Description)
                query = query.join(Entry.instance).where(Instance.name == instance_name)
                if equals:
                    query = query.where(Thing.name == equals)
                if like:
                    query = query.where(Thing.name.ilike(f"%{like}%"))
                if location_id:
                    query = query.where(Location.id == location_id)
                return session.execute(query).fetchall()
        else:
            raise ValueError("It is acceptable to use only one of the arguments: equals or like")

    def remove_entries_by_ids(self, entry_ids):
        with self.Session.begin() as session:
            stmt = delete(Entry).where(Entry.id.in_(entry_ids))
            return session.execute(stmt)

    def remove_entries_by_location_id(self, location_id):
        with self.Session.begin() as session:
            stmt = delete(Entry).where(Entry.location_id == location_id)
            return session.execute(stmt)

    def remove_location_by_id(self, location_id):
        self.remove_entries_by_location_id(location_id)
        with self.Session.begin() as session:
            stmt = delete(Location).where(Location.id == location_id)
            return session.execute(stmt)

    def move_entries(self, location_to_id, entry_ids=None, location_from_id=None):
        with self.Session.begin() as session:
            entries = session.query(Entry).filter(Entry.location_id != location_to_id)
            if location_from_id:
                entries = entries.filter(Entry.location_id == location_from_id)
            if entry_ids:
                entries = entries.filter(Entry.id.in_(entry_ids))
            for entry in entries:
                new_entry = self.add_entry(
                    thing_name = entry.thing.name,
                    quantity = entry.quantity,
                    description_text = entry.description.text if entry.description else None,
                    location_id = location_to_id,
                    instance_name = entry.instance.name,
                    session = session,
                )
            entries.delete()


if __name__ == "__main__":
    from random import randint, choice
    from utils import remove_extra_spaces as clear_text
    from config import DevelopmentConfig
    conf = DevelopmentConfig()
    db = DataBase(
        database_uri=conf.SQLALCHEMY_DATABASE_URI,
        echo=conf.SQLALCHEMY_DATABASE_ECHO,
        deployment_key=conf.SQLALCHEMY_DATABASE_DEPLOYMENT_KEY,
        clear_text=clear_text,
    )

    def gen_data():
        for s in range(3):
            for p in range(6):
                db.add_location(f"{s+1}-{p+1}", instance_name="test")
        db.add_location("за дверью", instance_name="test")
        db.add_location("у подсобки", instance_name="test")
        db.add_location("документы", instance_name="test")

    def gen_entries():
        example_descriptions = (
            "химия",
            "хрупкое",
            "очень тяжело",
            "давать поштучно",
            "закончились идеи",
        )
        tmp = db.get_locations(instance_name="test")
        # for item in db.get_locations():
        for _ in range(30):
            location_name, location_id = choice(tmp)
            desc = None if randint(0, 1) else choice(example_descriptions)
            db.add_entries(
                things=((f"115{randint(00000, 99999)}", randint(1, 4), desc), ),
                location_id=location_id,
                instance_name="test",
            )
    # gen_data()
    # gen_entries()
    db.move_entries(location_from_id=19, location_to_id=15)
    # print(db.search_entries(instance_name="test"))
    # db.rename_location(id=6, name="переименование", instance_name="test")
    # print(db.search_entries(instance_name="test"))
    # db.add_entry(f"11664781", 2, quantity=5, description_text="химия")
    # db.add_entry(f"11664781", 2, quantity=1, description_text="очень тяжело, ldf, ldf")
    # db.add_entry(f"11664781", location_id=1, quantity=4, description_text="хрупкое, test, test")
    # print("Wrong id", db.search_entries("777777", instance_name="123"))
    # print("Right id", db.search_entries("777777", instance_name="test_user"))
