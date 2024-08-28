# coding: utf-8
# @Author: Xayanium

import asyncio
import json
import socket
import time


# 使用上下文管理器
class Client(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.loop = asyncio.get_running_loop()

    async def recv(self):
        data = await self.loop.sock_recv(self.sock, 1024)
        return data

    async def send(self, data):
        await self.loop.sock_sendall(self.sock, data.encode('utf-8'))

    async def __aenter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 同步连接服务端
        # self.sock.connect((self.ip, self.port))

        # 异步连接服务端
        # 参数: 1. socket对象 , 2. ip+port
        await self.loop.sock_connect(self.sock, (self.ip, self.port))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()


async def main():
    async with Client('127.0.0.1', 8000) as client:
        while True:
            await client.send('ready')
            data = await client.recv()
            await asyncio.sleep(0.1)
            ed_time = time.time()
            if data:
                data_dict = json.loads(data.decode('utf-8'))
                st_time = data_dict['st_time']
                print(f'st_time: {st_time}, ed_time: {ed_time}, task use time: {ed_time - st_time}')
            else:
                print('no data')
            # print(data.decode('utf-8'))
            # await asyncio.sleep(4)


asyncio.run(main())
