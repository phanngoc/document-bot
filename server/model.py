from peewee import Model, SqliteDatabase, CharField, DateTimeField, ForeignKeyField, IntegerField, TextField, BooleanField, ManyToManyField
from datetime import datetime
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash

db = SqliteDatabase('../chatbot.db')

class BaseModel(Model):
    class Meta:
        database = db

class Assistant(BaseModel):
    id = IntegerField(primary_key=True)
    url = CharField(unique=True)
    name = CharField()
    settings = TextField(null=True)  # Thêm trường settings
    tool = CharField(null=True)  # Thêm trường tool
    is_builded = BooleanField(default=False)
    is_crawled = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    tools = TextField(null=True)  # Thêm trường để lưu trữ công cụ tương ứng
    # Thêm các trường cho gmail_tool và quickstart_tool nếu cần thiết
class User(BaseModel):
    name = CharField()
    email = CharField(unique=True)
    password = CharField()
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    assistants = ManyToManyField(Assistant, backref='users')

    @classmethod
    def create_user(cls, name, email, password):
        hashed_password = generate_password_hash(password)
        return cls.create(name=name, email=email, password=hashed_password)

    @classmethod
    def authenticate(cls, email, password):
        user = cls.get_or_none(cls.email == email)
        if user and check_password_hash(user.password, password):
            return user
        return None

class MessageType(Enum):
    USER = 'user'
    BOT = 'bot'
    SYSTEM = 'system'
    ASSISTANT = 'assistant'
    FUNCTION = 'function'
    TOOL = 'tool'

class Thread(BaseModel):
    id = IntegerField(primary_key=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    user = ForeignKeyField(User, backref='threads', null=True)
    uuid = CharField(max_length=200, unique=True, null=True, index=True)



class Message(BaseModel):
    user = ForeignKeyField(User, backref='messages', null=True)
    assistant = ForeignKeyField(Assistant, backref='messages', null=True)
    thread = ForeignKeyField(Thread, backref='messages', null=True)  # Add thread field
    type = CharField(choices=[(tag, tag.value) for tag in MessageType])
    message = CharField()
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

class Page(BaseModel):
    class Meta:
        table_name = 'pages'
    url = CharField(unique=True)
    text_content = TextField()
    assistant = ForeignKeyField(Assistant, backref='pages')
    created_at = DateTimeField(default=datetime.now)
    # updated_at = DateTimeField(default=datetime.now)

class UserAssistant(BaseModel):
    user = ForeignKeyField(User, backref='assistants')
    assistant = ForeignKeyField(Assistant, backref='users')

db.connect()
db.create_tables([User, Message, Page, Assistant, Thread, UserAssistant])
