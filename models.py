from database import Base
from sqlalchemy import Column, Integer, String


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
