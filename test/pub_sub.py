import os
import nats
import asyncio
from nats.errors import TimeoutError
import uvloop

# 获取到对应的nats服务列表
servers = os.environ.get('NATS_URL', 'nats://localhost:4222').split(',')
print(servers)


async def main():
    # 连接到nats服务, 得到一个客户端对象
    nc = await nats.connect(servers=servers)

    # 发布消息 nc.publish()  订阅 nc.subscribe()
    # 在订阅之前发布消息，这些消息将不会被接收到 (适用于不关心历史消息，只关心订阅之后的新消息)
    # 在订阅之后发布消息，所有活跃的订阅者都会接收到这些消息 (适用于你希望确保所有消息都被订阅者接收到的场景)

    # 场景一: 在订阅之前发消息:
    await nc.publish('great.yzy', b'hello')

    sub = await nc.subscribe('great.*')

    try:
        msg = await sub.next_msg(timeout=0.5)
        print(f'{msg.data} on subject: {msg.subject}')
    except TimeoutError:
        print('after 1 seconds waiting , no msg from publisher')

    # 场景二: 在订阅之后发消息:
    await nc.publish('great.yhr', b'hello')
    await nc.publish('great.yxj', b'hello')

    try:
        msg = await sub.next_msg(timeout=1)
        print(f'{msg.data} on subject: {msg.subject}')
    except TimeoutError:
        print('after 1 seconds waiting , no msg from publisher')

    try:
        msg = await sub.next_msg(timeout=1)
        print(f'{msg.data} on subject: {msg.subject}')
    except TimeoutError:
        print('after 1 seconds waiting , no msg from publisher')

    # 取消订阅(不再接收任何新的消息, 如果有未处理的消息，这些消息将被丢弃)
    # await sub.unsubscribe()
    # 优雅地关闭订阅(处理所有已接收但未处理的消息，然后再关闭订阅或连接)
    await sub.drain()

    # 关闭连接
    await nc.drain()
    await nc.close()


if __name__ == '__main__':
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())

