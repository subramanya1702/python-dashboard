import os

import psycopg2
from dotenv import load_dotenv


# PostgresDB class
# Initializes a connection object using the env file
# and exposes a function to retrieve the connection object for querying the postgresDB
class PostgresDB:
    __connection_object = None

    def __init__(self):
        try:
            load_dotenv("./local.env")
            self.__connection_object = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST"),
                database=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                port=os.getenv("POSTGRES_PORT")
            )
        except Exception:
            print("Exception while creating a database connection")

        if self.__connection_object is None:
            print("Unable to retrieve connection object")


def get_connection_object(self):
    return self.__connection_object
