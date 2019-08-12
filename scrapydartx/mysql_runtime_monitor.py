from .mysql_models import SpiderMonitor
from .mysql_models import UnormalSpider
from .mysql_models import TerminatedSpider
from .mysql_models import SpiderScheduleModel
from twisted.logger import Logger
from .config import Config
from .Time_Method import time_pass2 as TP
from .Time_Method import time_pass_to as TPT
from scrapydartx import global_values as glv
import threading
import signal
import random
import os
import datetime
import time
import json
import requests
import numpy as np


class RuntimeCalculator:
    def __init__(self, lock, addr='localhost', port='6800'):
        config = Config()
        self.lock = lock
        self.highest_level = glv.get_value(key='top_level')
        self.user_name = config.get('auth_username', '')
        self.user_password = config.get('auth_password', '')
        self.clear_at_start = config.get('clear_up_database_when_start', 'yes')
        self.observation_times = int(config.get('observation_times', '20'))
        self.strict_mode = config.get('strict_mode', 'no')
        self.strict_degree = int(config.get('strict_degree', '4'))   # 严格模式的严格程度，取值大于零，数值越小越严格
        self.db = glv.get_value(key='mysql_db')
        self.mysql_host = config.get('mysql_host', '127.0.0.1')
        self.mysql_port = config.get('mysql_port', '3306')
        self.mysql_user = config.get('mysql_user', 'root')
        self.mysql_db = config.get('mysql_db', 'scrapydartdb')
        self.runtime_log = Logger(namespace='- Runtime Collector -')
        self.terminator_log = Logger(namespace='- TERMINATOR -')
        self.sep_time = 1 * 60  # 每次收集时间间隔 1 分钟
        self.terminator_scan_sep = 20
        self.server_port = 'http://{}:{}/'.format(addr, port)
        self.jobs_url = self.server_port + 'listjobs.json'

    def list_the_spiders(self, spider_list):
        dic = dict()
        if spider_list:
            for spider_dic in spider_list:
                spider_name = [x for x in spider_dic.keys()][0]
                runtime = int([x for x in spider_dic.values()][0])
                if dic.get(spider_name):
                    dic[spider_name].append(runtime)
                else:
                    dic[spider_name] = list()
                    dic[spider_name].append(runtime)
        return dic

    def unusual_spider(self, project, name_of_spider, runtime_of_spider, save_to_database=True):
        where_str = ' where project="{}"'.format(project)
        self.lock.acquire()
        res_from_db = self.db.get_result(model=SpiderScheduleModel, fields=['project', 'spider'], where_dic={'status': '=*3'})
        data = self.db.get_spider_runtime(field=['spider', 'runtime'], where=where_str)
        self.lock.release()
        top_set = {'{}-{}'.format(x.project, x.spider) for x in res_from_db}
        item = '{}-{}'.format(project, name_of_spider)
        if item in top_set:
            return -1100
        spider_list_temp = [{x.spider: x.runtime} for x in data] if data else []
        spider_dic_temp = self.list_the_spiders(spider_list_temp)
        over_time = -1000
        if spider_dic_temp:
            time_list = spider_dic_temp.get(name_of_spider)
            if time_list and len(time_list) > self.observation_times:
                std = np.std(time_list, ddof=1)
                if self.strict_mode == "yes":
                    time_list_set = set(time_list)
                    expectation = sum([x*(time_list.count(x)/len(time_list)) for x in time_list_set])   # 数学期望
                    over_time = runtime_of_spider - (std * self.strict_degree + expectation)    # 严格模式，样本偏差加上数学期望
                else:
                    over_time = runtime_of_spider - (std + max(time_list))      # 非严格模式，样本偏差加上最大值，确保不误杀
                if over_time > 0:
                    if save_to_database:
                        self.lock.acquire()
                        unusual_spider_data = self.db.get_unormal_spider(field=['spider'])
                        self.lock.release()
                        unusual_spiders_set = set([x.spider for x in unusual_spider_data]) if unusual_spider_data else {}
                        if name_of_spider not in unusual_spiders_set:
                            self.lock.acquire()
                            self.db.insert_data(
                                model=UnormalSpider,
                                field_names='spider',
                                values=name_of_spider)
                            self.lock.release()
        return over_time

    def save_spider_runtime(self):
        if self.clear_at_start == 'yes':
            self.lock.acquire()
            self.db.del_data(model=SpiderMonitor)
            self.db.del_data(model=UnormalSpider)
            self.db.del_data(model=TerminatedSpider)
            self.lock.release()
            self.runtime_log.warn('spider running recorder database has been clean up')
            self.runtime_log.info('database type: mysql')
            mysql_info = '{}@{}:{}/{}'.format(self.mysql_user, self.mysql_host, self.mysql_port,self.mysql_db)
            self.runtime_log.info('database info: {}'.format(mysql_info))
            self.runtime_log.info('each spider observation times: {}'.format(self.observation_times))
            self.runtime_log.info('is unusual spider runtime calculation in strict mode: {}'.format(self.strict_mode))
            if self.strict_mode == 'yes':
                self.runtime_log.info('strict mode value: {}'.format(self.strict_degree))
        time.sleep(3)
        while True:
            self.lock.acquire()
            job_res = self.db.get_result(model=SpiderMonitor, fields=['job_id'], return_model_map=True)
            self.lock.release()
            job_ids = set([x.job_id for x in job_res]) if job_res else set()
            save_sta = False
            for s_lis in self.runtime_monitor():
                if s_lis:
                    project, spider_name, runtime, job_id = s_lis
                    if self.unusual_spider(project, spider_name, runtime, save_to_database=False) <= 0:
                        self.database_limit_ctrl(
                                model=SpiderMonitor,
                                where_dic={'spider': '=*{}'.format(spider_name), 'project': '=*{}'.format(project)},
                                limit=1000
                        )
                        if job_id not in job_ids:
                            self.lock.acquire()
                            self.db.insert_data(
                                    model=SpiderMonitor,
                                    field_names=['project', 'spider', 'runtime', 'job_id'],
                                    values=[project, spider_name, runtime, job_id])
                            self.lock.release()
                            save_sta = True
            if save_sta:
                self.runtime_log.info('spider runtime saved')
            time.sleep(self.sep_time)

    def database_limit_ctrl(self, model, where_dic, limit=1000):
        self.lock.acquire(blocking=True)
        res = self.db.get_result(model=model, fields=['id', 'create_time'], where_dic=where_dic, return_model_map=True)
        self.lock.release()
        if res:
            id_res = [x.id for x in res]
            id_res.sort(reverse=True)
            if len(id_res) > limit:
                if limit > 100:
                    limit = random.randint(100, limit)
                remove_ids = id_res[limit:]
                if remove_ids:
                    self.lock.acquire()
                    self.db.del_data(model=model, where_dic={'id': remove_ids})
                    self.lock.release()
            time_res = {str(TP(y.create_time.strftime("%Y-%m-%d %H:%M:%S"))): y.id for y in res}
            over_time = 30 * 24 * 60 * 60
            rm_lis = [time_res.get(t) for t in time_res if int(t) > over_time]
            if rm_lis:
                self.lock.acquire()
                self.db.del_data(model=model, where_dic={'id': rm_lis})
                self.lock.release()

    def runtime_monitor(self, req_spider=''):
        res = requests.get(url=self.jobs_url)
        spider_list = list()
        spiders_dic = dict()
        if res:
            rank_list = json.loads(res.content).get('finished')
            if rank_list:
                for each_spider in rank_list:
                    project = each_spider.get('project')
                    spider_name = each_spider.get('spider')
                    job_id = each_spider.get('id')
                    s_time = each_spider.get('start_time').split('.')[0]
                    e_time = each_spider.get('end_time').split('.')[0]
                    runtime = TPT(s_time, e_time)
                    spider_list.append([project, spider_name, runtime, job_id])
                    if not spiders_dic.get(spider_name):
                        spiders_dic[spider_name] = list()
                        spiders_dic[spider_name].append(runtime)
                    else:
                        spiders_dic[spider_name].append(runtime)
        if req_spider and spiders_dic:
            return sum(spiders_dic.get(req_spider))//len(spiders_dic.get(req_spider))
        return spider_list

    def time_format(self, strtime):
        strtime = str(strtime)

        times = [x.strip() for x in strtime.split('d')]
        if len(times) > 1:
            d = int(times[0])
            hms = times[1]
        else:
            d = 0
            hms = times[0]

        h, m, s = [int(x.strip()) for x in hms.split(":") if x and x.strip()]
        seconds = d * 24 * 60 * 60 + h * 60 * 60 + m * 60 + s
        return seconds

    def terminator(self):
        time.sleep(3)
        self.terminator_log.info('Terminator Started')
        while True:
            res = json.loads(requests.get(url=self.jobs_url).content)
            if res.get('status') == 'ok':
                running_spiders = res.get('running')
                if running_spiders:
                    kill_lis = list()
                    for running_spider in running_spiders:
                        project = running_spider.get('project')
                        spider = running_spider.get('spider')
                        job_id = running_spider.get('id')
                        PID = running_spider.get('pid')
                        start_time = running_spider.get('start_time')
                        time_passed = self.time_passed(start_time)
                        if self.unusual_spider(
                                project=project,
                                name_of_spider=spider,
                                runtime_of_spider=time_passed,
                                save_to_database=False) > 0:
                            self.terminator_log.info('Unusual spider detected! ')
                            if project and job_id:
                                term = threading.Thread(target=self.kill_spider,
                                                        args=(project, job_id, spider, PID))
                                term.setDaemon(True)
                                term.start()
                                kill_lis.append("{}-{}-{}".format(project, spider, job_id))
                            else:
                                p_name = '<project name> ' if not project else '[{}]'.format(project)
                                j_id = '<job id>' if not job_id else '[{}]'.format(job_id)
                                missing_data = p_name + j_id
                                self.terminator_log.warn('Target info {} missing , Unable to locate the target!'.format(missing_data))
                                pass
                    ter_msg = 'Scan completed'
                    if kill_lis:
                        ter_msg += ', Terminated target: {}'.format(str(kill_lis))
                    self.terminator_log.warn(ter_msg)
            time.sleep(self.terminator_scan_sep)

    def kill_spider(self, project, job_id, spider, PID):
        kill_url = os.path.join(self.server_port, 'cancel.json')
        self.terminator_log.warn('\n\n\tTarget Found! >>> {}  {} <<<\n'.format(spider, job_id))
        self.terminator_log.warn('terminate the spider "{}" within 3 seconds'.format(spider))
        time.sleep(2)
        self.terminator_log.warn('sending terminate signal...')
        body = {"project": project, "job": job_id}
        try:
            target_killed = False
            for _ in range(2):
                res = json.loads(requests.post(url=kill_url, data=body).content)
                self.terminator_log.warn('terminate signal has been sanded [{}]'.format(_))
                kill_status = res.get('status')
                kill_prevstate = res.get('prevstate')
                if kill_status == 'ok' and kill_prevstate not in {'running', 'pending'}:
                    target_killed = True
                    break
                time.sleep(0.5)
            if target_killed:
                self.terminator_log.warn('Target [ {} ] has been terminated {}\n'.format(spider, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
                self.lock.acquire()
                self.db.insert_data(model=TerminatedSpider, field_names=['spider', 'job_id'], values=[spider, job_id])
                self.lock.release()
            else:
                raise ValueError('\t[- TERMINATOR -] >> Signal sended, but the target still running')
        except Exception as E:
            self.terminator_log.warn('sth goes wrong when sending the terminate signal : {}'.format(E))
            self.terminator_log.warn('trying to terminate it with PID...')
            try:
                os.kill(int(PID), signal.SIGKILL)
                self.lock.acquire()
                self.db.insert_data(model=TerminatedSpider, field_names=['spider', 'job_id'], values=[spider, job_id])
                self.lock.release()
                self.terminator_log.warn('Target [{}] has been terminated {}\n'.format(spider, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
            except:
                os.popen('taskkill.exe /pid:' + str(PID))
                self.lock.acquire()
                self.db.insert_data(model=TerminatedSpider, field_names=['spider', 'job_id'], values=[spider, job_id])
                self.lock.release()
                self.terminator_log.warn('Target [{}] has been terminated {}\n'.format(spider, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

    def time_passed(self, date_time):
        date_time = date_time.strip()
        if len(date_time.split(' ')) < 2:
            date_time = date_time + " 00:00:00"
        last_news_date = date_time.split(" ")[0].split('-')
        last_news_time = date_time.split(" ")[1].split(':')
        for t in last_news_time:
            last_news_date.append(t)
        ls = [int(x) if '.' not in x else int(float(x)) for x in last_news_date]
        secs = "(datetime.datetime.now() - " \
               "datetime.datetime({},{},{},{},{},{})).total_seconds()".format(ls[0], ls[1], ls[2], ls[3], ls[4], ls[5])
        secs = round(eval(secs))
        return secs
