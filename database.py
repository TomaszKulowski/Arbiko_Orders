from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from models import Base
from protection import Protection


class Database:
    def __init__(self, database_path):
        self.database_path = database_path
        self.engine = create_engine(f'sqlite:///:memory:', future=True)
        self.session = None

    def __enter__(self):
        self.create_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        Protection(self.database_path).save_database_dump(self.dump())

    def add_new_records(self, models: list):
        self.session.add_all(models)
        self.session.commit()

    def create_database(self):
        if self.database_path.exists():
            raise FileExistsError

        Base.metadata.create_all(self.engine)

    def create_session(self):
        with Session(self.engine) as session:
            self.session = session

    def dump(self) -> bytes:
        connection = self.engine.raw_connection()
        result = b''

        for line in connection.iterdump():
            result += bytes('%s\n', 'utf8') % bytes(line, 'utf8')

        return result

    def load(self):
        content = Protection(self.database_path).decrypt_file()
        scripts = content.split(';')
        for script in scripts:
            self.session.execute(text(script))
