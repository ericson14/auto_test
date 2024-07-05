import asyncio

import pandas as pd
from aiohttp import ClientSession


res = {}


async def http(domain, session):
    """
    http请求处理器
    """
    async with session.request("GET", domain) as response:
        s = response.headers.get("Content-Type")
        if s == "binary/octet-stream":
            return True
        else:
            print(s)
            return False


async def one(url, session):
    urls = url.split("/")
    high_file = urls[-1]
    url_p = "/".join(urls[:-1])
    hs = high_file.split(".")
    if len(hs) == 2:
        high_file_name, high_file_prefix = hs
    else:
        high_file_name = ".".join(hs[:-1])
        high_file_prefix = hs[-1]
    low_file = high_file_name + "_low" + "." + high_file_prefix
    low_url = url_p + "/" + low_file
    r = await http(low_url, session)
    if r:
        res[url] = low_url
    else:
        res[url] = ""


async def fill_url(sema, loop):
    df = pd.read_csv("E:\\小渲风glb表.csv")
    urls = df["glb_url"]
    async with ClientSession(loop=loop) as session:
        async with sema:
            for url in urls:
                await one(url, session)


def main():
    loop = asyncio.get_event_loop()
    semaphore = asyncio.Semaphore(5)
    task = loop.create_task(fill_url(semaphore, loop))
    try:
        loop.run_until_complete(task)
    finally:
        loop.close()
    db = pd.read_csv("E:\\小渲风glb表.csv")
    print(res)
    db["low_glb_url"] = db["glb_url"].apply(lambda x: res[x])
    db.to_csv("E:\\小渲风glb填充表.csv")


def data_to_sql():
    df = pd.read_csv("E:\\小渲风glb填充表.csv")
    update_dict = dict(zip(df["id"], df["low_glb_url"]))
    sql = "UPDATE render_model SET low_glb_url= CASE id "
    update_id_list = []
    for k, v in update_dict.items():
        if pd.isnull(v):
            continue
        sql += f"WHEN {k} THEN %s "
        update_id_list.append(k)
    sql += "END WHERE id IN %s;"
    args = [update_dict.get(k) for k in update_dict]
    args.append(update_id_list)


if __name__ == '__main__':
    data_to_sql()
