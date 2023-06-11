#!/usr/bin/env python
# from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.orm import mapped_column, relationship, sessionmaker
from sqlalchemy.exc import NoResultFound
from typing import List


class Base(DeclarativeBase):
    pass


class Thing(Base):
    __tablename__ = "thing_table"

    id:             Mapped[int]             = mapped_column(primary_key=True)
    name:           Mapped[str]             = mapped_column(index=True)
    entries:        Mapped[List["Entry"]]   = relationship(back_populates="thing", cascade="all, delete-orphan")
    last_queried:   Mapped[datetime]        = mapped_column(default=datetime.utcnow())


class LocationName(Base):
    __tablename__ = "location_name_table"

    id:             Mapped[int]             = mapped_column(primary_key=True)
    name:           Mapped[str]             = mapped_column(index=True)


class Location(Base):
    __tablename__ = "location_table"

    id:             Mapped[int]             = mapped_column(primary_key=True)
    name_id:        Mapped[str]             = mapped_column(ForeignKey("location_name_table.id"))
    name:           Mapped["LocationName"]  = relationship()
    instance_id:    Mapped[int]             = mapped_column(ForeignKey("instance_table.id"))
    instance:       Mapped["Instance"]      = relationship(back_populates="locations")
    entries:        Mapped[List["Entry"]]   = relationship(back_populates="location", cascade="all, delete-orphan")


class Instance(Base):
    __tablename__ = "instance_table"

    id:             Mapped[int]                 = mapped_column(primary_key=True)
    name:           Mapped[str]                 = mapped_column(unique=True, index=True)
    locations:      Mapped[List["Location"]]    = relationship(back_populates="instance")
    entries:        Mapped[List["Entry"]]       = relationship(back_populates="instance")
    last_queried:   Mapped[datetime]            = mapped_column(default=datetime.utcnow())


class Description(Base):
    __tablename__ = "description_table"

    id:             Mapped[int]         = mapped_column(primary_key=True)
    text:           Mapped[str]         = mapped_column(unique=True, index=True)
    last_queried:   Mapped[datetime]    = mapped_column(default=datetime.utcnow())


# class User(Base):
    # __tablename__ = "user_table"

    # id:             Mapped[int] = mapped_column(primary_key=True)
    # tg_id:          Mapped[str] = mapped_column(index=True)
    # tg_chat_id:     Mapped[str] = mapped_column(index=True)
    # name:           Mapped[str]
    # search_count:   Mapped[int] = mapped_column(default=0)
    # adding_count:   Mapped[int] = mapped_column(default=0)
    # decent_count:   Mapped[int] = mapped_column(default=0)


class Entry(Base):
    __tablename__ = "entry_table"

    id:             Mapped[int]             = mapped_column(primary_key=True)
    thing_id:       Mapped[int]             = mapped_column(ForeignKey("thing_table.id"))
    thing:          Mapped["Thing"]         = relationship(back_populates="entries")
    location_id:    Mapped[int]             = mapped_column(ForeignKey("location_table.id"))
    location:       Mapped["Location"]      = relationship(back_populates="entries")
    instance_id:    Mapped[int]             = mapped_column(ForeignKey("instance_table.id"))
    instance:       Mapped["Instance"]      = relationship(back_populates="entries")
    description_id: Mapped[int | None]      = mapped_column(ForeignKey("description_table.id"))
    description:    Mapped["Description"]   = relationship()
    quantity:       Mapped[int]             = mapped_column(default=0)
    created_on:     Mapped[datetime]        = mapped_column(default=datetime.utcnow())
    updated_on:     Mapped[datetime]        = mapped_column(default=datetime.utcnow(), onupdate=datetime.utcnow())


# class EntryLog(Base):
    # __tablename__ = "entry_log_table"

    # id:         Mapped[int]         = mapped_column(primary_key=True)
    # user_id:    Mapped[str]         = mapped_column(index=True)
    # text:       Mapped[str]         = mapped_column(index=True)
    # user_id:    Mapped[int]         = mapped_column(ForeignKey("user_table.id"))
    # datetime:   Mapped[DateTime]    = mapped_column(DateTime, default=datetime.utcnow) # верный тип объекта?


class InstanceConfig(Base):
    __tablename__ = "config_table"

    id:             Mapped[int] = mapped_column(primary_key=True)
    instance_id:    Mapped[str] = mapped_column(unique=True, index=True)
    key:            Mapped[str] = mapped_column(unique=True, index=True)
    value:          Mapped[str]


def create_session(database_uri, echo=False):
    engine = create_engine(database_uri, echo=echo)
    Base.metadata.create_all(engine)
    return sessionmaker(engine)


if __name__ == "__main__":
    pass
