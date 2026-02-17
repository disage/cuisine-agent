from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine("sqlite:///recipes.db", echo=True)
SessionLocal = sessionmaker(bind=engine)


class Dialog(Base):
    __tablename__ = "dialogs"

    id = Column(Integer, primary_key=True)
    question = Column(String)
    answer = Column(String)
    cuisine = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
