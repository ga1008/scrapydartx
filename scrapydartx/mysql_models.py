from sqlalchemy import Column, Integer, String, DateTime, TIMESTAMP, text
from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from twisted.logger import Logger
import pymysql
from .config import Config


logger = Logger(namespace='- MODEL -')


def make_engine(user='root',
                  passwd='mysql',
                  host='127.0.0.1',
                  port=3306,
                  db='scrapydartdb',
                  charset='utf8'):
    # user = 'quinns'
    # passwd = 'Quinns3000'
    # host = '192.168.0.61'
    # port = 3306
    # db = 'watermelon'
    create_db = pymysql.connect(
        host=host,
        user=user,
        port=int(port),
        password=passwd,
        db='mysql')
    cursor = create_db.cursor()

    cursor.execute('show databases like "{}";'.format(db))
    db_show_res = cursor.fetchone()
    if not db_show_res:
        try:
            cursor.execute(
                "Create Database If Not Exists {} Character Set UTF8".format(db))
        except Exception as E:
            logger.error('database creation fail, please check connection info')
    create_db.close()

    conn = 'mysql+pymysql://%s:%s@%s:%s/%s?charset=%s' % (
        user, passwd, host, port, db, charset)
    return create_engine(conn, max_overflow=5)


Base = declarative_base()


class SpiderMonitor(Base):
    __tablename__ = 'spider_monitor'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project = Column(String(200))
    spider = Column(String(255))
    runtime = Column(String(50))
    job_id = Column(String(100))
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


class SpiderScheduleModel(Base):
    __tablename__ = 'spider_schedule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project = Column(String(255), nullable=False)
    spider = Column(String(255), nullable=False)
    schedule = Column(LONGTEXT, nullable=False)
    args = Column(String(255), nullable=True)
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text('NOW()'))
    update_time = Column(TIMESTAMP(True), nullable=False)
    status = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {c.name: getattr(self, c.name, None)
                for c in self.__table__.columns}


config = Config()
mysql_host = config.get('mysql_host', '127.0.0.1')
mysql_port = config.get('mysql_port', 3306)
mysql_user = config.get('mysql_user', 'root')
mysql_password = config.get('mysql_password', 'mysql')
mysql_db = config.get('mysql_db', 'scrapydartTest')

engine = make_engine(user=mysql_user, passwd=mysql_password, host=mysql_host, port=mysql_port, db=mysql_db)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
