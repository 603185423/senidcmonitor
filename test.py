from time import sleep

from config import InstanceAlertHandle, SenidcInstanceConfig, ConfigManager
from logger import log

from data_model import InstanceOperation
from senidcmonitor import SenidcInstanceChecker

config = ConfigManager().data_obj

log.info("开始监控")

for instance in config.instance:
    log.info(f'添加实例 {instance.machine_id} 监控, mosaic_id = {instance.mosaic_id}')
    SenidcInstanceChecker(instance).start_monitor()
    sleep(5)

while True:
    pass
