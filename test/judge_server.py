# coding: utf-8
# @Author: Xayanium

import asyncio
import nats
import functools


# Linux和macOS上可以使用uvloop提高事件循环执行效率
# import uvloop
# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def waiter(reader, writer, queue_push: asyncio.Queue, queue_pull: asyncio.Queue):
    print('one client connected')
    try:
        while True:
            data = await reader.read(1024)  # 不传参数, 读取直到流结束
            if not data:
                break
            elif data.decode('utf-8') == 'ready':
                judge_data = await queue_push.get()
                writer.write(judge_data)
                await writer.drain()
                # result_data = await reader.read()
                # 推送到nats消息队列中
                # await queue_pull.put(result_data)

    except ConnectionError:
        pass
    finally:
        writer.close()
        await writer.wait_closed()


async def run_server(ip, port, queue_push: asyncio.Queue, queue_pull: asyncio):
    # 预先填充回调函数的参数
    partial_waiter = functools.partial(waiter, queue_push=queue_push, queue_pull=queue_pull)
    # start_server会生成reader和writer参数, 传入回调函数waiter中
    server = await asyncio.start_server(partial_waiter, ip, port)
    async with server:
        await server.serve_forever()


# 使用nats作为后端和判题机间通信的消息队列
async def pull_task(queue_push: asyncio.Queue):
    # 连接NATS服务器
    nc = await nats.connect('nats://124.223.74.196:4222')
    # 创建JetStream上下文
    js = nc.jetstream()
    # 创建拉取式消费者并获取信息
    consumer = await js.pull_subscribe(subject='judge', stream='t_stream', durable='pro1')
    while True:
        msgs = await consumer.fetch(1, timeout=65535)  # 得到Msg对象列表(fetch(n)得到的列表中有n条消息对象)
        for msg in msgs:
            await queue_push.put(msg.data)
            await msg.ack()  # 对收到的消息要进行确认
            # print(msg.data.decode('utf-8'))  # 是一个Msg类的对象, 可以对其取值


async def push_task(queue_pull: asyncio.Queue):
    nc = await nats.connect('nats://124.223.74.196:4222')
    js = nc.jetstream()
    # 发布消息

    result_data = await queue_pull.get()
    await js.publish(subject='judge', payload=result_data, stream='result_json')


async def main():
    ip = '127.0.0.1'
    port = 8000
    # 创建协程中的消息队列, 用作判题机和判题服务器间的通信
    queue_push = asyncio.Queue(maxsize=500)  # 从nats中拉取任务, 放入协程消息队列中
    queue_pull = asyncio.Queue(maxsize=20)  # 从协程消息队列中拉取任务, 放入nats中
    # 使用 asyncio.gather 同时运行多个协程
    await asyncio.gather(
        run_server(ip, port, queue_push, queue_pull),
        pull_task(queue_push),
        # push_task(queue_pull)
    )


if __name__ == '__main__':
    asyncio.run(main())
# asyncio.run(main('localhost', 8080))
