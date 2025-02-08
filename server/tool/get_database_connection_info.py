from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional
import mysql.connector

llm = ChatOpenAI(model="gpt-4o")


class DatabaseConnection(BaseModel):
    """Database connection information."""
    host: str = Field(description="Host of the database.")
    user: str = Field(description="User of the database.")
    password: str = Field(description="Password of the database.")
    database: str = Field(description="Database name.")
    port: int = Field(description="Port of the database.")

@tool
def get_database_connection_info(query: str):
    """Extract the connection information for the database."""
    print("tool:get_database_connection_info", query)
    
    structured_llm = llm.with_structured_output(DatabaseConnection)
    database_connect = structured_llm.invoke(query)

    return database_connect 