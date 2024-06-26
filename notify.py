import threading

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from config import ConfigManager
from logger import log

config = ConfigManager().data_obj


class NotificationSender:
    def __init__(self):
        self.lock = threading.Lock()
        self.notifications = []
        self.api_url = config.preference.serverchan_url
        self.timer = threading.Timer(30, self.send_notifications)
        self.timer.start()

    def send_notification(self, title, desp):
        with self.lock:
            self.notifications.append((title, desp))

    def send_notifications(self):
        if not self.api_url:
            return
        with self.lock:
            if self.notifications:
                title = "Senidc"
                desp = '\n'.join(f"{t}:{d}" for t, d in self.notifications)
                data = {"title": title, "desp": desp}
                session = requests.Session()
                retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
                session.mount('http://', HTTPAdapter(max_retries=retries))
                session.mount('https://', HTTPAdapter(max_retries=retries))
                try:
                    response = session.post(self.api_url, data=data)
                    log.info("通知已发送")
                except Exception as e:
                    log.error("发送通知时出现异常：", str(e))
            self.notifications = []
        # 重置定时器
        self.timer = threading.Timer(30, self.send_notifications)
        self.timer.start()

    def stop(self):
        self.timer.cancel()


# 单例模式实例化
sender_instance = NotificationSender()


# 使用
def send_notification(title, desp):
    sender_instance.send_notification(title, desp)
