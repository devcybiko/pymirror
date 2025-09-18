from dataclasses import dataclass
from munch import DefaultMunch, Munch
from sqlalchemy import MetaData, Table, create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

from pymirror.utils import from_dict

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

    def create_table(self, table: Table, checkfirst=True):
        table.__table__.create(self.engine, checkfirst=checkfirst)

    def to_dict(self, record) -> dict:
        return {c.name: getattr(record, c.name) for c in record.__table__.columns}

    def get(self, table: Table, key) -> dict:
        record = self.session.query(table).get(key)
        return self.to_dict(record)

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

