use peewee + sqlite , 
    add entity user (id, name, email, password, created_at, updated_at)
    add entity: messages 
        (id, user_id (FK) nullable, type (enum: user, bot), 
         message, created_at, updated_at)


---

use llama_index + chroma for save vector embedding