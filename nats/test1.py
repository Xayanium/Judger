import asyncio
from nats.aio.client import Client as NATS
from nats.errors import TimeoutError
from nats.js.api import ConsumerConfig


async def main():
    # 连接到 NATS 服务器
    nc = NATS()
    await nc.connect("nats://localhost:4222")

    # 启用 JetStream
    js = nc.jetstream()

    # 创建或获取一个 Stream
    await js.add_stream(name="mystream", subjects=["my.subject"])

    # 创建消费者配置
    consumer_config = ConsumerConfig(
        durable_name="consumer1",  # 每个消费者应该有唯一的 durable_name
        ack_policy="explicit",  # 明确确认消息已处理
        deliver_subject="",
        max_deliver=10,
        ack_wait=30,  # 消费者在超时之前等待确认
        max_ack_pending=20,
    )

    # 创建多个消费者
    for i in range(3):
        consumer_name = f"consumer-{i + 1}"
        await js.add_consumer(stream="mystream", config=consumer_config._replace(durable_name=consumer_name))

    async def pull_messages(consumer_name):
        while True:
            try:
                # 从消费者中拉取消息
                msgs = await js.pull_subscribe("my.subject", durable=consumer_name)
                for msg in msgs:
                    print(f"Consumer {consumer_name} received message: {msg.data.decode()}")
                    await msg.ack()
            except TimeoutError:
                print(f"Consumer {consumer_name} timed out waiting for messages")

    # 启动多个消费者的协程
    consumers = [asyncio.create_task(pull_messages(f"consumer-{i + 1}")) for i in range(3)]

    # 等待所有消费者处理完
    await asyncio.gather(*consumers)


if __name__ == "__main__":
    asyncio.run(main())
