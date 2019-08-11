from .MysqlOrm_information import GetBDataBase
from .model_news_infomation import SpiderMonitor
from .model_news_infomation import UnormalSpider
from .model_news_infomation import TerminatedSpider
import threading
import signal
import os
import datetime
import logging
import time
import json
import requests
import numpy as np


class RuntimeCalculator:

    def __init__(self):
        self.db = GetBDataBase()  # 实例化orm对象
        self.sep_time = 5 * 60  # 每次收集时间间隔 5分钟
        self.standard_deviation_extend_times = 1.9   # 方差倍数，数值越大越容易被定为正常运行时间
        self.server_port = 'http://127.0.0.1:6800/'
        self.timerank_url = os.path.join(self.server_port, 'timerank.json?index=100')
        self.jobs_url = os.path.join(self.server_port, 'listjobs.json?project=scrapy_information')

        data = self.db.get_spider_runtime(field=['spider', 'runtime'])
        self.spider_list = [{x.spider: x.runtime} for x in data]
        self.spider_dic = self.list_the_spiders(self.spider_list)

        spider_data = self.db.get_unormal_spider(field=['spider'])
        self.unormal_spiders = set([x.spider for x in spider_data])

    def list_the_spiders(self, spider_list):
        if spider_list:
            dic = dict()
            for spider_dic in spider_list:
                spider_name = [x for x in spider_dic.keys()][0]
                runtime = int([x for x in spider_dic.values()][0])
                if dic.get(spider_name):
                    dic[spider_name].append(runtime)
                else:
                    dic[spider_name] = list()
                    dic[spider_name].append(runtime)
            return dic

    def unormal_spider(self, name_of_spider, runtime_of_spider, save_to_database=True):
        time_list = self.spider_dic.get(name_of_spider)
        over_time = -np.e
        if time_list:
            std = np.std(time_list)
            avg = sum(time_list) / len(time_list)
            over_time = runtime_of_spider - (std * self.standard_deviation_extend_times + avg)
            if over_time > 0:
                # print(name_of_spider, runtime_of_spider)
                if save_to_database:
                    if name_of_spider not in self.unormal_spiders:
                        self.db.insert_data(
                            model=UnormalSpider,
                            field_names='spider',
                            values=name_of_spider)
        return over_time

    def save_spider_runtime(self):
        for count in range(1, 10081):  # 循环一星期
            for s_lis in self.runtime_monitor():
                if s_lis:
                    spider_name, runtime = s_lis
                    self.db.insert_data(
                        model=SpiderMonitor, field_names=[
                            'spider', 'runtime'], values=[
                            spider_name, runtime])
            time.sleep(self.sep_time)

    def runtime_monitor(self):
        res = requests.request(url=self.timerank_url, method='GET')
        spider_list = list()
        if res:
            rank_list = json.loads(res.text).get('ranks')
            if rank_list:
                for each_spider in rank_list:
                    spider_name = each_spider.get('spider')
                    runtime = each_spider.get('time')
                    if runtime:
                        runtime_lis = runtime.split(":")
                        runtime = int(
                            runtime_lis[0]) * 60 * 60 + int(runtime_lis[1]) * 60 + int(runtime_lis[2])
                        spider_list.append([spider_name, runtime])
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
        while True:
            try:
                res = json.loads(requests.request(url=self.jobs_url, method='GET').content)
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
                            time_passed = self.time_pass(start_time)
                            if self.unormal_spider(name_of_spider=spider,
                                                   runtime_of_spider=time_passed,
                                                   save_to_database=False) > 0:
                                kill_lis.append(running_spider)
                                self.db.insert_data(
                                        model=TerminatedSpider,
                                        field_names=['spider', 'job_id'],
                                        values=[spider, job_id]
                                        )

                                term = threading.Thread(target=self.kill_spider,
                                                        args=(project, job_id, spider, PID))
                                term.setDaemon(True)
                                term.start()
            except:
                logging.error("terminator ERROR")
                # break
            finally:
                time.sleep(100)

    def kill_spider(self, project, job_id, spider, PID):
        kill_url = os.path.join(self.server_port, 'cancel.json')
        logging.warning('terminate the spider "{}" within 10 min'.format(spider))
        time.sleep(60)
        logging.warning('sending terminate signal...')
        body = {"project": str(project), "job": str(job_id)}
        try:
            res = json.loads(requests.post(url=kill_url, data=body).content)
            logging.warning('terminate signal has been sanded')
            kill_status = res.get('status')
            kill_prevstate = res.get('prevstate')
            if kill_status == 'ok' and kill_prevstate == 'running':
                logging.warning('spider "{}" has been terminated  {}'.format(spider, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
            elif kill_status == 'ok' and kill_prevstate is None:
                logging.warning('The spider seems finished before we kill it')
        except:
            logging.warning('sth goes wrong when sending the terminate signal')
            logging.warning('trying to terminate it with PID...')
            try:
                os.kill(pid=int(PID), sig=signal.SIGKILL)
                logging.warning('kill success')
            except:
                os.popen('taskkill.exe /pid:' + str(PID))
                logging.warning('kill success')
            else:
                logging.warning('unable to kill it! ')

    def time_pass(self, date_time):
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
