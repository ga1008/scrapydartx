import pkgutil

__version__ = pkgutil.get_data(__package__, 'VERSION').decode('ascii').strip()
version_info = tuple(__version__.split('.')[:3])

from .runtime_monitor import RuntimeCalculator
from scrapy.utils.misc import load_object
from scrapydart.config import Config
import threading

RC = RuntimeCalculator()
runtime_thread = threading.Thread(target=RC.save_spider_runtime)
runtime_thread.setDaemon(True)
runtime_thread.start()

terminator_thread = threading.Thread(target=RC.terminator)
terminator_thread.setDaemon(True)
terminator_thread.start()

def get_application(config=None):
    if config is None:
        config = Config()
    apppath = config.get('application', 'scrapydartx.app.application')
    appfunc = load_object(apppath)
    return appfunc(config)


