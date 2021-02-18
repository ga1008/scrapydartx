from sqlalchemy import Column, Integer, String, DateTime, TIMESTAMP, text
from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

user = 'quinns'
passwd = 'Quinns3000'
host = '192.168.0.61'
port = 3306
db = 'news_information'
charset = 'utf8'
conn = 'mysql+pymysql://%s:%s@%s:%s/%s?charset=%s' % (user, passwd, host, port, db, charset)
Base = declarative_base()
egine = create_engine(conn, max_overflow=5)


class SpiderMonitor(Base):
    __tablename__ = 'spider_monitor'
    id = Column(Integer, primary_key=True, autoincrement=True)
    spider = Column(String(255))
    runtime = Column(String(50))
    create_time = Column(DateTime, nullable=False, server_default=text('NOW()'))
    update_time = Column(TIMESTAMP(True), nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class UnormalSpider(Base):
    __tablename__ = 'unormal_spider'
    id = Column(Integer, primary_key=True, autoincrement=True)
    spider = Column(String(255))
    create_time = Column(DateTime, nullable=False, server_default=text('NOW()'))
    update_time = Column(TIMESTAMP(True), nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class TerminatedSpider(Base):
    __tablename__ = 'terminated_spider'
    id = Column(Integer, primary_key=True, autoincrement=True)
    spider = Column(String(255))
    job_id = Column(String(255))
    create_time = Column(DateTime, nullable=False, server_default=text('NOW()'))
    update_time = Column(TIMESTAMP(True), nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


Base.metadata.create_all(egine)
Session = sessionmaker(bind=egine)
session = Session()

