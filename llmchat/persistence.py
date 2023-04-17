import sqlite3
import discord


class PersistentData:
    def __init__(self, client: discord.Client, db_path: str = "persistent.db"):
        self.client = client
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute(
            """
    CREATE TABLE IF NOT EXISTS message_history (
        author_id INTEGER,
        content TEXT,
        message_id INTEGER
    )
	"""
        )
        self.cursor.execute(
            """
    CREATE TABLE IF NOT EXISTS user_identities (
        user_id INTEGER UNIQUE,
        identity TEXT,
        name TEXT
    )
	"""
        )
        self.connection.commit()

    def clear(self):
        self.cursor.execute("DELETE FROM message_history")
        self.connection.commit()
        self.create_table()

    def append(self, message: discord.Message):
        self.cursor.execute(
            "INSERT INTO message_history VALUES (?, ?, ?)",
            (message.author.id, message.content, message.id),
        )
        self.connection.commit()

    def speech(self, author: discord.User, content: str):
        self.cursor.execute(
            "INSERT INTO message_history VALUES (?, ?, ?)", (author.id, content, -1)
        )
        self.connection.commit()

    def system(self, content: str, message_id: int):
        self.cursor.execute(
            "INSERT INTO message_history VALUES (?, ?, ?)", (-1, content, message_id)
        )
        self.connection.commit()

    def remove(self, message_id: int):
        self.cursor.execute(
            "DELETE FROM message_history WHERE message_id = ?", (message_id,)
        )
        self.connection.commit()

    def set_identity(self, user_id: int, name: str, identity: str):
        self.cursor.execute(
            "INSERT OR REPLACE INTO user_identities (user_id, name, identity) VALUES (?, ?, ?)",
            (user_id, name, identity),
        )
        self.connection.commit()

    def get_identity(self, user_id: int):
        self.cursor.execute(
            "SELECT name,identity FROM user_identities WHERE user_id = ?", (user_id,)
        )
        row = self.cursor.fetchone()
        return row

    @property
    def last(self):
        self.cursor.execute(
            "SELECT * FROM message_history ORDER BY ROWID DESC LIMIT 1"
        )
        row = self.cursor.fetchone()
        return row

    def get_recent_messages(self, count: int):
        self.cursor.execute(
            "SELECT author_id, content, message_id FROM message_history ORDER BY ROWID DESC LIMIT ?",
            (count,),
        )
        rows = self.cursor.fetchall()
        rows.reverse()
        return rows

    def edit(self, message_id: int, new_content: str):
        self.cursor.execute(
            "UPDATE message_history SET content = ? WHERE message_id = ?",
            (new_content, message_id)
        )
        self.connection.commit()

    def query(self, author=None, content=None, message_id=None):
        query = "SELECT * FROM message_history"
        conditions = []
        values = []

        if author is not None:
            conditions.append("author_id = ?")
            values.append(author.id)

        if content is not None:
            conditions.append("content = ?")
            values.append(content)

        if message_id is not None:
            conditions.append("message_id = ?")
            values.append(message_id)

        if len(conditions) > 0:
            query += " WHERE " + " AND ".join(conditions)

        self.cursor.execute(query, tuple(values))
        rows = self.cursor.fetchall()
        return rows
