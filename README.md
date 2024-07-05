# senidcmonitor

## 配置文件说明

配置文件 `config.yaml` 包含以下几个部分：

### 偏好设置

- `notify_on_instanceStatusChanged`: 实例状态发生变化时是否通知，布尔值。
- `serverchan_url`: Server酱的通知URL，用于发送通知消息。

### 账户信息

- `phone`: 登录账户的手机号。
- `password`: 登录密码。
- `cookies`: 不需要填写。

### 实例信息

配置多个机器实例的监控与管理：

- `machine_id`: 机器ID。
- `monitor_interval`: 监控间隔时间，单位为秒。
- `alert_handle`: 报警处理配置。
  - `send_notify`: 是否发送通知。
  - `operation`: 发生报警时的操作（如 `reboot` 表示重启机器）。
  - `continue_monitor`: 报警处理后是否继续监控。

## 首次运行

首次运行 `test.py` 时，系统会自动生成 `./data/config.yaml` 配置文件。

## 如何使用

1. 确保已经按照上述配置编辑好 `config.yaml` 文件。
2. 运行 `test.py` 脚本启动监控程序。
3. 根据日志和Server酱的通知来查看实例状态及处理结果。

## 注意事项

- 确保 `serverchan_url` 正确无误，以保证能成功接收到通知。
- 监控间隔请根据实际情况合理设置，以避免过于频繁的检查造成系统负担。

## 配置示例

```yaml
preference:
    notify_on_instanceStatusChanged: true
    serverchan_url: https://sctapi.ftqq.com/AAAAAAA.send
account:
    phone: '13300001111'
    password: '111111'
    cookies: ""
instance:
-   machine_id: 8105
    monitor_interval: 900
    alert_handle:
        send_notify: true
        operation: reboot
        continue_monitor: true
-   machine_id: 8104
    monitor_interval: 900
    alert_handle:
        send_notify: true
        operation: reboot
        continue_monitor: true
```

