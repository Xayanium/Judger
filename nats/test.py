# coding: utf-8
# @Author: Xayanium

import os
import json
import asyncio
import nats


async def main():
    # 连接NATS服务器
    nc = await nats.connect('nats://122.152.236.4:4222')

    # 创建JetStream上下文
    js = nc.jetstream()

    # 创建 Work-queue Stream
    # 使用nats.js的StreamConfig类
    """
    name (str): 流的名称, 唯一标识流
    subjects (List[str]): 流所订阅的主题列表, 定义流将接收哪些主题的消息
    retention (str): 消息保留策略, 可选limits, interest, workqueue
    max_consumers (int): 流允许的最大消费者数量
    max_msgs: 流中允许的最大消息数量
    max_bytes (int): 流中允许的最大存储字节数
    max_age (int): 消息在流中的最大保留时间（以纳秒为单位）
    max_msg_size (int): 单条消息的最大字节数
    storage (str): 消息存储类型, 可选file(硬盘), memory(内存)
    discard (str): 消息丢弃策略, 可选old, new, 决定在达到限制时丢弃旧消息还是新消息
    num_replicas (int): 消息的复制副本数量
    no_ack (bool): 是否禁用消息确认
    template_owner (str): 流模板的所有者
    duplicate_window (int): 重复消息检测窗口(以纳秒为单位)
    placement (dict): 指定流在集群中的放置位置
    mirror (dict): 从另一个流中镜像消息
    sources (List[dict]): 从其他流中获取消息
    """

    # await js.add_stream(name='sa-stream', subjects=['core'], retention='workqueue')
    # stream_info = await js.stream_info('sa-stream')
    # print(stream_info)
    # print('created the stream')

    # try:
    #     stream_info = await js.stream_info('sa-stream')
    #     print(stream_info)
    # except Exception as e:
    #     print('stream not exists')
    #     await js.add_stream(name='sa-stream', subjects=['core'], retention='workqueue')

    for i in range(0, 10):
        await js.publish('core', f'hello world: {i}'.encode('utf-8'))

    consumer = await js.pull_subscribe(subject='core', stream='sb-stream', durable='processor1')
    for i in range(0, 10):
        try:
            msgs = await consumer.fetch(1, timeout=10)
            for msg in msgs:
                print(msg.data.decode('utf-8'))
        except Exception as e:
            print('time out')

    # 销毁
    # await js.delete_stream('sa-stream')
    await nc.close()


if __name__ == '__main__':
    asyncio.run(main())




