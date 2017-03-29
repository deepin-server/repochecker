Deepin 软件仓库辅助工具
-----------------------

## repochecker.py

用来检查仓库中的软件包是否存在依赖问题。

### 配置

如果要接收邮件报告，则可打开 `mail_config.ini`，配置邮箱及密码：

    # 发送者的邮箱
    send_mail = xxxxx@deepin.com
    # 发送者邮箱的密码
    send_mail_pass = xxxxxxxx
    # 接收者的邮箱，多个使用 , 分隔
    receive_mail = xxxxx@deepin.com, yyyyyy@deepin.com

### 用法

    ./repochecker.py
    Usage: repochecker.py [options]

    Options:
    -h, --help     show this help message and exit
    -m CHECK_MODE  cb: check broken package. cd: check build depends.
    -f             filter packages
    -d             debug information
    -s             send mail

选项说明：

+ `-m`：检查模式，包括：`cb`，检查软件包的运行依赖；`cd`，检查软件包的构建依赖
+ `-f`：过滤包
+ `-d`：打印调试信息
+ `-s`：发送邮件报告

例如，要检查仓库中软件包的运行依赖，可以执行：

    ./repochecker.py -m cb -f
