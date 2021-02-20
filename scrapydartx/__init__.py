from threading import RLock

from scrapy.utils.misc import load_object

from scrapydartx import global_values as glv
from scrapydartx.config import Config

glv._init()
lock = RLock()
glv.set_value(key='lock', value=lock)
glv.set_value(key='top_level', value=set())

__version__ = '1.3.5'
version_info = tuple(__version__.split('.')[:3])
name = "scrapydartx"


def get_application(config=None):
    if config is None:
        config = Config()
    apppath = config.get('application', 'scrapydartx.app.application')
    appfunc = load_object(apppath)
    database_type = config.get('database_type', 'sqlite')
    if database_type == 'mysql':
        from scrapydartx.mysql_orm import GetData as MSDB
        mysql_db = MSDB()
        glv.set_value(key='mysql_db', value=mysql_db)
    else:
        from scrapydartx.sqlite_orm import GetData as STDB
        sqlite_db = STDB()
        glv.set_value(key='sqlite_db', value=sqlite_db)

    return appfunc(config)
