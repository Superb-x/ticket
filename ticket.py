# -*- coding: utf-8 -*-
'''
    命令行火车票查看器
    
Usage:
    ticket [-gdtkz] <from> <to> <date>
    
Options:
    -h, ---help   显示帮助
    -g            高铁
    -d            动车
    -t            特快
    -k            快速
    -z            直达
Example:
    ticket 长沙 北京 2017-10-07
    ticket -gd 长沙 北京 2017-10-07    
'''
import requests
from docopt import docopt
from stations import stations
from stcode import stcodes
from prettytable import PrettyTable
from colorama import init, Fore

init()

# 封装一个简单的类来解析数据
class TrainsCollection:

    header = '车次 车站 时间 历时 一等 二等 软卧 硬卧 动卧 硬座 无座'.split()

    def __init__(self, available_trains, options):
        '''
        查询到的火车班次集合
        :param available_trains: 一个列表，包含可获得的火车班次，每个班次是一个字典
        :param options: 查询选项eg:高铁 动车 Z字头
        '''

        self.available_trains = available_trains
        self.options = options

    def _get_duration(self, raw_train):
        duration = raw_train[10].replace(':', '小时') + '分'
        return duration

    @property
    def trains(self):
        for raw_train in self.available_trains:
            train_no = raw_train[3]
            initial = train_no[0].lower()    # 取车次中的首字母
            if not self.options or initial in self.options: 
                train = [
                    train_no,
                    '\n'.join([Fore.GREEN + stcodes[raw_train[6]] + Fore.RESET, Fore.RED + stcodes[raw_train[5]] + Fore.RESET]),
                    '\n'.join([Fore.GREEN + raw_train[8] + Fore.RESET, Fore.RED + raw_train[9] + Fore.RESET]),
                    self._get_duration(raw_train),
                    raw_train[31],
                    raw_train[30],
                    raw_train[23],
                    raw_train[28],
                    raw_train[33],
                    raw_train[29],
                    raw_train[26]
                ]
                yield train

    def pretty_print(self):
        pt = PrettyTable()
        pt._set_field_names(self.header)
        num = 0
        for train in self.trains:
            pt.add_row(train)
            num += 1
        print(pt)
        print(Fore.GREEN + '一共查询到 %s 趟列车' % num + Fore.RESET)

def cli():
    '''命令行接口'''
    arguments = docopt(__doc__)
    from_station = stations.get(arguments['<from>'])
    to_station = stations.get(arguments['<to>'])
    date = arguments['<date>']
    # 余票查询接口
    url = 'https://kyfw.12306.cn/otn/leftTicket/queryX?leftTicketDTO.train_date={0}&leftTicketDTO.from_station={1}&leftTicketDTO.to_station={2}&purpose_codes=ADULT'.format(date, from_station, to_station)

    # 获取参数
    options = ''.join([
        key for key, value in arguments.items() if value is True
    ])

    #设置请求头，防止被12306屏蔽
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36'
    }
    # 关闭证书警告
    requests.packages.urllib3.disable_warnings()
    # 添加verify=False 不验证证书
    r = requests.get(url, headers=headers, verify=False)
    # 提取有效信息
    data = r.json()['data']['result']
    available_trains = []
    for item in data:
        available_trains.append(item.split('|'))
    TrainsCollection(available_trains, options).pretty_print()
if __name__ == "__main__":
    cli()