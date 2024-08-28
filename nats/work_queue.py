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

    await js.add_stream(name='demo-stream', subjects=['foo', 'judge'])
    print('created the stream')

    # 发布消息
    for i in range(0, 10):
        ack = await js.publish('foo', f'hello world: {i}'.encode('utf-8'))
        # print(ack)
    print('published 10 messages')

    # 订阅消息
    """
    ConsumerConfig类:
    durable_name (str): 消费者的持久名称, 如果设置了这个属性，消费者将是持久的
    filter_subject (str): 消费者只会接收匹配这个主题的消息
    ack_policy (str): 可以是explicit(每条消息都必须明确确认), all(只确认最后一条), none(不确认)
    max_deliver (int): 最大投递次数, 如果消息未被确认, 消费者将重新投递消息, 直到达到这个次数
    replay_policy (str): 重放策略, 可以是instant(立即重放), original(按照原始时间顺序重放)
    max_ack_pending (int): 最大未确认消息数
    """

    # 创建拉取式消费者并获取信息
    consumer = await js.pull_subscribe('foo', 'psub')
    for i in range(0, 12):
        msgs = await consumer.fetch(1)  # 得到Msg对象列表(fetch(n)得到的列表中有n条消息对象)
        for msg in msgs:
            print(msg.data.decode('utf-8'))  # 是一个Msg类的对象, 可以对其取值

    """
    js.subscribe()参数:
    subject (str): 要订阅的主题名称
    queue (str): 队列组名称, 队列组中每条消息只会被队列组中的一个订阅者接收和处理
    cb (callable): 回调函数, 回调函数接受消息对象
    durable (str): 持久订阅者名称, 客户端断开连接后仍然存在, 在重新连接时继续接收消息
    config (dict): 消费者配置选项
    manual_acks (bool): 是否手动确认消息, 设置为 True，则需要显式调用 msg.ack() 来确认消息
    ordered_consumer (bool): 是否创建有序消费者, 有序消费者确保消息按顺序处理, 并在发生故障时自动恢复
    """

    # 创建单个临时推送式订阅者
    sub = await js.subscribe('foo')
    for i in range(0, 11):
        msg = await sub.next_msg()
        print(msg.data.decode('utf-8'))
        await msg.ack()

    # 创建持久推送式订阅者
    sub = await js.subscribe('foo', durable='myapp')
    msg = await sub.next_msg()
    print(msg.data.decode('utf-8'))
    await msg.ack()

    # 创建负载均衡式订阅者(queue)
    async def qa_handler(msg):
        print(f'A received message: {msg.data.decode("utf-8")}')
        await msg.ack()

    async def qb_handler(msg):
        print(f'B received message: {msg.data.decode("utf-8")}')
        await msg.ack()

    # 发布消息, 查看队列组接受情况
    for i in range(5):
        await js.publish('judge', f'message {i}'.encode('utf-8'))
    # 创建两个同属于一个队列组的订阅者
    await js.subscribe('judge', queue='workers', cb=qa_handler)
    await js.subscribe('judge', queue='workers', cb=qb_handler)

    # 销毁
    await js.delete_stream('demo-stream')
    await js.delete_stream('events')
    await nc.close()


if __name__ == '__main__':
    asyncio.run(main())




