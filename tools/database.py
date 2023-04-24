"""The collections of tools to manage the database."""
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from typing import Type

from credentials import database_password
from tools.models import Base
from tools.protection import Protection


class Database:
    """The collections of the tools to manage the database.
    The class has implemented the necessary methods to use as a context manager.

    Methods:
         create_database(): create the database if not exists
         dump(): dump the data from the database and return as bytes
         load(): load the data from the protected file and load it to database
    """
    def __init__(self, database_path: Type[Path]):
        """Construct all the necessary attributes for the database object.

        Args:
            database_path (Type[Path]): database path
        """
        self.database_path = database_path
        self.engine = create_engine(f'sqlite:///:memory:', future=True)
        self.session = None

    def __enter__(self):
        self.create_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        Protection(database_password, self.database_path).save_database_dump(self.dump())

    def create_database(self):
        """Create the database if not exists."""
        if self.database_path.exists():
            raise FileExistsError

        Base.metadata.create_all(self.engine)

    def create_session(self):
        """Create database session."""
        with Session(self.engine) as session:
            self.session = session

    def dump(self) -> bytes:
        """Dump the data from the database and return as bytes."""
        connection = self.engine.raw_connection()
        result = b''

        for line in connection.iterdump():
            result += bytes('%s\n', 'utf8') % bytes(line, 'utf8')

        return result

    def load(self):
        """Load the data from the protected file and load it to database."""
        content = Protection(self.database_path).decrypt_file()
        scripts = content.split(';')
        for script in scripts:
            self.session.execute(text(script))
