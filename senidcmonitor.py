import json
import random
import threading
import time
import datetime

import requests
import http.client
import urllib.parse
import re

from requests.adapters import HTTPAdapter
from urllib3 import Retry

from logger import log

from config import ConfigManager, InstanceAlertHandle, write_plugin_data, SenidcInstanceConfig
from data_model import InstanceStatus, InstanceOperation, UrlPath
from notify import send_notification

config = ConfigManager().data_obj


def is_today(timestamp) -> bool:
    today = datetime.date.today()
    date_of_timestamp = datetime.datetime.fromtimestamp(timestamp).date()
    return date_of_timestamp == today


def update_cookie(payload):
    host = "www.senidc.cn"
    url = "/login?action=phone"
    params = urllib.parse.urlencode(payload)
    connection = http.client.HTTPSConnection(host)
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    connection.request("POST", url, params, headers)

    response = connection.getresponse()
    log.debug(f"Status Code: {response.status}")

    if response.status != 302:
        connection.close()
        raise Exception("Expected HTTP status code 302, but received {}".format(response.status))

    cookies = response.getheader('Set-Cookie')
    if cookies is None:
        connection.close()
        raise Exception("No cookies set in response")

    log.debug(f"Set-Cookie: {cookies}")
    connection.close()

    match = re.findall(r'(ZJMF_.*?)=(.*?);', cookies)
    if not match:
        raise Exception("Expected cookie pattern not found in Set-Cookie header")

    return match[0]


def sign_in() -> str:
    host = "www.senidc.cn"
    url = "/addons?_plugin=points_mall&_controller=index&_action=sign"
    connection = http.client.HTTPSConnection(host)
    headers = {
        'Content-type': 'application/x-www-form-urlencoded',
        'Cookie': generate_cookie_string(config.account.cookies),
        'X-Requested-With': 'XMLHttpRequest',
    }
    connection.request("POST", url, None, headers)

    response = connection.getresponse()
    log.debug(f"Status Code: {response.status}")
    notify_msg = ''
    if response.status == 200:
        response_body = response.read().decode()

        msg = json.loads(response_body)['msg']
        if "成功" in response_body:
            notify_msg = f"签到成功, {msg}"
            config.account.last_sign_in = datetime.datetime.now().timestamp()
            write_plugin_data()
        else:
            notify_msg = f"签到失败, {msg}"
            if "已经" in response_body:
                config.account.last_sign_in = datetime.datetime.now().timestamp()
                write_plugin_data()
        log.info(notify_msg)
    else:
        notify_msg = f"签到失败，状态码: {response.status}"
        log.error(notify_msg)
    return notify_msg


def check_and_sign_in():
    if not config.preference.enable_sign_in:
        return
    if is_today(config.account.last_sign_in):
        return
    notify_msg = ''
    try:
        notify_msg = sign_in()
    except Exception as e:
        notify_msg = "签到异常"
        log.exception("签到异常")
    send_notification("Senidc-Sign_in", notify_msg)


def generate_cookie_string(cookies):
    cookie_parts = []
    for key, value in cookies.items():
        cookie_parts.append(f"{key}={value}")
    return "; ".join(cookie_parts)


class SenidcInstance:
    def __init__(self, machine_id: int, mosaic_id: str | None = None):
        self.base_domain = 'https://www.senidc.cn'
        self.machine_id = machine_id
        self.mosaic_id = machine_id if mosaic_id is None else mosaic_id
        self.status: InstanceStatus = InstanceStatus()
        self.last_status: InstanceStatus = InstanceStatus()
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def build_url(self, path, query_params=None):
        """
        拼接基本域名、路径和查询参数，返回完整的URL。
        """
        url = f"{self.base_domain}{path.value}"
        if query_params:
            query_string = '&'.join([f"{key}={value}" for key, value in query_params.items()])
            url += f"?{query_string}"
        return url

    def operate_instance(self, instance_operation: str) -> InstanceStatus:
        time.sleep(random.uniform(0, 2))
        global config
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Cookie': generate_cookie_string(config.account.cookies)
        }
        data = {
            'id': self.machine_id,
            'func': instance_operation
        }
        response = self.session.post(self.build_url(UrlPath.DEFAULT), headers=headers, data=data)
        if response.status_code != 200 or response.json().get('status') != 200:
            log.info("Cookie失效，尝试更新Cookie")
            new_cookie_name, new_cookie_value = update_cookie(
                {'phone': config.account.phone, 'password': config.account.password})
            if new_cookie_name and new_cookie_value:
                # 更新配置中的cookie
                config.account.cookies = {new_cookie_name: new_cookie_value}
                write_plugin_data()
                # 重新尝试请求
                headers['Cookie'] = f"{new_cookie_name}={new_cookie_value}"
                response = self.session.post(self.build_url(UrlPath.DEFAULT), headers=headers, data=data)
            # 更新cookie后尝试签到
            check_and_sign_in()
        if instance_operation != InstanceOperation.STATUS.value:
            return self.update_status()
        else:
            return InstanceStatus(response.json()['data']['status'], response.json()['data']['des'])

    def update_status(self) -> InstanceStatus:
        global config
        self.last_status = self.status
        self.status = self.operate_instance(InstanceOperation.STATUS.value)
        log.debug(f"更新实例 {self.mosaic_id} 状态 {self.status}")
        if self.last_status.status != self.status.status:
            log.info(f"实例 {self.mosaic_id} 状态变更: {self.last_status.status} -> {self.status.status}")
            if self.last_status.status and config.preference.notify_on_instanceStatusChanged and self.status.status != 'unknown' and self.last_status.status != 'unknown':
                send_notification("Senidc-Instance",
                                  f"实例 {self.mosaic_id} 状态变更: {self.last_status.status} -> {self.status.status}")
        return self.status


class SenidcInstanceChecker(SenidcInstance):
    def __init__(self, senidc_instance_config: SenidcInstanceConfig):
        super().__init__(senidc_instance_config.machine_id,
                         senidc_instance_config.mosaic_id if config.preference.use_mosaic_id else None)
        self.monitor_interval = senidc_instance_config.monitor_interval  # 监控间隔，单位秒
        self.timer: [threading.Timer, None] = None
        self.on_alert = senidc_instance_config.alert_handle  # 异常处理函数

    def start_monitor(self):
        interval = self.monitor_interval
        if self.status.status != 'on':
            interval = 10
        if self.status.status == 'unknown':
            interval = 30
        self.timer = threading.Timer(interval, self._check)
        self.timer.start()

    def _check(self):
        try:
            self.update_status()
            if self.status.status != 'on':
                self._default_alert()
                if not self.on_alert.continue_monitor:
                    return
        except Exception as e:
            log.exception("网络异常")
        self.start_monitor()

    def _default_alert(self):
        # 默认的异常处理策略
        log.info(f"Instance {self.mosaic_id} is down: {self.status.description}")
        if self.on_alert.send_notify and self.status.status != 'unknown':
            send_notification("Senidc-Instance Alert", f"Instance {self.mosaic_id} is down: {self.status.description}")
        if self.status.status == 'off' or self.status.status == 'paused':
            self.operate_instance(self.on_alert.operation)
