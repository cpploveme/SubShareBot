import os
import re
import time
import yaml
import copy
import base64
import telebot
import aiohttp
import asyncio
from aiohttp import web
from loguru import logger
from threading import Thread
from collections import deque
from telebot.async_telebot import AsyncTeleBot

version_content = "1.0.0"
version_id = 23121801
logger.add('Bot.log')

class Config:
    def __init__(self, configpath="./config.yaml"):
        logger.info('Initializing Config')
        self.config = {}
        try:
            with open(configpath, "r", encoding="UTF-8") as fp:
                self.config = yaml.safe_load(fp)
        except FileNotFoundError:
            logger.error("Config not found")
            os._exit(0)
    
    def reload(self, configpath="./config.yaml"):
        self.config = {}
        try:
            with open(configpath, "r", encoding="UTF-8") as fp:
                self.config = yaml.safe_load(fp)
        except FileNotFoundError:
            logger.error("Config not found")
            os._exit(0)

    def Save(self, configpath="./config.yaml"):
        with open(configpath, "w", encoding="UTF-8") as fp:
            yaml.safe_dump(self.config, fp)

    def LoadBotToken(self):
        try:
            logger.info('Obtaining Telegram Bot Token')
            return self.config['TelegramBotToken']
        except:
            logger.error("Telegram Bot Token not found")
            os._exit(0)
    
    def LoadSuAdmin(self):
        try:
            logger.info('Obtaining SuAdmin')
            return self.config['SuAdmin']
        except:
            logger.error("SuAdmin not found")
            os._exit(0)
    
    def LoadAdmin(self):
        try:
            logger.info('Obtaining Admin')
            return self.config['Admin']
        except:
            logger.warning("Admin not found")
            return []
    
    def AddAdmin(self, user: list or str or int):
        userlist = []
        if type(user).__name__ == "list":
            for li in user:
                userlist.append(int(li))
        else:
            userlist.append(int(user))
        try:
            old = self.config['Admin']
            if old is not None:
                userlist.extend(old)
            newuserlist = []
            for i in userlist:
                if not i in newuserlist:
                    newuserlist.append(i)
            self.config['Admin'] = newuserlist
            
            logger.info(f"Add Admin {user}")
        except KeyError:
            newuserlist = []
            for i in userlist:
                if not i in newuserlist:
                    newuserlist.append(i)
            self.config['Admin'] = newuserlist
            logger.info(f"Add Admin {user}")
    
    def RemoveAdmin(self, user: list or str or int):
        userlist = self.config['Admin']
        if type(user).__name__ == "list":
            for li in user:
                try:
                    userlist.remove(int(li))
                    logger.info(f"Remove Admin {int(li)}")
                except:
                    logger.warning(f"User {int(li)} is not in the Admin List")
        else:
            try:
                userlist.remove(int(user))
                logger.info(f"Remove Admin {int(user)}")
            except:
                logger.warning(f"User {int(user)} is not in the Admin List")
        self.config['Admin'] = userlist
    
    def LoadPort(self):
        try:
            logger.info('Obtaining WebServer Port')
            return self.config['WebServer']['Port']
        except:
            logger.warning("WebServer Port not found")
            return 12345
    
    def LoadPath(self):
        try:
            logger.info('Obtaining WebServer Path')
            return self.config['WebServer']['Path']
        except:
            logger.warning("WebServer Path not found")
            return '/subcribe/token/'
    
    def AddSub(self, name: str, url: str):
        try:
            logger.info(f'Add Sub {name} {url}')
            if self.config['Subscribe'].get(name) == None:
                self.config['Subscribe'][name] = {'Url': url, 'Token': {}}
                return 1
            else:
                self.config['Subscribe'][name]['Url'] = url
                return 2
        except:
            logger.warning("Add Sub Error")
            return -1
    
    def RemoveSub(self, name: str):
        try:
            if not name in self.config['Subscribe']:
                logger.warning(f"Sub {name} Does Not Exist")
                return False
            else:
                logger.info(f'Remove Sub {name}')
                del self.config['Subscribe'][name]
                return True
        except:
            logger.warning("Remove Sub Error")
            return False
    
    def AddToken(self, name: str, token: str, info: dict):
        try:
            logger.info(f'Add Token {name} {token}')
            for sub_name in self.config['Subscribe']:
                if token in self.config['Subscribe'][sub_name]['Token']:
                    if not sub_name == name:
                        return 3
            if self.config['Subscribe'].get(name) == None:
                return 0
            elif self.config['Subscribe'][name]['Token'].get(token) == None:
                self.config['Subscribe'][name]['Token'][token] = info
                return 1
            else:
                self.config['Subscribe'][name]['Token'][token] = info
                return 2
        except:
            logger.warning("Add Token Error")
            return -1
    
    def RemoveToken(self, name: str, token: str):
        try:
            logger.info(f'Remove Token {name} {token}')
            if self.config['Subscribe'].get(name) == None:
                return 0
            elif self.config['Subscribe'][name]['Token'].get(token) == None:
                return 1
            else:
                del self.config['Subscribe'][name]['Token'][token]
                return 2
        except:
            logger.warning("Remove Token Error")
            return -1

    def FindToken(self, token: str):
        try:
            logger.info(f'Finding Token {token}')
            for sub_name in self.config['Subscribe']:
                if token in self.config['Subscribe'][sub_name]['Token']:
                    try:
                        exp = self.config['Subscribe'][sub_name]['Token'][token]['Expire']
                        if exp != -1 and int(time.time()) > exp:
                            logger.info(f'Token {token} Expire')
                            return 'Token Expire'
                    except:
                        pass
                    try:
                        count = self.config['Subscribe'][sub_name]['Token'][token]['Count']
                        if count != -1 and count <= 0:
                            logger.info(f'Token {token} Expire')
                            return 'Token Expire'
                    except:
                        pass
                    return {'url': self.config['Subscribe'][sub_name]['Url'], 'subname': sub_name}
            logger.info(f'Token {token} Not Found')
            return 'Token Not Found'
        except:
            logger.warning(f'Token {token} Error')
            return 'Token Error'
    
    def LoadConvert(self):
        try:
            logger.info(f'Load Convert')
            return self.config['Convert']
        except:
            logger.warning("Convert Not Found")
            return None

config = Config()
bot = AsyncTeleBot(config.LoadBotToken())

su_admin_list = config.LoadSuAdmin()
admin_list = config.LoadAdmin()

web_port = config.LoadPort()
web_path = config.LoadPath()

def reloadConfig():
    global su_admin_list, admin_list
    su_admin_list = config.LoadSuAdmin()
    admin_list = config.LoadAdmin()
    config.reload()

result = {}

async def get_token(request):
    token = request.match_info['token']
    try :
        resp = config.FindToken(token)
        url = resp['url']
        subname = resp['subname']
    except:
        return web.Response(body=resp, content_type='text/plain')
    try:
        headers = {'User-Agent': request.headers['User-Agent']}
    except:
        headers = {'User-Agent': 'ClashMetaForAndroid/2.8.9.Meta'}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as res:
                text = await res.text()
        try:
            if config.config['Subscribe'][subname]['Token'][token]['Count'] != -1:
                config.config['Subscribe'][subname]['Token'][token]['Count'] = config.config['Subscribe'][subname]['Token'][token]['Count'] - 1
                config.Save()
        except:
            pass
        return web.Response(body=text, headers={'Content-Disposition': f'attachment; filename="{subname}"'}, content_type='text/plain')
    except:
        return web.Response(body="", content_type='text/plain')

app = web.Application()
app.router.add_get(web_path + '{token}', get_token)

def convert_space(s: str) -> str:
    temp = ""
    i = 0
    while i < len(s):
        try:
            if s[i] == "\\" and s[i + 1] == "s":
                temp = temp + " "
                i = i + 2
            elif s[i] == "\\" and s[i + 1] == "\\":
                temp = temp + "\\"
                i = i + 2
            else:
                temp = temp + s[i]
                i = i + 1
        except:
            temp = temp + s[i]
            i = i + 1
    return temp

def set_config(data: dict, pos: list, value: str):
    if len(pos) == 1:
        try:
            data[pos[0]] = int(value)
        except:
            data[pos[0]] = value
    else:
        data[pos[0]] = set_config(data[pos[0]], pos[1:], value)
    return data

async def deletecommand(msg, message, t: int):
    await asyncio.sleep(t)
    try:
        await bot.delete_message(msg.chat.id, msg.message_id)
    except:
        pass
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

# 新增订阅
@bot.message_handler(commands=['new'])
async def new_sub(message):
    if not int(message.from_user.id) in admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请联系管理员授权 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        config.reload()
        name = message.text.split()[1]
        url = message.text.split()[2]
        stat = config.AddSub(name, url)
        config.Save()
        if stat == 1:
            msg = await bot.reply_to(message, f"✔ 已新增订阅 `{name}` - `{url}` ~", parse_mode = 'Markdown')
            await deletecommand(msg, message, 15)
        elif stat == 2:
            msg = await bot.reply_to(message, f"✔ 已覆盖订阅 `{name}` - `{url}` ~", parse_mode = 'Markdown')
            await deletecommand(msg, message, 15)
    except Exception as e:
        msg = await bot.reply_to(message, f"❌ 新增订阅失败\n\n错误: `{e}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)

# 删除订阅
@bot.message_handler(commands=['remove'])
async def remove_sub(message):
    if not int(message.from_user.id) in admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请联系管理员授权 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        config.reload()
        name = message.text.split()[1]
        stat = config.RemoveSub(name)
        config.Save()
        if stat == 1:
            msg = await bot.reply_to(message, f"✔ 已删除订阅 `{name}` ~", parse_mode = 'Markdown')
            await deletecommand(msg, message, 15)
        else:
            msg = await bot.reply_to(message, f"❌ 删除订阅失败\n\n错误: `订阅 {name} 不存在`", parse_mode = 'Markdown')
            await deletecommand(msg, message, 15)
    except Exception as e:
        msg = await bot.reply_to(message, f"❌ 删除订阅失败\n\n错误: `{e}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)

# 新增密钥
@bot.message_handler(commands=['generate'])
async def generate_token(message):
    if not int(message.from_user.id) in admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请联系管理员授权 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        config.reload()
        name = message.text.split()[1]
        token = message.text.split()[2]
        try:
            count = int(message.text.split()[3])
        except:
            count = -1
        try:
            exp = int(message.text.split()[4])
        except:
            exp = -1
        stat = config.AddToken(name, token, {'Count': count, 'Expire': exp})
        config.Save()
        if stat == 0:
            msg = await bot.reply_to(message, f"❌ 新增密钥失败\n\n错误: `订阅 {name} 不存在`", parse_mode = 'Markdown')
            await deletecommand(msg, message, 15)
        elif stat == 1:
            msg = await bot.reply_to(message, f"✔ 已新增密钥 `{token}` ~", parse_mode = 'Markdown')
            await deletecommand(msg, message, 15)
        elif stat == 2:
            msg = await bot.reply_to(message, f"✔ 已覆盖密钥 `{token}` ~", parse_mode = 'Markdown')
            await deletecommand(msg, message, 15)
        elif stat == 3:
            msg = await bot.reply_to(message, f"❌ 新增密钥失败\n\n错误: `密钥 {token} 已存在`", parse_mode = 'Markdown')
            await deletecommand(msg, message, 15)
    except Exception as e:
        msg = await bot.reply_to(message, f"❌ 新增密钥失败\n\n错误: `{e}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)

# 新增密钥
@bot.message_handler(commands=['consume'])
async def consume_token(message):
    if not int(message.from_user.id) in admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请联系管理员授权 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        config.reload()
        name = message.text.split()[1]
        token = message.text.split()[2]
        stat = config.RemoveToken(name, token)
        config.Save()
        if stat == 0:
            msg = await bot.reply_to(message, f"❌ 删除密钥失败\n\n错误: `订阅 {name} 不存在`", parse_mode = 'Markdown')
            await deletecommand(msg, message, 15)
        elif stat == 1:
            msg = await bot.reply_to(message, f"❌ 删除密钥失败\n\n错误: `密钥 {token} 不存在`", parse_mode = 'Markdown')
            await deletecommand(msg, message, 15)
        elif stat == 2:
            msg = await bot.reply_to(message, f"✔ 已删除密钥 `{token}` ~", parse_mode = 'Markdown')
            await deletecommand(msg, message, 15)
    except Exception as e:
        msg = await bot.reply_to(message, f"❌ 删除密钥失败\n\n错误: `{e}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)

# 获取订阅列表
@bot.message_handler(commands=['sub'])
async def get_sub_list(message):
    if not int(message.from_user.id) in admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请联系管理员授权 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        config.reload()
        logger.info(f"Admin {message.from_user.id} Get Sub List")
        msg = await bot.reply_to(message, f"✔ 订阅列表:\n\n `{list(config.config['Subscribe'].keys())}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 15)
    except Exception as e:
        msg = await bot.reply_to(message, f"❌ 获取订阅列表失败\n\n错误: `{e}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)

# 获取密钥列表
@bot.message_handler(commands=['token'])
async def get_token_list(message):
    if not int(message.from_user.id) in admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请联系管理员授权 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        config.reload()
        logger.info(f"Admin {message.from_user.id} Get Token List")
        name = message.text.split()[1]
        if config.config['Subscribe'].get(name) == None:
            msg = await bot.reply_to(message, f"❌ 获取密钥列表失败\n\n错误: `订阅 {name} 不存在`", parse_mode = 'Markdown')
            await deletecommand(msg, message, 10)
            return
        msg = await bot.reply_to(message, f"✔ 密钥列表:\n\n `{list(config.config['Subscribe'][name]['Token'].keys())}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 15)
    except Exception as e:
        msg = await bot.reply_to(message, f"❌ 获取密钥列表失败\n\n错误: `{e}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)



# 获取授权列表
@bot.message_handler(commands=['list'])
async def get_list(message):
    if not int(message.from_user.id) in su_admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请在配置文件中设置呢 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        logger.info(f"Su Admin {message.from_user.id} Get Grant List")
        reloadConfig()
        msg = await bot.reply_to(message, f"✔ 已授权用户列表:\n\n `{admin_list}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 15)
    except Exception as e:
        msg = await bot.reply_to(message, f"❌ 获取用户失败\n\n错误: `{e}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)

# 离开群聊
@bot.message_handler(commands=['leave'])
async def leave_group(message):
    try:
        logger.info(f"Escape The Group {message.chat.id}")
        await bot.leave_chat(message.chat.id)
    except :
        return

# 防拉群
@bot.message_handler(func=lambda m: True, content_types=['new_chat_members'])
async def auto_leave(message):
    bot_name = await bot.get_me()
    if not message.json['new_chat_participant']['username'] in bot_name.username :
       return
    try:
        if not int(message.from_user.id) in admin_list:
            logger.info(f"Automatically Escape The Group")
            try :
                await bot.reply_to(message, "❌ 机器人已启动防拉群模式 请联系管理员拉群 ~")
                await bot.leave_chat(message.chat.id)
            except :
                pass
    except:
        await bot.reply_to(message, "❌ 机器人已启动防拉群模式 请联系管理员拉群 ~")
        await bot.leave_chat(message.chat.id)

# 授权
@bot.message_handler(commands=['grant'])
async def grant(message):
    if not int(message.from_user.id) in su_admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请在配置文件中设置呢 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        grantlist = []
        try:
            grantlist.append(int(message.reply_to_message.from_user.id))
            config.AddAdmin(int(message.reply_to_message.from_user.id))
        except:
            for arg in message.text.split()[1:]:
                config.AddAdmin(int(arg))
                grantlist.append(int(arg))
        config.Save()
        reloadConfig()
        msg = await bot.reply_to(message, f"✔ 已授权用户 `{grantlist}` ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 15)
    except Exception as e:
        msg = await bot.reply_to(message, f"❌ 授权失败\n\n错误: `{e}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)

# 取消授权
@bot.message_handler(commands=['ungrant'])
async def ungrant(message):
    if not int(message.from_user.id) in su_admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请在配置文件中设置呢 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        ungrantlist = []
        try:
            ungrantlist.append(int(message.reply_to_message.from_user.id))
            config.RemoveAdmin(int(message.reply_to_message.from_user.id))
        except:
            for arg in message.text.split()[1:]:
                config.RemoveAdmin(int(arg))
                ungrantlist.append(int(arg))
        config.Save()
        reloadConfig()
        msg = await bot.reply_to(message, f"✔ 已取消授权用户 `{ungrantlist}` ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 15)
    except Exception as e:
        msg = await bot.reply_to(message, f"❌ 取消授权失败\n\n错误: `{e}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)

# 获取配置
@bot.message_handler(commands=['get'])
async def getting_config(message):
    if not int(message.from_user.id) in su_admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请在配置文件中设置呢 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        config.reload()
        try:
            if message.text.split()[1].split('.')[0] == "TelegramBotToken":
                msg = await bot.reply_to(message, f"❌ 获取配置失败\n\n错误: `已屏蔽的路径 {message.text.split()[1].split('.')[0]}`", parse_mode = 'Markdown')
                await deletecommand(msg, message, 10)
                return
        except:
            pass
        data = copy.deepcopy(config.config)
        if len(message.text.split()) == 1:
            data.pop("TelegramBotToken")
            logger.info(f"Su Admin {message.from_user.id} Get All Config")
            msg = await bot.reply_to(message, f"✔ 读取成功啦 ~\n\n键 `全部配置`\n值 `{str(data)}`", parse_mode = 'Markdown')
            await deletecommand(msg, message, 15)
            return
        for item in message.text.split()[1].split('.'):
            data = data[item]
        logger.info(f"Su Admin {message.from_user.id} Get Config {message.text.split()[1]}")
        msg = await bot.reply_to(message, f"✔ 读取成功啦 ~\n\n键 `{message.text.split()[1]}`\n值 `{str(data)}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 15)
    except Exception as e:
        msg = await bot.reply_to(message, f"❌ 获取配置失败\n\n错误: `{e}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)

# 设置配置
@bot.message_handler(commands=['set'])
async def setting_config(message):
    if not int(message.from_user.id) in su_admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请在配置文件中设置呢 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        config.reload()
        try:
            if message.text.split()[1].split('.')[0] == "TelegramBotToken" or message.text.split()[1].split('.')[0] == "SuAdmin":
                msg = await bot.reply_to(message, f"❌ 设置配置失败\n\n错误: `已屏蔽的路径 {message.text.split()[1].split('.')[0]}`", parse_mode = 'Markdown')
                await deletecommand(msg, message, 10)
                return
        except:
            pass
        old = "None"
        try:
            data = copy.deepcopy(config.config)
            for item in message.text.split()[1].split('.'):
                data = data[item]
            old = str(data)
            if data.keys():
                msg = await bot.reply_to(message, f"❌ 设置配置失败\n\n错误: `路径 {message.text.split()[1]} 下有其他值`", parse_mode = 'Markdown')
                await deletecommand(msg, message, 10)
                return
        except:
            pass
        cont = convert_space(message.text.split()[2])
        if len(message.text.split()) > 3:
            for c in message.text.split()[3:]:
                cont = cont + " " + convert_space(c)
        config.config = set_config(copy.deepcopy(config.config), message.text.split()[1].split('.'), cont)
        config.Save()
        reloadConfig()
        logger.info(f"Su Admin {message.from_user.id} Set Config {message.text.split()[1]} Into {cont}")
        msg = await bot.reply_to(message, f"✔ 设置成功啦 ~\n\n键 `{message.text.split()[1]}`\n原始值 `{old}`\n修改值 `{cont}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 15)
    except Exception as e:
        msg = await bot.reply_to(message, f"❌ 设置配置失败\n\n错误: `{e}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)

# 获取日志
@bot.message_handler(commands=['logs'])
async def get_log(message):
    if not int(message.from_user.id) in su_admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请在配置文件中设置呢 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        logger.info(f"Su Admin {message.from_user.id} Get logs")
        config.reload()
        n = int(message.text.split()[1])
        last_lines = deque(maxlen=n)
        with open('Bot.log', 'r', encoding='utf-8') as f:
            for line in f:
                last_lines.append(line)
        str1 = ''.join(last_lines)
        await bot.reply_to(message, f"✔ 读取成功啦:\n条目信息 后 `{n}` 条\n`{str1}`", parse_mode = 'Markdown')
    except Exception as e:
        msg = await bot.reply_to(message, f"❌ 获取日志失败\n\n错误: `{e}`", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)

# 关闭程序
@bot.message_handler(commands=['stop'])
async def stop_bot(message):
    if not int(message.from_user.id) in su_admin_list:
        msg = await bot.reply_to(message, f"❌ 您没有权限呢 请在配置文件中设置呢 ~", parse_mode = 'Markdown')
        await deletecommand(msg, message, 10)
        return
    try:
        logger.info(f"Su Admin {message.from_user.id} Stop Bot")
        await bot.reply_to(message, f"✔ 正在关闭 `Bot` ~", parse_mode = 'Markdown')
        os._exit(1)
    except :
        return

async def reloadCommand():
    command_list = [
            telebot.types.BotCommand("help", "获取帮助菜单"),
            telebot.types.BotCommand("version", f"获取版本信息 - {version_content}({version_id})"),
            telebot.types.BotCommand("stats", "获取权限状态"),
            telebot.types.BotCommand("new", "新增订阅"),
            telebot.types.BotCommand("remove", "删除订阅"),
            telebot.types.BotCommand("generate", "生成密钥"),
            telebot.types.BotCommand("consume", "删除密钥"),
            telebot.types.BotCommand("sub", "获取订阅列表"),
            telebot.types.BotCommand("token", "获取密钥列表")
        ]
    await bot.set_my_commands(
        commands=command_list,
    )

@bot.message_handler(commands=['help'])
async def help(message):
    logger.info(f"User {message.from_user.id} Get Help")
    bot_name = await bot.get_me()
    content = "欢迎使用 `" + bot_name.first_name + "` 呢  你可以使用以下指令呢 ~\n\n/help `获取帮助菜单`\n/version `获取版本信息 - " + version_content + "(" + str(version_id) + ")`\n/stats `获取权限状态`\n"
    if int(message.from_user.id) in admin_list:
        content = content + """/new `[管理]新增订阅`
/remove `[管理]删除订阅`
/generate `[管理]生成密钥`
/consume `[管理]删除密钥`
/sub `[管理]获取订阅列表`
/token `[管理]获取密钥列表`
"""
    if int(message.from_user.id) in su_admin_list:
        content = content + """/grant `[超管]授权目标对象`
/ungrant `[超管]取消授权目标对象`
/list `[超管]获取目前所有的授权者`
/set `[超管]写入配置文件`
/get `[超管]读取配置文件`
/logs `[超管]倒序输出日志`
/stop `[超管]关闭程序`
"""
    msg = await bot.reply_to(message, content, parse_mode = 'Markdown')
    if not message.chat.type == "private":
        await deletecommand(msg, message, 15)

@bot.message_handler(commands=['version'])
async def get_version(message):
    logger.info(f"User {message.from_user.id} Get Version")
    cont = f"Version: `{version_content} ({version_id})`"
    msg = await bot.reply_to(message, cont, parse_mode = 'Markdown')
    await deletecommand(msg, message, 10)

@bot.message_handler(commands=['stats'])
async def get_stats(message):
    logger.info(f"User {message.from_user.id} Get Stats")
    content = "你当前的权限状态是:\n\n管理权限: "
    if int(message.from_user.id) in admin_list:
        content = content + "✔"
    else:
        content = content + "❌"
    content = content + "\n超管权限: "
    if int(message.from_user.id) in su_admin_list:
        content = content + "✔"
    else:
        content = content + "❌"
    if int(message.from_user.id) in admin_list:
        sub = config.config['Subscribe']
        content = content + f"\n\n订阅数量: `{len(sub)}`"
    msg = await bot.reply_to(message, content, parse_mode = 'Markdown')
    await deletecommand(msg, message, 10)

def runserver():
    while True:
        try:
            web.run_app(app, port=web_port)
        except:
            pass

async def webserver():
    logger.info('Start WebServer')
    Thread(target=runserver).start()

async def pollBot():
    await reloadCommand()
    for send_id in su_admin_list :
        try :
            await bot.send_message(send_id, '`Bot` 启动啦 ~', parse_mode = 'Markdown')
        except :
            continue
    logger.info('Start Bot')
    await bot.infinity_polling()

async def main():
    while True:
        try:
            #tasks = [asyncio.create_task(pollBot()), asyncio.create_task(webserver())]
            #await asyncio.gather(*tasks)
            await pollBot()
        except:
            pass

#from telebot import asyncio_helper
#asyncio_helper.proxy = 'http://127.0.0.1:7890'

if __name__ == '__main__':
    asyncio.run(main())
