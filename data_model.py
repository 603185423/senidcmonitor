from enum import Enum
from typing import NamedTuple


class UrlPath(Enum):
    DEFAULT = '/provision/default'
    TRAFFIC_USAGE = '/host/trafficusage'
    CHART = '/provision/chart'


class InstanceOperation(Enum):
    NONE = 'status'
    STATUS = 'status'
    ON = 'on'
    OFF = 'off'
    REBOOT = 'reboot'
    HARD_OFF = 'hard_off'
    HARD_REBOOT = 'hard_reboot'


class InstanceStatus(NamedTuple):
    status: str = ''
    description: str = 'empty status'
