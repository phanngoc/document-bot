from peewee import Model, SqliteDatabase, CharField, DateTimeField, ForeignKeyField, IntegerField, TextField
from datetime import datetime
from enum import Enum

db = SqliteDatabase('chatbot.db')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    name = CharField()
    email = CharField(unique=True)
    password = CharField()
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

class MessageType(Enum):
    USER = 'user'
    BOT = 'bot'
    SYSTEM = 'system'
    ASSISTANT = 'assistant'
    FUNCTION = 'function'
    TOOL = 'tool'

class Message(BaseModel):
    user = ForeignKeyField(User, backref='messages', null=True)
    type = CharField(choices=[(tag, tag.value) for tag in MessageType])
    message = CharField()
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

class Page(BaseModel):
    class Meta:
        table_name = 'pages'
    url = CharField(unique=True)
    text_content = TextField()
    created_at = DateTimeField(default=datetime.now)
    # updated_at = DateTimeField(default=datetime.now)

# db.connect()
# db.create_tables([User, Message, Page])
