# -*- coding: utf-8 -*-
import requests
import smtplib
import time
from stations import stations
from stcode import stcodes
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

class Email:

    def __init__(self, train_info):
        # 车次信息
        self.train_info = train_info

        # 接收参数: 发件人地址
        self.from_addr = '172564615@qq.com'
        # 接收参数: 客户端授权密码
        self.passwd = 'qmowhxwduhaacabg'
        # 接收参数: 收件人地址,可多个
        self.to_addrs = [
            'liuxianglin@bjscfl.com',
            'nearwind_x@163.com'
        ]
        # 接收参数: SMTP服务器(注意:是发件人的smtp服务器)
        self.smtp_server = 'smtp.qq.com' # 注意是HTTPS服务

        # 接收参数: 邮件主题
        self.subject = '余票提醒'

        # 实例化正文
        self.html = ''  # 将邮件用HTML的形式发过去

        # 指定subtype为alternative，同时支持html和plain格式
        self.msg = MIMEMultipart('alternative')

        # 接收参数: 邮件正文
        for info in self.train_info:
            self.html += '<div><span>{0}</span> ' \
                          '<span style="color: red">{1}</span> ' \
                          '<span style="color: green">{2}</span> ' \
                          '<span>{3}</span> 还有余票，请尽快抢票 </div>'.format(info['train_date'], info['train_num'], info['train_trip'], info['train_time'])

        self.msg.attach(MIMEText(self.html, 'html', 'utf-8'))
        self.msg['Subject'] = Header(str(self.subject), 'utf-8').encode()
        self.msg['Date'] = formatdate()

    # =========================================================================
    # 发送邮件
    # =========================================================================
    def sendm(self):
        # SMTP服务器设置(地址,端口):
        server = smtplib.SMTP_SSL(self.smtp_server, 465)
        try:
            # server.set_debuglevel(1)
            # 连接SMTP服务器(发件人地址, 客户端授权密码)
            server.login(self.from_addr, self.passwd)

            # 发送邮件
            server.sendmail(self.from_addr, self.to_addrs, self.msg.as_string())

            print('邮件发送成功')

        except smtplib.SMTPException as e:
            print(e)
            print('邮件发送失败')

        finally:
            # 退出SMTP服务器
            server.quit()

# 封装一个简单的类来解析数据
class TrainsCollection:

    header = '车次 车站 时间 历时 一等 二等 软卧 硬卧 动卧 硬座 无座'.split()

    def __init__(self, available_trains, options, date):
        '''
        查询到的火车班次集合
        :param available_trains: 一个列表，包含可获得的火车班次，每个班次是一个字典
        :param options: 查询选项eg:高铁 动车 Z字头
        :param date 车次的出发日期
        '''

        self.available_trains = available_trains
        self.options = options
        self.date = date

    def _get_duration(self, raw_train):
        duration = raw_train[10].replace(':', '小时') + '分'
        return duration

    @property # 数据筛选
    def trains(self):
        for raw_train in self.available_trains:
            train_no = raw_train[3]
            initial = train_no[0].lower()  # 取车次中的首字母
            if not self.options or initial in self.options:
                train = [
                    train_no,
                    ' - '.join([stcodes[raw_train[6]] ,  # 起点站
                               stcodes[raw_train[7]]]), # 终点站
                    ' - '.join([raw_train[8], raw_train[9]]),
                    self._get_duration(raw_train),
                    raw_train[31],  #一等座
                    raw_train[30],  #二等座
                    raw_train[23],  #软卧
                    raw_train[28],  #硬卧
                    raw_train[33],  #动卧
                    raw_train[29],  #硬座
                    raw_train[26]   #无座
                ]
                yield train

    def send(self):
        train_info = []
        for train in self.trains:
            print(train)
            # 我现在只想二等，软卧，硬卧，所以筛选的时候手动设置一下
            if (train[5] != '无' and train[5] != '') or (train[6] != '无' and train[6] != '') or (train[7] != '无' and train[7] != ''):
                train_info.append({
                    'train_num': train[0],
                    'train_date': self.date,
                    'train_duration': train[3],
                    'train_trip': train[1],
                    'train_time': train[2]
                })
        if train_info:
            Email(train_info).sendm()

from_station = stations[input("请输入起点车站：")]
to_station = stations[input("请输入终点车站：")]
date = input("请输入出发日期：")
types = input("请输入车次类型：")

def search():
    url = 'https://kyfw.12306.cn/otn/leftTicket/queryX?leftTicketDTO.train_date={0}&leftTicketDTO.from_station={1}&leftTicketDTO.to_station={2}&purpose_codes=ADULT'.format(
        date, from_station, to_station)

    options = list(types)
    # 设置请求头，防止被12306屏蔽
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36'
    }
    # 关闭证书警告
    requests.packages.urllib3.disable_warnings()
    # 添加verify=False 不验证证书
    r = requests.get(url, headers=headers, verify=False)
    # 提取有效信息
    print(r)
    data = r.json()['data']['result']
    available_trains = []
    for item in data:
        available_trains.append(item.split('|'))
    TrainsCollection(available_trains, options, date).send()
    time.sleep(60)  # 刷新间隔，频率不建议太高，容易被12306封

if __name__ == '__main__':
    while True:
        try:
            search()
        except:
            search()
