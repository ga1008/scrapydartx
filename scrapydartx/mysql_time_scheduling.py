import time
import json
import datetime
import threading
import requests
import psutil
from twisted.logger import Logger
from .config import Config
from scrapydartx import global_values as glv
from .mysql_models import SpiderScheduleModel, SpiderMonitor


class TimeSchedule:

    def __init__(self, lock, host='localhost', port='6800'):
        config = Config()
        self.highest_level = glv.get_value(key='top_level')
        self.db = glv.get_value(key='mysql_db')
        self.user_name = config.get('auth_username', '')
        self.user_password = config.get('auth_password', '')
        self.start_time = time.strftime("%Y %m %d %H %M %S", time.localtime())
        self.schedule_post_url = 'http://{}:{}/schedule.json'.format(host, port)
        self.listproject_url = 'http://{}:{}/listprojects.json'.format(host, port)
        self.projects = None
        self.spider_task_dic = dict()
        self.db_lock = lock
        self.ts_lock = threading.Lock()
        self.CPU_THRESHOLD = 93
        self.MEMORY_THRESHOLD = 96
        self.schedule_logger = Logger(namespace='- Scheduler -')

    def run(self):
        time.sleep(3)
        self.projects = self.list_projects()
        self.schedule_logger.info('scheduler is running')
        count = 1
        while True:
            schedule_sta = self.task_scheduler()
            if not schedule_sta and count == 1:
                self.schedule_logger.info('No Scheduled Spider in Database')
                count += 1
            elif not schedule_sta and count != 1:
                count += 1
            else:
                count = 1
            time.sleep(1)

    def task_scheduler(self):
        self.ts_lock.acquire(blocking=True)
        self.db_lock.acquire()
        db_result = self.db.get_result(model=SpiderScheduleModel, fields=['project', 'spider', 'schedule', 'args', 'status'])
        self.db_lock.release()
        self.ts_lock.release()
        schedule_list_raw = [
            {'project': x.project, 'spider': x.spider, 'schedule': x.schedule, 'args': x.args, 'status': x.status}
            for x in db_result if int(x.status) != 0
        ] if db_result else []
        schedule_sta = False
        if schedule_list_raw:
            for each_schedule in schedule_list_raw:
                project = each_schedule.get('project')
                if project in self.projects:
                    schedule = each_schedule.get('schedule').replace('\\', '')
                    try:
                        schedule = json.loads(schedule)
                    except:
                        schedule = eval(schedule)
                    try:
                        next_time_sep = self.cal_time_sep(**schedule)
                        next_time_sep = int(next_time_sep) + 1
                        if next_time_sep > 1:
                            each_schedule['schedule'] = next_time_sep
                            item = '{}-{}'.format(each_schedule['project'], each_schedule['spider'])
                            self.ts_lock.acquire(blocking=True)
                            if self.spider_task_dic.get(item) != 'waiting':
                                self.spider_task_dic[item] = 'waiting'
                                t = threading.Thread(target=self.poster, args=(each_schedule, ))
                                try:
                                    t.start()
                                except Exception as APError:
                                    self.schedule_logger.warn('no new jobs : {}'.format(APError))
                            self.ts_lock.release()
                    except ValueError:
                        self.schedule_logger.error('spider runtime schedule error, please check the database')
            schedule_sta = True
        return schedule_sta

    def poster(self, dic):
        status = int(dic.pop('status'))
        project = dic.get('project')
        spider = dic.get('spider')
        job_str = " %s-%s " % (project, spider)
        args = dic.get('args').replace('\\', '')
        if args:
            args = eval(args)
        wait_time = dic.get('schedule')
        item = '{}-{}'.format(project, spider)
        if project and spider:
            data = {'project': project, 'spider': spider, 'un': self.user_name, 'pwd': self.user_password}
            if args:
                data.update(args)
            self.schedule_logger.info('job {} is waiting, countdown {}s'.format(item, wait_time))
            time.sleep(wait_time - 1)
            another_wait_time = 0
            spider_runtime_avg = self.spiders_runtime(project=project, spider=spider)
            if status == 1:
                while not self.is_system_ok():
                    self.schedule_logger.warn('system is fully functioning, wait another 2 seconds to post schedule')
                    time.sleep(3)
                    another_wait_time += 2
                    if another_wait_time >= (wait_time - spider_runtime_avg):
                        self.schedule_logger.warning('wait too long, cancel the job %s' % job_str)
                        return None
                res = json.loads(requests.post(url=self.schedule_post_url, data=data).content)
            elif status == 2:
                res = json.loads(requests.post(url=self.schedule_post_url, data=data).content)
            elif status == 3:
                res = json.loads(requests.post(url=self.schedule_post_url, data=data).content)
            else:
                res = json.loads(requests.post(url=self.schedule_post_url, data=data).content)
            spider_status = res.get('status')
            if spider_status != 'ok':
                spider_status = 'error'
        else:
            self.schedule_logger.error('job project: {}, spider: {} post fail!'.format(project, spider))
            spider_status = 'error'
        self.ts_lock.acquire(blocking=True)
        self.spider_task_dic[item] = spider_status
        self.ts_lock.release()

    def spiders_runtime(self, project, spider):
        where_dic = {
            'project': '=*{}'.format(project),
            'spider': '=*{}'.format(spider)
        }
        self.db_lock.acquire()
        res = self.db.get_result(model=SpiderMonitor, fields=['runtime'], where_dic=where_dic)
        self.db_lock.release()
        spider_list = [int(x.runtime) for x in res if x.runtime.isdigit()] if res else [0]
        return sum(spider_list) / len(spider_list)

    def list_projects(self):
        res = requests.get(url=self.listproject_url)
        projects = {}
        if res:
            projects_list = json.loads(res.content).get('projects')
            if projects_list:
                projects = set(projects_list)
        return projects

    def cal_time_sep(self,
            year='*',
            month='*',
            day='*',
            week='*',
            hour='*',
            minute='*',
            second='*',
            ):
        """
            "%Y-%m-%d %H:%M:%S %w"

        """

        y = int(time.strftime("%Y", time.localtime()))
        if year != '*' and '*' in year:
            y = int(year.split('/')[-1]) + y
        elif year.isdigit():
            y = int(year)

        if week == '*':
            m = int(time.strftime("%m", time.localtime()))
            if month != '*' and '*' in month:
                m_raw = int(month.split('/')[-1])
                if m_raw >= 12:
                    raise ValueError('month value is too large, please set the year instead')
                m = m_raw + m
                if m > 12:
                    y += m // 12
                    m = m % 12
            elif month.isdigit():
                m = int(month)

            days_in_this_month = self.how_many_days_in_this_month(y, m)
            d = int(time.strftime("%d", time.localtime()))
            if day != '*' and '*' in day:
                d_raw = int(day.split('/')[-1])
                if d_raw > days_in_this_month:
                    raise ValueError('day value is too large, please set the month or the year instead')
                d = d_raw + d
                if d > days_in_this_month:
                    d = d - days_in_this_month
                    m += 1
                    if m > 12:
                        y += 1
                        m = m - 12
            elif day.isdigit():
                d = int(day)

            days_in_this_month = self.how_many_days_in_this_month(y, m)
            H = int(time.strftime("%H", time.localtime()))
            if hour != '*' and '*' in hour:
                H_raw = int(hour.split('/')[-1])
                if H_raw > 24:
                    raise ValueError('hour value is too large, please set the day instead')
                H = H_raw + H
                if H >= 24:
                    H = H - 24
                    d += 1
                    if d > days_in_this_month:
                        d = d - days_in_this_month
                        m += 1
                        if m > 12:
                            y += 1
                            m = m - 12
            elif hour.isdigit():
                H = int(hour)

            days_in_this_month = self.how_many_days_in_this_month(y, m)
            M = int(time.strftime("%M", time.localtime()))
            if minute != '*' and '*' in minute:
                M_raw = int(minute.split('/')[-1])
                if M_raw > 60:
                    raise ValueError('minute value is too large, please set the hour instead')
                M = M_raw + M
                if M >= 60:
                    M = M - 60
                    H += 1
                    if H >= 24:
                        H = H - 24
                        d += 1
                        if d > days_in_this_month:
                            d = d - days_in_this_month
                            m += 1
                            if m > 12:
                                y += 1
                                m = m - 12
            elif minute.isdigit():
                M = int(minute)

            days_in_this_month = self.how_many_days_in_this_month(y, m)
            S = int(time.strftime("%S", time.localtime()))
            if second != '*' and '*' in second:
                S_raw = int(second.split('/')[-1])
                if S_raw > 60:
                    raise ValueError('second value is too large, please set the minute instead')
                S = S_raw + S
                if S >= 60:
                    S = S - 60
                    M += 1
                    if M >= 60:
                        M = M - 60
                        H += 1
                        if H >= 24:
                            H = H - 24
                            d += 1
                            if d > days_in_this_month:
                                d = d - days_in_this_month
                                m += 1
                                if m > 12:
                                    y += 1
                                    m = m - 12
            elif second.isdigit():
                S = int(second)
            time_sep = eval("(datetime.datetime({},{},{}, {},{},{}) - datetime.datetime.now()).total_seconds()".format(y,m,d, H,M,S))

        else:
            week_in_this_year = int(time.strftime("%U", time.localtime()))
            w = int(time.strftime("%w", time.localtime()))
            if '*' in week:
                w_raw = int(week.split('/')[-1])
                if w_raw >= 7:
                    raise ValueError('week value is too large, please set the day or the month instead')
                if w_raw < w:
                    week_in_this_year += 1
                w = w_raw
                if week_in_this_year > 53:
                    y += 1
                    week_in_this_year = week_in_this_year - 53

            elif week.isdigit():
                w = int(week)
                if int(week) < w:
                    week_in_this_year += 1

            H = int(time.strftime("%H", time.localtime()))
            if hour != '*' and '*' in hour:
                H_raw = int(hour.split('/')[-1])
                if H_raw >= 24:
                    raise ValueError('hour value is too large, please set the day instead')
                H = H_raw + H
                if H >= 24:
                    H = H - 24
                    w += 1
                    if w >= 7:
                        w = w - 7
                        week_in_this_year += 1
                        if week_in_this_year > 53:
                            y += 1
                            week_in_this_year = week_in_this_year - 53
            elif hour.isdigit():
                H = int(hour)

            M = int(time.strftime("%M", time.localtime()))
            if minute != '*' and '*' in minute:
                M_raw = int(minute.split('/')[-1])
                if M_raw >= 60:
                    raise ValueError('minute value is too large, please set the hour instead')
                M = M_raw + M
                if M >= 60:
                    M = M - 60
                    H += 1
                    if H >= 24:
                        H = H - 24
                        w += 1
                        if w > 7:
                            w = w - 7
                            week_in_this_year += 1
                            if week_in_this_year > 53:
                                y += 1
                                week_in_this_year = week_in_this_year - 53
            elif minute.isdigit():
                M = int(minute)

            S = int(time.strftime("%S", time.localtime()))
            if second != '*' and '*' in second:
                S_raw = int(second.split('/')[-1])
                if S_raw >= 60:
                    raise ValueError('second value is too large, please set the minute instead')
                S = S_raw + S
                if S >= 60:
                    S = S - 60
                    M += 1
                    if M >= 60:
                        M = M - 60
                        H += 1
                        if H >= 24:
                            H = H - 24
                            w += 1
                            if w > 7:
                                w = w - 7
                                week_in_this_year += 1
                                if week_in_this_year > 53:
                                    y += 1
                                    week_in_this_year = week_in_this_year - 53
            elif second.isdigit():
                S = int(second)
            if S >= 60:
                S = S - 60
                M += 1
                if M >= 60:
                    M = M - 60
                    H += 1
                    if H >= 24:
                        H = H - 24
                        w += 1
                        if w > 7:
                            w = w - 7
                            week_in_this_year += 1
                            if week_in_this_year > 53:
                                y += 1
                                week_in_this_year = week_in_this_year - 53
            m, d = self.get_month_and_days_by_week(year=y, week_in_this_year=week_in_this_year, week=w)
            time_sep = eval("(datetime.datetime({},{},{}, {},{},{}) - datetime.datetime.now()).total_seconds()".format(y, m, d, H, M, S))

        return time_sep

    def get_month_and_days_by_week(self, year, week_in_this_year, week):
        days = week_in_this_year * 7 + week
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            Fe = 29
        else:
            Fe = 28
        month_lis = [31, Fe, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        month_count = 1
        days_count = 0
        for month_days in month_lis:
            days = days - month_days
            if days > 0:
                month_count += 1
            elif days == 0:
                days_count = 0
                month_count += 1
                break
            else:
                days_count = days + month_days
                break
        return [month_count, days_count]

    def how_many_days_in_this_month(self, y, m):
        if m in (1, 3, 5, 7, 8, 10, 12):
            days = 31
        elif m in (4, 6, 9, 11):
            days = 30
        else:
            if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0):
                days = 29
            else:
                days = 28
        return days

    def is_system_ok(self):
        is_pass = True
        cpu_list = psutil.cpu_percent(interval=1, percpu=True)
        memory_percent = psutil.virtual_memory().percent
        if cpu_list and memory_percent:
            is_cpu_ok = True
            if min(cpu_list) > self.CPU_THRESHOLD:
                is_cpu_ok = False
            is_memo_ok = True
            if memory_percent > self.MEMORY_THRESHOLD:
                is_memo_ok = False
            if not is_cpu_ok or not is_memo_ok:
                is_pass = False
        return is_pass


# if __name__ == "__main__":
    # insert_schedule_into_database(values=['P1', 'spider_2', "{'second': '*/30'}", '1'])
    # time.sleep(1)
    # TS = TimeSchedule()
    # m, d = TS.get_month_and_days_by_week(year=2020, week_in_this_year=20, week=3)
    # 

    # time_sep = TS.cal_time_sep(second='*/50')

    # print(TS.is_system_ok())

    # TS.run()
