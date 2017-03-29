Deepin 软件仓库辅助工具
-----------------------

## repochecker.py

用来检查仓库中的软件包是否存在依赖问题。

### 用法

    ./repochecker.py
    Usage: check-depends.py [options]

    Options:
    -h, --help     show this help message and exit
    -m CHECK_MODE  cb: check broken package. cd: check build depends.
    -f             filter packages
    -d             debug information

选项说明：

+ `-m`：检查模式，包括：`cb`，检查软件包的运行依赖；`cd`，检查软件包的构建依赖
+ `-f`：过滤包
+ `-d`：打印调试信息

例如，要检查仓库中软件包的运行依赖，可以执行：

    ./repochecker.py -m cb -f
