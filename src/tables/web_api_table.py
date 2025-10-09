from sqlalchemy import Column, DateTime, Integer, String, and_
from pmdb.pmdb import Base
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class WebApiTable(Base):
    __tablename__ = 'webapi'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    last_time = Column(DateTime)
    last_rc = Column(Integer)
    rate_limit_secs = Column(Integer)
    retry_after_secs = Column(Integer)
    result_text = Column(String)
    params = Column(String)
