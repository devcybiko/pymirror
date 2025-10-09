from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from pmdb.pmdb import Base
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class IcalTable(Base):
    __tablename__ = 'ical'
    id = Column(Integer, primary_key=True)
    calendar_name = Column(String)
    all_day = Column(Boolean)
    dtstart = Column(DateTime)
    dtend = Column(DateTime)
    utc_start = Column(Float)
    utc_end = Column(Float)
    summary = Column(String)
    description = Column(String)
    rrule = Column(String)
    uid = Column(String, unique=True)
