from sqlalchemy import Column, DateTime, Integer, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TuroVehiclesTable(Base):
    __tablename__ = 'vehicles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer)
    vin = Column(String)
    year = Column(Integer)
    nickname = Column(String)
    make = Column(String)
    model = Column(String)
    color = Column(String)
    purchase_mileage = Column(Integer)
    purchase_date = Column(DateTime)
    purchase_price = Column(Integer)
    purchase_value = Column(Integer)
    last_mileage = Column(Integer)
    last_value = Column(Integer)
    last_date = Column(DateTime)
