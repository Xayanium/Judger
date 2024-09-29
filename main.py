# -*- coding: utf-8 -*-
# @Time    : 2024/8/29 12:59
# @Author  : Xayanium

import asyncio
import json
import os.path
import subprocess
from concurrent.futures import ProcessPoolExecutor
import nats
from nats.errors import *
import uvloop
from minio import Minio
from minio.error import InvalidResponseError
import aiofiles


# 将判题相关变量及方法进行封装
class Judge:
    def __init__(self, judge_json: dict):
        self.lan = judge_json['language']
        self.p_name = judge_json['problem_id']
        self.judge_id = judge_json['judge_id']
        self.ti_lim = judge_json['time_limit']
        self.mem_lim = judge_json['memory_limit']
        self.is_spj = judge_json['is_spj']
        self.path = os.path.dirname(os.path.abspath(__file__))  # 当前文件所在目录
        self.tmp_path = os.path.join(self.path, 'tmp')  # 临时文件夹, 用于存放判题过程中产生的数据
        self.exec_path = os.path.join(self.tmp_path, f'{self.p_name}')
        self.data_path = os.path.join(self.path, 'problem', f'{self.p_name}')
        self.judge_path = os.path.join(self.path, 'output', 'judge')  # 判题核心可执行文件的路径
        self.proc_argv = []  # 将判题json加入列表中, 方便进程池调用
        self.result_json = {  # 判题结果json数据, 传回给后端(按照后端给定的json命名)
            'judge_id': self.judge_id,
            'case_id': 0,
            'time_cost': 0,
            'memory_cost': 0,
            'result': '',
            'message': '',
            'input_data': '',
            'sample_output': '',
            'user_output': ''
        }
        with open(os.path.join(self.tmp_path, f'{self.p_name}.{self.lan}'), 'wt') as file:
            file.write(judge_json['code'])

    def compile_code(self):
        # 新增语言时在此处增加需编译的语言的编译参数
        if self.lan == 'c':
            proc_args = (f'gcc {os.path.join(self.tmp_path, f"{self.p_name}.c")} -o '
                         f'{os.path.join(self.tmp_path, f"{self.p_name}")} -O2 -Wall')
        elif self.lan == 'cpp':
            proc_args = (f'g++ {os.path.join(self.tmp_path, f"{self.p_name}.c")} -o '
                         f'{os.path.join(self.tmp_path, f"{self.p_name}")} -O2 -Wall')
        elif self.lan == 'java':
            proc_args = f'javac {os.path.join(self.tmp_path, "Main.java")} -d {self.tmp_path}'
        elif self.lan == 'go':
            proc_args = f'go build {os.path.join(self.tmp_path, self.p_name)}.go'
        else:
            return True
        # 创建子进程执行编译
        proc = subprocess.Popen(proc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        if not err:
            print('compile successful')
            return True
        else:
            if err.decode('utf-8').find('error') != -1:
                print('compile error: ', err.decode('utf-8'))
                return err.decode('utf-8')
            else:
                print('compile successful')
                return True

    def parse_judge_json(self):
        # 判题数据文件在判题机中存放路径为: {data_path}/{p_name}_{t_case}.in(out)
        # 将 problem/{p_name} 文件夹进行遍历,
        for file in os.listdir(self.data_path):
            if file.split('.')[1] == 'out':  # 遍历到.out文件不进行处理, 用.in文件拼接出.out文件路径
                continue
            file_name = file.split('.')[0]  # 去除标准输入文件后缀得到文件名, 拼接得到标准输出文件地址
            t_case = int(file_name.split('_')[1])  # 得到当前测试用例号

            in_path = os.path.join(self.data_path, file)
            ans_path = os.path.join(self.data_path, f'{file_name}.out')
            out_path = os.path.join(self.tmp_path, f'{self.p_name}_{t_case}.txt')
            err_path = os.path.join(self.tmp_path, f'{self.p_name}er_{t_case}.txt')

            judge_json = {
                'pid': t_case, 'ti_lim': self.ti_lim, 'mem_lim': self.mem_lim,
                'exec_path': self.exec_path, 'in_path': in_path, 'out_path': out_path,
                'err_path': err_path, 'ans_path': ans_path, 'is_spj': self.is_spj
            }
            proc_json = [self.judge_path, json.dumps(judge_json)]  # 得到当前测试用例的判题json
            self.proc_argv.append(proc_json)


# 使用上下文管理器, 封装客户端的打开和关闭等操作
class Client(object):
    def __init__(self, conf: dict):
        self.nats_server = conf['nats_server']
        self.subject = conf['subject']
        self.stream = conf['stream']
        self.durable = conf['durable']
        self.endpoint = conf['endpoint']  # Minio server地址
        self.access_key = conf['access_key']
        self.secret_key = conf['secret_key']
        self.bucket_name = conf['bucket_name']

    async def __aenter__(self):
        # 异步连接NATS服务端
        self.nc = await nats.connect(servers=self.nats_server)
        self.js = self.nc.jetstream()
        self.consumer = await self.js.pull_subscribe(subject=self.subject, stream=self.stream, durable=self.durable)
        # 异步连接Minio
        self.bucket = Minio(
            self.endpoint,
            self.access_key,
            self.secret_key,
            secure=False
        )
        return self  # 必须return self 才能拿到上下文管理器返回的对象

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 异步关闭客户端连接
        await self.nc.close()


# 启动判题子进程
def run_judge_core(proc_args: list):
    proc = subprocess.Popen(proc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return out.decode('utf-8'), err.decode('utf-8')


# 创建进程池, 启动判题进程
async def run_judge(proc_argv: list):
    loop = asyncio.get_running_loop()  # 通过run_in_executor方法桥接同步的进程池和异步的协程函数
    with ProcessPoolExecutor() as executor:
        futures = [loop.run_in_executor(executor, run_judge_core, proc_args) for proc_args in proc_argv]
        # 监控并发任务的完成情况
        for future in futures:
            # 每完成一个任务, 就返回结果(使用python中的生成器, 从而不中断函数执行)
            result = await asyncio.wrap_future(future)  # 将 concurrent.futures.Future 包装成 asyncio.Future
            yield result  # 返回一个元组, 值为subprocess中的(stdout, stderr)的字符串形式
            # yield future.result()
            # out, err = future.result()
            # print(out, err)
    print('finish process')


# 从Minio中下载判题数据到本地
# 得到所有需要下载的数据(key-value对象), 通过线程池下载
async def download_judge_data(client: Client, prefix, file_path):
    try:
        loop = asyncio.get_event_loop()
        objects = client.bucket.list_objects(client.bucket_name, prefix=prefix, recursive=True)
        # run_in_executor默认使用线程池
        futures = [loop.run_in_executor(
            None,
            client.bucket.fget_object,
            client.bucket_name,
            obj.object_name,
            # 后端上传至minio中的文件的key是: {p_id}/xxx/{file_name}, 拉取到判题机内后存放路径为{data_path}/{file_name}
            os.path.join(file_path, f"{obj.object_name.split('/')[2]}")
        ) for obj in objects]
        await asyncio.gather(*futures)
    except InvalidResponseError:
        print('download file error')


async def return_judge_data(judge: Judge, in_path, sample_out_path, user_out_path, lim_count):
    async with aiofiles.open(in_path, 'r', encoding='utf-8') as file:
        line_count = 0
        async for line in file:
            judge.result_json['input_data'] += line
            line_count += 1
            if line_count >= lim_count:
                break
    async with aiofiles.open(sample_out_path, 'r', encoding='utf-8') as file:
        line_count = 0
        async for line in file:
            judge.result_json['sample_output'] += line
            line_count += 1
            if line_count >= lim_count:
                break
    async with aiofiles.open(user_out_path, 'r', encoding='utf-8') as file:
        line_count = 0
        async for line in file:
            judge.result_json['user_output'] += line
            line_count += 1
            if line_count >= lim_count:
                break


async def run_client(conf: dict):
    # 使用上下文管理器, 创建客户端连接对象
    async with Client(conf) as client:
        # 客户端进入连接循环, 和服务端进行通信
        while True:
            try:
                # 从nats中取消息, 得到一个列表, 列表中只有一个判题消息
                msgs = await client.consumer.fetch(1, timeout=90*24*3600)
                for msg in msgs:
                    await msg.ack()  # 向NATS服务端确认收到消息
                    """
                    后端传递的数据包括: 判题id, 题目id, 用户代码及所用语言, 判题机的时空限制, 是否为特判
                    judge_json = {
                        'judge_id': (int),
                        'problem_id': (int),
                        'problem_code': (string),
                        'language': (string),
                        'code': (string),
                        'time_limit': (int),
                        'memory_limit': (int)
                    }
                    """
                    judge_json = json.loads(msg.data.decode('utf-8'))
                    judge = Judge(judge_json)

                    # 从Minio中拉取判题文件(由于Minio和判题机部署在一台服务器, 所以可以忽略每次拉取的网络延迟)
                    await download_judge_data(client, judge.p_name,judge.data_path)

                    compile_info = judge.compile_code()
                    if compile_info is not True:
                        # 编译出错直接返回判题结果, 结束此次判题
                        judge.result_json['result'] = 'COMPILE_ERROR'
                        judge.result_json['message'] = compile_info
                        # 将判题结果推送至指定位置(NATS中主题名为当前进行判题用户的uid)
                        await client.nc.publish(judge.judge_id, json.dumps(judge.result_json).encode('utf-8'))
                        break

                    judge.parse_judge_json()

                    """
                        判题结果json数据, 传回给后端
                        result_json = {
                            'judge_id': self.judge_id,
                            'case_id': 0,
                            'time_cost': 0,
                            'memory_cost': 0,
                            'result': '',
                            'message': '',
                            'input_data': '',
                            'sample_output': '',
                            'user_output': ''
                        }
                    """
                    flag = False
                    async for out, err in run_judge(judge.proc_argv):  # 从yield生成器中取结果
                        if err:
                            judge.result_json['result'] = 'UNKNOWN_ERROR'
                            judge.result_json['message'] = err
                        else:
                            out = json.loads(out)
                            judge.result_json['case_id'] = out['test_case']
                            judge.result_json['time_cost'] = out['ti_use']
                            judge.result_json['memory_cost'] = out['mem_use']
                            judge.result_json['result'] = out['result']

                        # 对于第一个结果错误的测试用例, 返回部分评测数据, 以及用户输出
                        if flag is False and out['result'] != 'ACCEPT':
                            flag = True
                            case_id = out["test_case"]
                            await return_judge_data(
                                judge,
                                os.path.join(judge.data_path, f'{judge.p_name}_{case_id}.in'),
                                os.path.join(judge.data_path, f'{judge.p_name}_{case_id}.out'),
                                os.path.join(judge.tmp_path, f'{judge.p_name}_{case_id}.txt'),
                                lim_count=50
                            )

                        await client.nc.publish(judge_json['judge_id'], json.dumps(judge.result_json).encode('utf-8'))

                    # 判完题后清理判题数据
                    

            except TimeoutError:
                continue

if __name__ == '__main__':
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_settings.json')
    with open(conf_path, mode='rt', encoding='utf-8') as f:
        config = json.load(f)
    asyncio.run(run_client(config))

