from config import InstanceAlertHandle, SenidcInstanceConfig, ConfigManager
from logger import log

from data_model import InstanceOperation
from senidcmonitor import SenidcInstanceChecker

config = ConfigManager().data_obj

log.info("开始监控")

for instance in config.instance:
    log.info(f'添加实例 {instance.machine_id} 监控')
    SenidcInstanceChecker(instance).start_monitor()

while True:
    pass
