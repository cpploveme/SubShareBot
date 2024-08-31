# 订阅分发Bot

订阅分发Bot 是一个调用 `Telegram Api` 的机场订阅分发项目，可以方便的在 `Telegram` 平台重置或替换订阅链接，已导入的设备仅需更新订阅即可方便地更新新的节点配置，也可避免更新订阅造成的 ip 泄露问题。

> 请勿滥用此项目来共享订阅链接等 造成的问题一概不负责

## 关于数据安全

订阅分发Bot 处理的所有的数据都不会以任何方式保存：包括但不限于 Telegram 消息、系统日志。

订阅分发Bot 会在 config.yaml 文件中存储订阅信息(但仅限于使用 /new 添加的订阅)。

订阅分发Bot 不会记录任何 IP、地理位置等数据，但仍会记录获取订阅的时间以及获取此订阅的密钥以便检查订阅是否泄露。

订阅分发Bot 仅会主动连接 Telegram 服务器、订阅服务器、订阅转换服务器（如果你配置了）。除此之外它不会与任何其他的服务器发送任何形式的通讯。

## 机器人安装方法

> 项目需要执行两个文件 `server.py` `bot.py` 分别对应订阅拉取功能和Bot前端

### 搭建

> 这里以 `Debian` 系统为例

你首先可能需要安装软件包

```bash
apt install git python3-pip -y
```

然后拉取项目

```bash
git clone https://github.com/cpploveme/SubShareBot.git
```

安装依赖

```bash
pip install PyYAML telebot aiohttp retry loguru
```

> 对于高版本且非虚拟环境搭建的Bot你可能需要加上 `--break-system-packages`

由于此项目有两个文件，你需要同时执行 `server.py` 与 `bot.py` 才可以正常运行。

关于如何持久化运行这里不会详细说，你可以参考 `screen`, `pm2`, `systemd` 等方法。

### 机器人配置说明

> 建议参看 `readme.config.yaml` 内的详细说明，也可以使用 `example.config.yaml` 的样例配置。

#### 必要配置

`SuAdmin`：不填入则 Bot 无法启动。

`TelegramBotToken`：不填入则 Bot 无法启动，`Bot Token` 可以在 `@BotFather` 获取。

`WebServer`：不填入则无法开启服务端拉取订阅链接。

#### 可选配置

建议填写 `Convert` 以便可以使用自带的自动转换功能导入订阅而无需指定订阅类型。

`Subscribe` 可以不提前填写，而使用 Bot 命令来进行操作。

#### 权限相关

##### 超级管理

超级管理是最大的管理层级，它有最大的操作权限。这意味着，有超管可以随意读取、写入任何 config.yaml 中的配置，也可以对 Bot 本身进行操作。超管可以使用 `/grant` 指令授权一个 Telegram 用户为普通管理。（`/ungrant` 来解除授权）

配置文件（数组，如果只有一个也必须有 `- ` 注意空格）：
```yaml
SuAdmin:
- 11111
- 22222
```

##### 普通管理

普通管理可以进行订阅的增添删除以及密钥的设置，但无法操作除 `Subscribe` 外的其他配置。

**Bot 会默认开启防拉群功能，非普通管理或超级管理的用户在拉 Bot 入群时 Bot 会自己退出群聊。**

## 机器人使用方法

### 公共指令

#### /help

获取帮助菜单

#### /version

查询机器人版本信息

#### /stats

查询自身权限状态，如果是管理员，还会展示目前订阅的数量

### 订阅操作指令

只能由管理、超级管理调用。

#### /new <订阅名称> <订阅链接>

新增一个订阅

#### /remove <订阅名称>

删除一个订阅

#### /generate <订阅名称> <密钥> <可选:获取次数> <可选:获取时间限制>

对一个已添加的订阅新增一个密钥以便获取此订阅。

后两个参数为可选参数，不填则为不限制，但如果想限制获取时间而不限制次数则仍需在第三个参数的位置填入 -1。

若此密钥已添加过则会覆盖之前的限制。

#### /consume <订阅名称> <密钥>

删除此订阅下的密钥

#### /sub

获取已添加的订阅列表

### 超级管理指令

仅能由超级管理调用。

#### /grant <可选:id>

回复一个用户将其权限提升为管理员，也可在命令后跟着一个 id，会被写入到 `Admin`。

#### /ungrant <可选:id>

回复一个用户将其取消管理员，也可在命令后跟着一个 id，会被从 `Admin` 移除。

#### /list

查看已授权的 id 列表

#### /leave

从此群聊中离开

#### /get <路径>

对配置文件进行读取。你需要对 `config.yaml` 配置文件非常熟悉。例如，你想获取 订阅转换的后端 的值：

```
/get Convert.Backend
返回：
✔ 读取成功啦 ~

键: Convert.Backend
值: https://api.ytools.cc/
```

再例如，你想获取 mycloud 这个订阅的订阅链接：
```
/get Subscribe.mycloud.Url
返回：
✔ 读取成功啦 ~

键: Subscribe.mycloud.Url
值: https://mycloud.com/api/v1/client/subscribe?token=1145141919810
```

#### /set <路径> <值>

同上，只是这次我们设置这个值。

#### /logs <数量>

倒叙读取日志

#### /stop

关闭 Bot 的程序

## 订阅链接使用方法

服务端会读取你访问的路径作为密钥来判断，并拉取订阅链接并返回节点信息，**部分格式订阅会替换开头的订阅链接为你获取的地址以免暴露原订阅链接**。

比如，你的配置文件按照以下方式填写：

```
Subscribe:
  mycloud:
    Token:
      Abc123:
        Count: -1
        Expire: -1
    Url: https://mycloud.com/api/v1/client/subscribe?token=1145141919810
  aaanet:
    Token:
      AaanetSubToken:
        Count: -1
        Expire: -1
    Url: https://aaa.net/link/114514?clash=1

WebServer:
  Path: /subscribe/token/
  Port: 34567
```

假如你的服务器 ip 为 `1.2.3.4`，如果你想获取 `mycloud` 订阅，那么你需要将服务器的 34567 端口开放，并访问 `http://1.2.3.4:34567/subscribe/token/Abc123` 来获取订阅信息。

如果你想将 `mycloud` 和 `aaanet` 合并获取，那么你可以用 `&` 来分割不同密钥来访问订阅，如 `http://1.2.3.4:34567/subscribe/token/Abc123&AaanetSubToken`

在开启了订阅转换后 (`Convert.Enable` 为 `1`)，服务端会自动识别 User-Agent 来决定目标订阅的类型，无需再次转换。

如果你没有开启订阅转换，那么服务端会在请求订阅链接时使用你请求的 User-Agent 以便机场订阅来识别类型。

如果你想指定获取的订阅类型，那么在开启了订阅转换后你可以通过参数 `flag` 来设置类型，如 `http://1.2.3.4:34567/subscribe/token/Abc123?flag=clash`。参数 `flag` 的值会被直接传递为访问的订阅转换链接的类型，那么你可能需要参看 [订阅转换文档](https://github.com/tindy2013/subconverter/blob/master/README-cn.md#%E6%94%AF%E6%8C%81%E7%B1%BB%E5%9E%8B) 以便使用。

## 免责声明

请勿滥用此项目来进行共享订阅链接等违反机场 TOS 的行为，造成的问题一概不负责

## 引用

[订阅转换项目地址](https://github.com/tindy2013/subconverter/)