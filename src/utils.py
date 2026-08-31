import sqlite3 as sql
import discord
import time
import difflib
import json
import re
import asyncio
import os
from constants import *

def user_has_role(user, role_id):
    try:
        if any(role.id == role_id for role in user.roles):
            return True
    except AttributeError:
        print("AttributeError")
    return False

def get_json(filepath):
    with open("src/data/" + filepath, "r") as f:
        return json.loads(f.read())

def is_mod(user):
    return user_has_role(user, MOD_ROLE_ID)

class BotDatabase:
    _instance = None
    def __init__(self):
        if BotDatabase._instance is not None:
            raise RuntimeError("Use BotDatabase.instance()")
        self.data = sql.connect("src/bot.db", check_same_thread=False)
        self.data.row_factory = sql.Row
        self._create_tables()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _create_tables(self):
        self.data.execute("""
        CREATE TABLE IF NOT EXISTS hof_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT NOT NULL
        )
        """)
        self.data.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            date TEXT NOT NULL,
            content TEXT NOT NULL
        )
        """)
        self.data.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            data_collect INTEGER DEFAULT 1 NOT NULL,
            points INTEGER DEFAULT 0 NOT NULL
        )
        """)
        self.data.execute("""
        CREATE TABLE IF NOT EXISTS game_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            private INTEGER NOT NULL,
            channel TEXT
        )
        """)


    def hof_message_exists(self, message_id):
        result = self.data.execute("SELECT EXISTS(SELECT 1 FROM hof_messages WHERE message_id=?)",
                                 (message_id,)).fetchone()
        return bool(result[0])
    def add_hof_message(self, message_id):
        self.data.execute("""
        INSERT INTO hof_messages (message_id)
        VALUES(?)
        """, (str(message_id),))
        self.data.commit()
    def get_user(self, user_id, guild_id):
        return self.data.execute("""
        SELECT * FROM members WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id,)).fetchone()
    def add_user(self, user_id, guild_id):
        self.data.execute("""
        INSERT INTO members(guild_id, user_id, data_collect, points)
        VALUES(?, ?, ?, ?)
        """, (guild_id, user_id, 1, 0))
        self.data.commit()
    def update_points(self, guild_id, user_id, points):
        if self.get_user(user_id, guild_id) == None:
            self.add_user(user_id, guild_id)
        content = self.get_user(user_id, guild_id)
        new_points = content["points"]+points
        self.data.execute("""
        UPDATE members SET points = ? WHERE user_id = ? AND guild_id = ?
        """, (new_points, user_id, guild_id))
        self.data.commit()
    def add_game_session(self, user_id, private, channel_id):
        self.data.execute("""
        INSERT INTO game_sessions(user_id, private, channel)
        VALUES(?, ?, ?)
        """, (user_id, private, channel_id))
