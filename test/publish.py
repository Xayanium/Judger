# coding: utf-8
# @Author: Xayanium
import json
import time
import asyncio
import nats


async def main():
    nc = await nats.connect('nats://124.223.74.196:4222')
    js = nc.jetstream()
    # 发布消息
    for i in range(0, 500):
        now_time = time.time()
        msg = {
            'st_time': now_time,
            'info': 'haha'
        }
        msg = json.dumps(msg)
        ack = await js.publish(subject='judge', stream='t_stream', payload=msg.encode('utf-8'))
        # print(msg)

        # print(ack)
    # print('published 10 messages')


if __name__ == '__main__':
    asyncio.run(main())
