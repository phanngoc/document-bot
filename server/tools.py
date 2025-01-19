import mysql.connector
import uuid

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from typing import List, Optional
from typing_extensions import Annotated

llm = ChatOpenAI(model="gpt-4o")


class SchemaAnalyzer:
    def __init__(self, host, user, password, database, port):
        self.reinit_connection(host, user, password, database, port)

    def reinit_connection(self, host, user, password, database, port):
        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        self.cursor = self.connection.cursor()
        self.analyze_schema()
        self.table_name_list = list(self.schema.keys())

    def get_table_name_list(self):
        table_name_list = list(self.schema.keys())
        return table_name_list

    def analyze_schema(self):
        self.schema = {}
        self.cursor.execute("SHOW TABLES")
        tables = self.cursor.fetchall()

        for table in tables:
            table_name = table[0]
            self.schema[table_name] = {
                "columns": [],
                "foreign_keys": []
            }
            self._analyze_columns(table_name)
            self._analyze_foreign_keys(table_name)

    def _analyze_columns(self, table_name):
        self.cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = self.cursor.fetchall()
        for column in columns:
            self.schema[table_name]["columns"].append(column[0])

    def _analyze_foreign_keys(self, table_name):
        self.cursor.execute(f"""
            SELECT
                column_name,
                referenced_table_name,
                referenced_column_name
            FROM
                information_schema.key_column_usage
            WHERE
                table_name = '{table_name}' AND
                referenced_table_name IS NOT NULL
        """)
        foreign_keys = self.cursor.fetchall()
        for fk in foreign_keys:
            self.schema[table_name]["foreign_keys"].append({
                "column": fk[0],
                "referenced_table": fk[1],
                "referenced_column": fk[2]
            })

    def get_schema(self):
        return self.schema

    def format_table_columns(self, table):
        tables_results = []
        response_text = ""
        for table_name in table.name:
            tables_results.append(table_name)
            response_text += f"Table: {table_name} "
            response_text += f" Columns:{', '.join(self.schema[table_name]['columns'])}"

        return response_text

class DatabaseConnection(BaseModel):
    """Database connection information."""
    host: str = Field(description="Host of the database.")
    user: str = Field(description="User of the database.")
    password: str = Field(description="Password of the database.")
    database: str = Field(description="Database name.")
    port: int = Field(description="Port of the database.")

analyzer = SchemaAnalyzer(
    host='127.0.0.1',
    user='root',
    password='root',
    database='eccubedb',
    port=13306
)

class Table(BaseModel):
    """List tables name in SQL database."""
    name: List[str] = Field(description="List of tables name in SQL database.")

@tool
def extract_list_tables_relavance(query: str, database_connection: Optional[DatabaseConnection] = None):
    """ Return the names of ALL the SQL tables that MIGHT be relevant to the user question.
        Args:
            query (str): The user's query.
            database_connection (DatabaseConnection): The database connection information.
    """
    if database_connection:
        analyzer.reinit_connection(
            host=database_connection.host,
            user=database_connection.user,
            password=database_connection.password,
            database=database_connection.database,
            port=database_connection.port
        )

    table_name_list = analyzer.get_table_name_list()
    print("call tool:extract_list_tables_relavance", query)
    system = f"""
        Return the names of ALL the SQL tables that MIGHT be relevant to the user question. \
        The tables are:
        {table_name_list}
        Remember to include ALL POTENTIALLY RELEVANT tables, even if you're not sure that they're needed.
        Output:
        "table_name1", "table_name2"
        """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "{input}"),
        ]
    )

    prompt = prompt | llm.with_structured_output(Table)

    prompt_value = prompt.invoke({"input": query})
    response_text = analyzer.format_table_columns(prompt_value)
    print("prompt_value", response_text)
    return response_text


@tool
def get_database_connection_info(query: str):
    """Provide the necessary information for connecting to the database."""
    print("tool:get_database_connection_info", query)
    
    structured_llm = llm.with_structured_output(DatabaseConnection)
    database_connect = structured_llm.invoke(query)

    return database_connect