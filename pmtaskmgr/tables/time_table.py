from sqlalchemy import Float, Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TimeTable(Base):
    __tablename__ = 'time'
    id = Column(Integer, primary_key=True)
    epoch = Column(Float)
    local_date = Column(String)
    local_time = Column(String)
    local_datetime = Column(String)
    utc_date = Column(String)
    utc_time = Column(String)
    utc_datetime = Column(String)
