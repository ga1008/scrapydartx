==========
ScrapydArt
==========

.. image:: https://secure.travis-ci.org/scrapy/scrapyd.svg?branch=master
    :target: http://travis-ci.org/scrapy/scrapyd

.. image:: https://codecov.io/gh/scrapy/scrapyd/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/scrapy/scrapyd


=======================================================================
建议使用anaconda环境，请前往主站或者清华站点下载并安装
$ bash Anaconda3-2019.03-Linux-x86_64.sh

在ScrapydArtEnv文件夹内有 ScrapydArt.txt 与 ScrapydArt.yaml 文件，在终端内输入:
$ conda env create -f ScrapydArt.yaml
$ conda activate ScrapydArt
$ pip install -r ScrapydArt.txt
即可解决环境问题
=======================================================================
功能扩展说明：
1. 集成了动态调度功能
scrapydart 现在可以在设置文件里(default_scrapyd.conf)设置调度数据库为mysql 或者是sqlite:
...
database_type = sqlite
...
若设置为mysql 则需要填写mysql 的配置信息, 可以是运行环境中的数据库或者在线数据库:
...
mysql_host = 127.0.0.1
mysql_port = 3306
mysql_user = root
mysql_password = mysql
mysql_db = scrapydartTest
...
其中mysql_db是指使用 mysql 的哪一个数据库
若database_type设置为 sqlite 则不需要设置这些

配置文件的其它设置：
...
clear_up_database_when_start = yes  // yes/no, 每次运行前清理观察数据
observation_times = 20      // >0的整数，设置异常监控的观察次数
strict_mode = no           // yes/no，设置是否严格模式
strict_degree = 4         // >0的任意数，设置严格模式的严格程度，越低越严格
...


平台被安装并且启动后，会自动在调度数据库查找需要调度的爬虫，并且根据调度字典计算下次运行时间。
需要注意的是，加入到调度数据库里的爬虫的项目名称（project）是必须的，并且不同的项目建议使用不同的项目名称

下面介绍将爬虫加入到调度数据库的方法
扩展平台加入了数个api以方便操控，包括调度数据库的增删改查都可以通过向端口发送请求完成
增加调度爬虫：
$ curl http://localhost:6800/scheduletodb.json -d project=project_name -d spider=spider_name -d schedule=spider_schedule_dict -d args=spider_args_dict -d status=spider_status

这样显得太长而且复用性太差，不建议这样，建议直接使用 python 的 requests 方法发送请求，效果是一样的，如下面的简单例子：
import requests

post_data = {
    'project': project_name, # str
    'spider': spider_name, # str
    'schedule': spider_schedule_dict, # dict
    'args': spider_args_dict, # dict
    'status': spider_status, # int
    }
result = requests.post(url='http://localhost:6800/scheduletodb.json', data=post_data)

上面post_data变量中的 “args” 如有需要请传入一个字典，里面的键和值将自动传递给相应的爬虫（需要提前在爬虫内接收），此项为可选项，可不传。

“status” 参数，数据类型为 int ，值为 0 或者1 或者2 或者3
0 ： 不启用此条调度
1 ： 正常启用
2 ： 高级模式
3 ： 最高级模式
设定为1的时候，爬虫会被系统资源限制运行，即当平台检测到系统cpu或者内存严重不足时，延缓数秒到一个周期执行，普通情况下请设置为1，同时如果运行时间异常，将会被平台异常管理机制自动终结
设定为2的时候，爬虫将忽略系统资源情况，不管系统资源占用多少都会按时执行，但如果运行时间异常，也将会被平台异常管理机制自动终结
设定为3的时候，爬虫为超级权限模式，不会被异常管理机制终止，同时忽略系统资源状况

“schedule” 的值需要一个字典，类似 {"second": "*/30"}，意思是每30秒运行一次，也可以设置为具体的某个时间点，例如：
...
'schedule': {
    'year': 2019,
    'month': 6,
    'day': 4,
    'hour': 10,
    'minute': 50,
    'second': 50
  }

        这样的设置是单次任务模式，爬虫只在设定的时间点（2019-06-04 10:50:50）运行一次
        也可以是只有分钟，或者只有秒，或者只有小时、天、月、年，平台将自动计算下次到达设定的时间的时间间隔，
        例如只给定 {'hour': 10}，则爬虫会在从明天开始的每一天的10点的当前分秒数启动，例如当发送了 "schedule" 参数为： 
"schedule": {"hour": 10}
而此时系统时间为 16:37:12，则爬虫将在明天，以及接下来的每一天的上午的 10:37:12 自动发送任务到运行平台并启动。        
若只设置为 {'day': 4}，则意思是从下个月开始的每个月的4号的当前时分秒启动，以此类推
        需要注意的是，设定的月为1~12， 日小于等于月最大天数，小时为0~23， 分钟数0~59，秒数0~59
此外，我想你应该已经完全了解在参数中加 "*/" 或 不加 "*/"的作用了，若仍觉得不清楚，直接使用它你会发现其中的含义。
        此外还可以设定星期数，例如 {'week': '*/2'}，意思是每周的周三执行，对的，星期的范围为0~6
        星期可以配合年、月、时、分、秒同时设定，但是不可同时设定星期数和天，否则将只按照天来计算，并忽略星期的设定。

    若入库成功，则返回的result如下：
 {"node_name": "name of node", "status": "ok"}
    入库成功后，等待几秒钟平台会发现它并且自动计算下次运行时间，后台将显示类似如下语句的日志：
[- Scheduler -#info] job default-xinhua is waiting, countdown 540s
                                                            ↑               ↑                                                       ↑
                                                       项目名        爬虫名                                      距下次运行秒数

    查看调度爬虫：
    $ curl http://localhost:6800/listdbschedule.json -d projects="['project_name1', 'project_name2']" -d spiders="['spider1', 'spider2']"

注意，参数projects与spiders需要传入字符串类型的列表，也可以什么都不传，将返回所有在数据库中的待调度爬虫和调度参数

    requests 方法：
import requests
url = 'http://127.0.0.1:6800/listdbschedule.json?un=&pwd='
data = {
    'projects': str(['project1', 'project2']),
    'spiders': str(['spider1', 'spider2']),
        }
res = json.loads(requests.post(url=url, data=data).content)
print(res)

    正确返回：
{"node_name": "name of node", "status": "ok", "database_schedules": 
                                        [{'id': schedule_id,
                                          'project': project_name,
                                          'spider': spider_name,
                                          'schedule': spider_schedule,
                                          'args': spider_args,
                                          'status': spider_status
                                          },
                                          {... ...},
                                          ...
                                          ] }
    更改调度爬虫：
    $ curl http://localhost:6800/updatedbschedule.json -d id=update_id -d schedule=new_schedule -d args=new_args -d status=new_status

    参数 id 是需要修改的那一条数据的id值，根据查看调度爬虫 listdbschedule.json 得知
    requests 方法：
import requests
post_data = {
          'id': update_id,
          'schedule': new_schedule,
          'args': new_args,
          'status': new_status,
          }
result = requests.post(url='http://localhost:6800/updatedbschedule.json', data=post_data)

    操作成功则返回：
    {"node_name": "name of node", 'update': "ok"}

    删除调度爬虫：
    $ curl http://localhost:6800/rmschedulefromdb.json -d id=delete_id
    delete_id 根据查询调度爬虫得知
    requests 方法：
import requests

post_data = {
            'id': delete_id,
            }
result = requests.post(url='http://localhost:6800/rmschedulefromdb.json', data=post_data)

    正确返回:
  {"node_name": "name of node", 'delete': "ok"}

    若在配置中设置了auth_username 和 auth_password，则需要在每次post请求的data中加入 {'un': user_name, 'pwd': password}， get 请求中加入 ?un=user_name&pwd=password

2. 异常爬虫管理功能
    此项功能默认在平台启动的时候自动启动，也可以在配置文件内设置为不启用 (默认 activate)
...
Terminator = deactivate
...
此功能会每隔数秒巡视一遍所有正在运行的爬虫，并根据之前的运行时间计算方差数与均值，推算判断本次运行的时间是否合理，若不合理，则会在几秒钟内终结此任务
不需要担心爬虫任务永远被杀死了，除非你设置的是单次定时任务，否则爬虫将在下一个周期继续正常启动
若设置为 Terminator设置为 "activate"，将会在平台启动时在后台显示日志：
[- TERMINATOR -#info] Terminator Started
Terminator 在每次巡视后在后台打印日志：
[- TERMINATOR -#warn] Scan completed
若本次巡视发现异常爬虫，且被终结，则巡视日志为：
[- TERMINATOR -#warn] Scan completed, Terminated target: '[default-xinhua-6796090a940b11e98d6854e1adc0a997, default-fifa-6796090a940b11e98d6854e1adc0a997]'
日志中 “Terminated target” 为被终结的爬虫的列表字符串，格式为:
  [project-spider-jobid, ...]

