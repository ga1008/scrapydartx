import time
import datetime


def time_pass(date_time):
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


def time_pass2(date_time, date_time_type="%Y-%m-%d %H:%M:%S"):
    date_time = date_time.strip()
    if len(date_time.split(' ')) < 2:
        date_time = date_time + " 00:00:00"

    secs = round(time.time() - time.mktime(time.strptime(date_time, date_time_type)))
    return secs


def time_pass_to(date_time1, date_time2, date_time1_type="%Y-%m-%d %H:%M:%S", date_time2_type="%Y-%m-%d %H:%M:%S"):
    date_time1 = date_time1.strip()
    if len(date_time1.split(' ')) < 2:
        date_time1 = date_time1 + " 00:00:00"
    date_time2 = date_time2.strip()
    if len(date_time2.split(' ')) < 2:
        date_time2 = date_time2 + " 00:00:00"

    secs = round(time.mktime(time.strptime(date_time2, date_time2_type)) - time.mktime(time.strptime(date_time1, date_time1_type)))
    return secs


def format_datetime(date_time, date_time_type="%Y-%m-%d %H:%M:%S", sep=' '):
    if date_time:
        date_time = date_time.strip()
        secs = time.mktime(time.strptime(date_time, "%s" % date_time_type))
        new_date_time = time.strftime("%Y-%m-%d{}%H:%M:%S".format(sep), time.localtime(secs))
        return new_date_time
    return time.strftime("%Y-%m-%d{}%H:%M:%S".format(sep), time.localtime())


if __name__ == "__main__":
    print(time_pass_to("2018-06-18 17:20:00", "2019-06-18 17:20:00"))
