# coding: utf-8
# @Author: Xayanium

import asyncio
import json
import nats
from nats.js import errors


async def main():
    nc = await nats.connect('nats://124.223.74.196:4222')
    js = nc.jetstream()
    consumer = await js.pull_subscribe(subject='judge', stream='t_stream', durable='pro1')

    while True:
        msgs = await consumer.fetch(1, timeout=65535)
        for msg in msgs:
            msg_dict = json.loads(msg.data)
            await msg.ack()


if __name__ == '__main__':
    asyncio.run(main())
