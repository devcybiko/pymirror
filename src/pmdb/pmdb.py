from dataclasses import dataclass
from icecream import ic
from munch import DefaultMunch, Munch
from sqlalchemy import MetaData, Table, create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

from pymirror.utils import from_dict
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

    def upsert(self, record: Table):
        self.session.merge(record)
        self.session.commit()

    def get(self, table: Table, key) -> Munch:
        record = self.session.query(table).get(key)
        return record

    def get_where(self, table: Table, **kwargs) -> dict:
        record = self.session.query(table).filter_by(**kwargs).first()
        return record

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

