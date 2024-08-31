import re
import yaml
import urllib
import aiohttp
import asyncio
from retry import retry
from aiohttp import web
from loguru import logger
from urllib import parse
from urllib.parse import unquote
from bot import Config

logger.add('Server.log')

config = Config()

web_port = config.LoadPort()
web_path = config.LoadPath()

def remove_convert(url: str):
    if "sub?target=" in url:
        pattern = r"url=([^&]*)"
        match = re.search(pattern, url)
        if match:
            encoded_url = match.group(1)
            decoded_url = unquote(encoded_url)
            url = decoded_url
        else:
            pass
    return url

def sub_convert(url: str, target: str, convert: dict):
    return convert['Backend'] + "sub?target=" + target + "&url=" + parse.quote_plus(remove_convert(url)) + "&config=" + convert['Config'] + convert['Parameter']

async def get_token(request):
    config.reload()
    token = request.match_info['token'].split('&')
    try:
        target = request.rel_url.query['flag'] 
    except:
        target = None
    if len(token) == 1:
        try :
            resp = config.FindToken(token[0])
            url = resp['url']
            subname = resp['subname']
        except:
            return web.Response(body=resp, content_type='text/plain')
    else:
        try :
            resp = config.FindToken(token[0])
            url = resp['url']
            subname = resp['subname']
        except:
            return web.Response(body=resp, content_type='text/plain')
        for arg in token[1:]:
            try :
                resp = config.FindToken(arg)
                url = url + '|' + resp['url']
                subname = subname + '&' + resp['subname']
                try:
                    if config.config['Subscribe'][resp['subname']]['Token'][arg]['Count'] != -1:
                        config.config['Subscribe'][resp['subname']]['Token'][arg]['Count'] = config.config['Subscribe'][resp['subname']]['Token'][arg]['Count'] - 1
                        config.Save()
                except:
                    pass
            except:
                return web.Response(body=resp, content_type='text/plain')
    try:
        convert = config.LoadConvert()
        if target == 'org':
            headers = {'User-Agent': request.headers['User-Agent']}
        elif target != None:
            if convert == None:
                headers = {'User-Agent': request.headers['User-Agent']}
            elif convert['Enable'] != 1:
                headers = {'User-Agent': request.headers['User-Agent']}
            else:
                headers = {'User-Agent': request.headers['User-Agent']}
                if target == "surge2":
                    target = 'surge&ver=2'
                elif target == "surge3":
                    target = 'surge&ver=3'
                elif target == "surge4":
                    target = 'surge&ver=4'
                url = sub_convert(url, target, convert)
        else:
            headers = {'User-Agent': request.headers['User-Agent']}
            if "clashr" in request.headers['User-Agent'].lower():
                target = 'clashr'
                url = sub_convert(url, target, convert)
            elif "clash" in request.headers['User-Agent'].lower():
                target = 'clash'
                url = sub_convert(url, target, convert)
            elif "surge2" in request.headers['User-Agent'].lower():
                target = 'surge&ver=2'
                url = sub_convert(url, target, convert)
            elif "surge3" in request.headers['User-Agent'].lower():
                target = 'surge&ver=3'
                url = sub_convert(url, target, convert)
            elif "surge4" in request.headers['User-Agent'].lower():
                target = 'surge&ver=4'
                url = sub_convert(url, target, convert)
            elif "surge" in request.headers['User-Agent'].lower():
                target = 'auto'
                url = sub_convert(url, target, convert)
            elif "quan" in request.headers['User-Agent'].lower() and "x" in request.headers['User-Agent'].lower():
                target = 'quanx'
                url = sub_convert(url, target, convert)
            elif "quan" in request.headers['User-Agent'].lower():
                target = 'quan'
                url = sub_convert(url, target, convert)
            elif "loon" in request.headers['User-Agent'].lower():
                target = 'quan'
                url = sub_convert(url, target, convert)
            elif "mellow" in request.headers['User-Agent'].lower():
                target = 'mellow'
                url = sub_convert(url, target, convert)
            elif "surfboard" in request.headers['User-Agent'].lower():
                target = 'surfboard'
                url = sub_convert(url, target, convert)
            elif "shadowsocksr" in request.headers['User-Agent'].lower():
                target = 'ssr'
                url = sub_convert(url, target, convert)
            elif "shadowsocksd" in request.headers['User-Agent'].lower():
                target = 'ssd'
                url = sub_convert(url, target, convert)
            elif "shadowsocks" in request.headers['User-Agent'].lower():
                target = 'ss'
                url = sub_convert(url, target, convert)
            elif "v2ray" in request.headers['User-Agent'].lower():
                target = 'v2ray'
                url = sub_convert(url, target, convert)
            elif "kitsunebi" in request.headers['User-Agent'].lower():
                target = 'v2ray'
                url = sub_convert(url, target, convert)
            elif "trojan" in request.headers['User-Agent'].lower():
                target = 'trojan'
                url = sub_convert(url, target, convert)
            elif "pharos" in request.headers['User-Agent'].lower():
                target = 'mixed'
                url = sub_convert(url, target, convert)
            elif "potatso" in request.headers['User-Agent'].lower():
                target = 'mixed'
                url = sub_convert(url, target, convert)
            elif "shadowrocket" in request.headers['User-Agent'].lower():
                target = 'mixed'
                url = sub_convert(url, target, convert)
            elif "shadowrocket" in request.headers['User-Agent'].lower():
                target = 'auto'
                url = sub_convert(url, target, convert)
            else:
                target = 'clash'
                url = sub_convert(url, target, convert)
    except:
        headers = {'User-Agent': 'ClashMetaForAndroid/2.8.9.Meta'}
    try:
        @retry(tries=5)
        async def get_sub_url(url, headers):
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=20) as res:
                    text = await res.text()
                    try:
                        sinfo = res.headers['subscription-userinfo']
                    except:
                        sinfo = None
                    try:
                        sinterval = res.headers['profile-update-interval']
                    except:
                        sinterval = None
            return text, sinfo, sinterval
        text, sinfo, sinterval = await get_sub_url(url, headers)
        if len(token) == 1:
            try:
                if config.config['Subscribe'][subname]['Token'][token[0]]['Count'] != -1:
                    config.config['Subscribe'][subname]['Token'][token[0]]['Count'] = config.config['Subscribe'][subname]['Token'][token[0]]['Count'] - 1
                    config.Save()
            except:
                pass
        respheaders = {'Content-Disposition': f'attachment; filename="{subname}"', 'Content-Type': 'application/*'}
        if sinfo != None:
            respheaders['subscription-userinfo'] = sinfo
        if sinterval != None:
            respheaders['profile-update-interval'] = sinterval
        if target == 'surfboard' or 'surge' in target:
            fline = text.split('\n')[0]
            ftext = "#!MANAGED-CONFIG " + str(request.url)
            try:
                for arg in fline.split()[2:]:
                    ftext = ftext + ' ' + arg
            except:
                pass
            text = text.replace(fline, ftext)
        return web.Response(body=text, headers=respheaders)
    except:
        return web.Response(body="")

app = web.Application()
app.router.add_get(web_path + '{token}', get_token)

if __name__ == '__main__':
    web.run_app(app, port=web_port)
