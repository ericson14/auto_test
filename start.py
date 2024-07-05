import asyncio
import os
import re
from typing import Dict

import aiofiles
import ujson
import yaml
from aiohttp import ClientSession, CookieJar


class BXMDict(Dict):
    def __init__(self, *args, **kwargs):
        super(BXMDict, self).__init__(*args, **kwargs)
        self._token = ""
        self._url = {
            "local": "192.168.60.72",
            "dev": "https://test.eggrj.com/render_v2",
            "prod": "http://ggtools.thinkerx.com/render_v2"
        }
        self._semaphore = 1

    def __getattr__(self, key):
        value = self[key]
        if isinstance(value, dict):
            value = BXMDict(value)
        return value

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    @property
    def url(self):
        return self._url

    @property
    def semaphore(self):
        return self._semaphore


async def advertise_cms_login(bxmat, session):
    data = {
        "phone": "13340682230"
    }
    async with session.request("POST", url=bxmat.url.get("dev")+"/login", json=data) as response:
        res = await response.json(loads=ujson.loads)
        token = res.get("data").get("token")
        bxmat.token = token


def my_iter(data):
    """
    递归测试用例，根据不同数据类型做相应处理，将模板语法转化为正常值
    """
    # 匹配函数调用形式的语法
    pattern_function = re.compile(r'^\${([A-Za-z_]+\w*\(.*\))}$')
    pattern_function2 = re.compile(r'^\${(.*)}$')
    # 匹配取默认值的语法
    pattern_function3 = re.compile(r'^\$\((.*)\)$')

    if isinstance(data, (list, tuple)):
        for index, _data in enumerate(data):
            data[index] = my_iter(_data) or _data
    elif isinstance(data, dict):
        for k, v in data.items():
            data[k] = my_iter(v) or v
    elif isinstance(data, (str, bytes)):
        m = pattern_function.match(data)
        if not m:
            m = pattern_function2.match(data)
        if m:
            return eval(m.group(1))
        if not m:
            m = pattern_function3.match(data)
        # if m:
        #     key, value = m.group(1).split(':')
        #     return bxmat.default_values.get(key).get(value)

        return data


async def yaml_load(file_dir=None, file=None):
    """异步读取YAML文件"""
    if file_dir:
        file = os.path.join(file_dir, file)
    async with aiofiles.open(file, "r", encoding="utf-8", errors="ignore") as f:
        data = await f.read()
    data = yaml.load(data, Loader=yaml.Loader)
    my_iter(data)

    return BXMDict(data)


async def http(bxmat, session, domain, *args, **kwargs):
    """
    http请求处理器
    """
    method, api = args
    arguments = kwargs.get('data') or kwargs.get('params') or kwargs.get('json') or {}

    # kwargs中加入token
    kwargs.setdefault('headers', {}).update({'token': bxmat.token})
    # 拼接服务地址和api
    url = ''.join([domain, api])

    async with session.request(method, url, **kwargs) as response:
        res = await response.json(loads=ujson.loads)
        return {
            'response': res,
            'url': url,
            'arguments': arguments
        }


async def entrance(bxmat, cases, loop, server, semaphore=None):
    """
    http执行入口
    """
    # 在CookieJar的update_cookies方法中，如果unsafe=False并且访问的是IP地址，客户端是不会更新cookie信息
    # 这就导致session不能正确处理登录态的问题
    # 所以这里使用的cookie_jar参数使用手动生成的CookieJar对象，并将其unsafe设置为True
    async with ClientSession(
            loop=loop, cookie_jar=CookieJar(unsafe=True), headers={'token': bxmat.token}
            ) as session:
        await advertise_cms_login(bxmat, session)
        if semaphore:
            async with semaphore:
                for test_case in cases:
                    data = await one(bxmat, session, server, case_name=test_case)
                    bxmat.setdefault(data.pop('case_dir'), []).append(data)
        else:
            for test_case in cases:
                data = await one(bxmat, session, server, case_name=test_case)
                bxmat.setdefault(data.pop('case_dir'), []).append(data)

        return bxmat


async def one(bxmat, session, server, case_dir='./', case_name=''):
    """
    一份测试用例执行的全过程，包括读取.yml测试用例，执行http请求，返回请求结果
    所有操作都是异步非阻塞的
    :param session: session会话
    :param case_dir: 用例目录
    :param case_name: 用例名称
    :return:
    """
    domain = bxmat.url.get(server)
    test_data = await yaml_load(file_dir=case_dir, file=case_name)
    result = BXMDict(
        {
            'case_dir': os.path.dirname(case_name),
            'api': test_data.args[1].replace('/', '_'),
        }
    )
    if isinstance(test_data.kwargs, list):
        for index, each_data in enumerate(test_data.kwargs):
            step_name = each_data.pop('case_name')
            r = await http(bxmat, session, domain, *test_data.args, **each_data)
            r.update({'case_name': step_name})
            result.setdefault('responses', []).append(
                {
                    'response': r,
                    'validator': test_data.validator[index]
                }
            )
    else:
        step_name = test_data.kwargs.pop('caseName')
        r = await http(session, domain, *test_data.args, **test_data.kwargs)
        r.update({'case_name': step_name})
        result.setdefault('responses', []).append(
            {
                'response': r,
                'validator': test_data.validator
            }
        )

    return result


def main(cases, server):
    """
    事件循环主函数，负责所有接口请求的执行
    :param cases:
    :param server
    :return:
    """
    bxmat = BXMDict()
    loop = asyncio.get_event_loop()
    semaphore = asyncio.Semaphore(bxmat.semaphore)
    # 需要处理的任务
    task = loop.create_task(entrance(bxmat, cases, loop, server, semaphore))
    # 将协程注册到事件循环，并启动事件循环
    try:
        # loop.run_until_complete(asyncio.gather(*tasks))
        loop.run_until_complete(task)
    finally:
        loop.close()

    return task.result()


if __name__ == '__main__':
    print(main(["E:\\Working\\auto_test_frame\\model_classification\\test_render_model.yaml"], "dev"))
