# coding: utf-8
# @Author: Xayanium

import asyncio
import socket
import uvloop
import time
import json


async def deal_client(conn, loop):
    status = False  # 判题机是否处于ok状态
    conn_time = time.time()  # 判题机连接后, 等待其进入ok状态, 超过5s发送销毁重连命令
    judge_json = {}
    while True:
        data = await loop.sock_recv(1024)
        # 如果消息队列中有消息, 且有空闲判题机, 则从消息队列中拉取相应的判题申请
        # 发送判题json给判题机
        if data.decode('utf-8') == 'ready':
            await loop.sock_sendall(conn, judge_json)
        # if status is True:
        #     status = False
        # else:
        #     await loop.sock_sendall(conn, 'get_status')
        #     data = await loop.sock_recv(1024)
        #     data = data.decode('utf-8')
        #     if not data:
        #         # linux下收空表明客户端异常断开
        #         break
        #
        #     if data == 'ok':
        #         status = True
            # else:
            #     if time.time() - conn_time > 5:
            #         await loop.sock_sendall(conn, 'time_out'.encode('utf-8'))
            #         break

    conn.close()


async def run_server(ip, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((ip, port))
    server.listen(20)
    server.setblocking(False)  # 异步要设置为非阻塞

    # 使用异步的accept方法
    loop = asyncio.get_running_loop()

    # 循环接受客户端的连接请求
    while True:
        conn, addr = await loop.sock_accept(server)
        # 每来一个客户端conn连接, 就创建一个task任务, 只接客, 交给事件循环服务, 实现协程
        await loop.create_task(deal_client(conn, addr))


if __name__ == '__main__':
    with open('./setting_server.json', mode='rt', encoding='utf-8') as f:
        server_json = json.load(f)

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # 使用uvloop(需下载)提高事件循环效率
    asyncio.run(run_server(server_json['ip'], server_json['port']))
