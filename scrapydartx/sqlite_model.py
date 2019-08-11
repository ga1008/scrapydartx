from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, TIMESTAMP, text, TEXT
from sqlalchemy.orm import sessionmaker
from twisted.logger import Logger
import datetime


engine = create_engine('sqlite:///sqlite_2.db?check_same_thread=False', echo=False)
Base = declarative_base()

logger = Logger(namespace='- MODEL -')


class SpiderMonitor(Base):
    __tablename__ = 'spider_monitor'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project = Column(String(200))
    spider = Column(String(255))
    runtime = Column(String(100))
    job_id = Column(String(100))
    create_time = Column(String(25))

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class UnormalSpider(Base):
    __tablename__ = 'unormal_spider'
    id = Column(Integer, primary_key=True, autoincrement=True)
    spider = Column(String(255))
    create_time = Column(String(25))

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class TerminatedSpider(Base):
    __tablename__ = 'terminated_spider'
    id = Column(Integer, primary_key=True, autoincrement=True)
    spider = Column(String(255))
    job_id = Column(String(255))
    create_time = Column(String(25))

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class SpiderScheduleModel(Base):
    __tablename__ = 'spider_schedule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project = Column(String(255), nullable=False)
    spider = Column(String(255), nullable=False)
    schedule = Column(String(255), nullable=False)
    args = Column(String(255), nullable=True)
    status = Column(Integer, nullable=False, default=0)
    create_time = Column(String(25))

    def to_dict(self):
        return {c.name: getattr(self, c.name, None)
                for c in self.__table__.columns}


model_dic = {
    'SpiderScheduleModel': SpiderScheduleModel,
    'TerminatedSpider': TerminatedSpider,
    'UnormalSpider': UnormalSpider,
    'SpiderMonitor': SpiderMonitor,
    # 'User': User,
}


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
