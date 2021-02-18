from twisted.logger import Logger
import threading
import time
import requests
import re

from .config import Config


def run_extend(lock):
    time.sleep(1)
    config = Config()
    database_type = config.get('database_type', 'sqlite')
    http_port = config.getint('http_port', 6800)
    # bind_address = config.get('server_ip', get_server_ip())
    address = 'localhost'
    if database_type == 'mysql':
        from .mysql_runtime_monitor import RuntimeCalculator
        RC = RuntimeCalculator(lock=lock, addr=address, port=http_port)
    else:
        from .sqlite_runtime_monitor import RuntimeCalculator as SL_RuntimeCalculator
        RC = SL_RuntimeCalculator(lock=lock, addr=address, port=http_port)
    runtime_thread = threading.Thread(target=RC.save_spider_runtime)
    runtime_thread.setDaemon(True)
    runtime_thread.start()

    ter = config.get('Terminator', 'activate')
    if ter == 'activate':
        terminator_thread = threading.Thread(target=RC.terminator)
        terminator_thread.setDaemon(True)
        terminator_thread.start()

    if database_type == 'mysql':
        from .mysql_time_scheduling import TimeSchedule
        TS = TimeSchedule(lock=lock, host=address, port=http_port)
    else:
        from .sqlite_time_scheduling import TimeSchedule as SL_TimeSchedule
        TS = SL_TimeSchedule(lock=lock, host=address, port=http_port)
    schedule_thread = threading.Thread(target=TS.run)
    schedule_thread.setDaemon(True)
    schedule_thread.start()


def test_connection(addr):
    res = requests.get(url=addr).status_code
    if res == 200:
        return True
    return False


def get_server_ip():
    try:
        res = requests.get(url='http://txt.go.sohu.com/ip/soip').content.decode()
    except:
        return None
    server_ip_temp = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', res)
    server_ip = server_ip_temp[0] if server_ip_temp else None
    return server_ip


def set_default_config():
    config = Config()
    logger = Logger(namespace='- Set Config -')
    set_sta = config.get('set_sta', 'not')
    if set_sta == 'not':
        # logger.info('there some options needs to be set at the first run time')
        print('there some options needs to be set at the first run time')
        database_type = str(input('task schedule database, input "mysql" or "sqlite" (default "sqlite"): '))
        if database_type != 'mysql':
            database_type = 'sqlite'
        else:
            logger.info('you choise mysql, please make shua the database is connectable')
            mysql_host = str(input('mysql host: (127.0.0.1) ')).strip()
            if not re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', mysql_host):
                mysql_host = '127.0.0.1'
            mysql_port = str(input('mysql port: (3306) ')).strip()
            if not re.findall(r'\d{3,5}', mysql_port):
                mysql_port = '3306'
            mysql_user = str(input('mysql user: (root) ')).strip()
            if not mysql_user:
                mysql_user = 'root'
            mysql_password = str(input('mysql password: (123456) '))
            if not mysql_password:
                mysql_password = 'mysql'
            mysql_db = str(input('mysql database: (scrapydartx) '))
            if not re.findall(r'[\da-zA-Z_]+', mysql_db):
                mysql_db = 'scrapydartTest'
            config.cp.set(section=config.SECTION, option='mysql_host', value=mysql_host)
            config.cp.set(section=config.SECTION, option='mysql_port', value=mysql_port)
            config.cp.set(section=config.SECTION, option='mysql_user', value=mysql_user)
            config.cp.set(section=config.SECTION, option='mysql_password', value=mysql_password)
            config.cp.set(section=config.SECTION, option='mysql_db', value=mysql_db)
        terminator_sta = str(input('activate terminator: (deactivate/activate, default activate) '))
        if terminator_sta != 'deactivate':
            terminator_sta = 'activate'

        set_sta = 'set'
        config.cp.set(section=config.SECTION, option='database_type', value=database_type)
        config.cp.set(section=config.SECTION, option='Terminator', value=terminator_sta)
        config.cp.set(section=config.SECTION, option='set_sta', value=set_sta)
        logger.info('set complite, you can change the options in the .conf file')
        time.sleep(1)
