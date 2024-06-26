import json
import os


class Config:
    _instance = None
    _is_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._is_initialized:
            self.config_file = 'config.json'
            self.data = self.load_config()
            self._is_initialized = True

    def load_config(self):
        if not os.path.exists(self.config_file):
            self.data = {
                'loginPayload': {'phone': 'xxx', 'password': 'xxx'},
                'cookie': {
                },
                'notifyOnInstanceStatusChanged': True,
                'serverchanUrl': ''
            }
            self.save_config()
            raise FileNotFoundError("配置文件不存在，请创建'config.json'文件并按正确格式填写.")
            # return self.data
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=4)

    def get_config(self):
        return self.data

    def update_config(self, key, value):
        if key in self.data:
            self.data[key] = value
            self.save_config()
