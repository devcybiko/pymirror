from dataclasses import dataclass
from munch import DefaultMunch, Munch
from sqlalchemy import MetaData, Table, create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

from pymirror.utils.utils import from_dict
from pymirror.pmlogger import _debug

Base = declarative_base()

@from_dict
@dataclass
class PMDbConfig:
    url: str = "sqlite:///pmdb.db"

class PMDb:
    def __init__(self, config: dict):
        self._pmdb = PMDbConfig.from_dict(config)
        self.engine = create_engine(self._pmdb.url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create_table(self, table: Table, checkfirst=True, force=False):
        try:
            _debug("creating table...")
            table.__table__.create(self.engine, checkfirst=checkfirst)
        except Exception as e:
            _debug("create_table failed...")
            if force:
                _debug("...trying to drop it and recreate...")
                try:
                    table.__table__.drop(self.engine)
                    table.__table__.create(self.engine, checkfirst=checkfirst)
                except Exception as e:
                    raise e
            else:
                raise e

    def rollback(self):
        self.session.rollback()

    def commit(self):
        try:
            self.session.commit()
        except Exception as e:
            self.rollback()
            raise e

    def upsert(self, record: Table):
        self.session.merge(record)
        self.commit()

    def get(self, table: Table, key) -> "Table":
        record = self.session.query(table).get(key)
        return record

    def get_all(self, table: Table) -> list["Table"]:
        records = self.session.query(table).all()
        return records

    def get_where(self, table: Table, **kwargs) -> "Table":
        record = self.session.query(table).filter_by(**kwargs).first()
        return record

    def get_all_where(self, table: Table, where_clause) -> list["Table"]:
        records = self.session.query(table).filter(where_clause)
        return records

    def delete(self, record: Table):
        self.session.delete(record)
        self.commit()

if __name__ == "__main__":
    def main():
        class Task(Base):
            __tablename__ = 'tasks'
            id = Column(Integer, primary_key=True)
            name = Column(String)

        config = DefaultMunch(url="sqlite:///pymirror.db")
        pmdb = PMDb(config)
        # Add a task
        task = Task(name="Example Task")
        pmdb.session.add(task)
        pmdb.session.commit()

    main()

