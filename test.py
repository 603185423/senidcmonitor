from logger import log

from data_model import InstanceOperation, InstanceAlertHandle
from senidcmonitor import SenidcInstanceChecker

log.info("开始监控")
checker = SenidcInstanceChecker(9758, 3 * 60, InstanceAlertHandle(True, InstanceOperation.HARD_REBOOT, True))
checker.start_monitor()
while True:
    pass
