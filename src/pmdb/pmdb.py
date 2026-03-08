from dataclasses import dataclass
import traceback
from munch import DefaultMunch, Munch
from sqlalchemy import MetaData, Table, create_engine, Column, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker

from glslib.dicts import from_dict
from glslib.logger import _debug, _error, tracebacker

Base = declarative_base()

class NullRecord:
    """Null object that mimics a database record"""
    def __init__(self, table_class=None):
        self.table_class = table_class
    
    def __getattr__(self, name):
        # Return None for any attribute access
        return None
    
    def __bool__(self):
        # Makes it falsy like None
        return False
    
    def __repr__(self):
        return f"<NullRecord for {self.table_class.__name__ if self.table_class else 'Unknown'}>"

global null_record
null_record = NullRecord()

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

    def query(self, sql: str, params=None):
        from sqlalchemy import text
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            keys = list(result.keys())
            result_list = [dict(zip(keys, row)) for row in result.fetchall()]
            return result_list

    def get(self, table: Table, key) -> "Table":
        record = self.session.query(table).get(key)
        return record

    @tracebacker([])
    def get_all(self, table: Table) -> list["Table"]:
        records = self.session.query(table).all()
        return records

    # @tracebacker(null_record)
    def get_where(self, table: Table, where_clause, order_by=None) -> list["Table"]:
        if type(where_clause) == str:
            where_clause = text(where_clause)
        query = self.session.query(table).filter(where_clause)
        if order_by is not None:
            query = query.order_by(order_by)
        print(query)
        records = query.first()
        return records

    @tracebacker([])
    def get_all_where(self, table: Table, where_clause, order_by=None) -> list["Table"]:
        if type(where_clause) == str:
            where_clause = text(where_clause)
        query = self.session.query(table).filter(where_clause)
        if order_by is not None:
            query = query.order_by(order_by)
        records = query.all()
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

