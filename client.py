# coding: utf-8
# @Author: Xayanium

import asyncio
import json
import os.path
import socket
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed


# 将判题相关变量及方法进行封装
class Judge:
    def __init__(self, judge_json: dict):
        self.lan = judge_json['lan']
        self.p_name = judge_json['id']
        self.ti_lim = judge_json['ti_lim']
        self.mem_lim = judge_json['mem_lim']
        self.is_spj = judge_json['is_spj']
        self.path = os.path.dirname(os.path.abspath(__file__))  # 当前文件所在目录
        self.exec_path = f'{self.path}/tmp/{self.p_name}'
        self.data_path = f'{self.path}/problem/{self.p_name}'
        self.judge_path = f'{self.path}/output/judge'  # 判题核心可执行文件的路径
        self.proc_argv = []  # 将判题json加入列表中, 方便进程池调用

    def compile_code(self):
        if self.lan == 'c':
            proc_args = f'gcc ./tmp/{self.p_name}.c -o ./tmp/{self.p_name} -O2 -Wall'
        elif self.lan == 'cpp':
            proc_args = f'g++ ./tmp/{self.p_name}.cpp -o ./tmp/{self.p_name} -O2 -Wall'
        elif self.lan == 'java':
            proc_args = f'javac ./tmp/Main.java -d ./tmp'
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
                print('compile error')
                print(err.decode('utf-8'))
                return err.decode('utf-8')
            else:
                print('compile successful')
                return True

    def get_judge_json(self):
        # 将 problem/{p_name}/in 文件夹进行遍历, 得到每一个标准输入文件地址
        # 根据我们的规定, 输入(输出)文件格式为: {p_name}_{t_case}.in(out)
        for file in os.listdir(self.path + '/in'):
            file_name = file.split('.')[0]  # 去除标准输入文件后缀得到文件名, 拼接得到对应的答案输出文件地址
            t_case = file_name.split('_')[1]  # 得到当前测试用例号(此时为str)
            in_path = os.path.join(self.data_path + '/in', file)
            ans_path = os.path.join(self.data_path + '/out', file_name + '.out')
            out_path = f'{self.path}/tmp/{self.p_name}_{t_case}.txt'
            err_path = f'{self.path}/tmp/{self.p_name}er_{t_case}.txt'
            t_case = int(t_case)  # 转换为数字的测试用例号
            judge_json = {
                'id': t_case, 'ti_lim': self.ti_lim, 'mem_lim': self.mem_lim,
                'exec_path': self.exec_path, 'in_path': in_path, 'out_path': out_path,
                'err_path': err_path, 'ans_path': ans_path, 'is_spj': self.is_spj
            }
            proc_json = [self.judge_path, json.dumps(judge_json)]  # 得到当前测试用例的判题json
            self.proc_argv.append(proc_json)


# 使用上下文管理器, 封装客户端的打开和关闭等操作
class Client(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.loop = asyncio.get_running_loop()

    async def recv(self):
        # 异步接受数据
        data = await self.loop.sock_recv(self.sock, 1024)
        return data

    async def send(self, data):
        # 异步发送数据(发送内容要进行编码)
        await self.loop.sock_sendall(self.sock, data.encode('utf-8'))

    async def __aenter__(self):
        # 异步连接服务端
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        await self.loop.sock_connect(self.sock, (self.ip, self.port))
        return self  # 必须return self 才能拿到上下文管理器返回的对象

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 异步关闭客户端连接
        self.sock.close()


# 启动判题子进程
def judge_code(proc_args):
    proc = subprocess.Popen(proc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return out.decode('utf-8'), err.decode('utf-8')


# 创建进程池, 启动判题进程
def run_judge(proc_argv: list):
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(judge_code, proc_args) for proc_args in proc_argv]
        for future in as_completed(futures):
            # 每完成一个任务, 就返回结果(使用python中的生成器不中断函数执行)
            yield future.result()  # 返回一个元组, 值为subprocess中的(stdout, stderr)的字符串形式
            # out, err = future.result()
            # print(out, err)
    print('finish process')


async def run_client(ip, port):
    # 使用上下文管理器, 创建客户端连接对象
    async with Client(ip, port) as client:
        # 客户端进入连接循环, 和服务端进行通信
        while True:
            await client.send('ready')
            data = await client.recv()
            data = data.decode('utf-8')
            if data:
                # 传递的数据包括: 用户id, 题号, 用户代码及所用语言, 判题机的时空限制, 评测数据最后更新时间
                judge_json = json.loads(data)
                async with open(f'./tmp/{judge_json["id"].judge_json["lan"]}', 'wt') as file:
                    await file.write(judge_json['code'])
                # 判题结果json数据, 传回给后端
                result_json = {
                    'uid': judge_json['uid'],
                    'id': judge_json['id'],
                    'lan': judge_json['lan'],
                    'test_case': 0,
                    'ti_use': 0,
                    'mem_use': 0,
                    'result': '',
                    'info': '',
                    'output': '',
                    'answer': ''
                }

                judge = Judge(judge_json)
                compile_info = judge.compile_code()
                if compile_info is not True:
                    result_json['result'] = 'COMPILE_ERROR'
                    result_json['info'] = compile_info
                    await client.send(json.dumps(result_json))
                    continue
                judge.get_judge_json()

                for out, err in run_judge(judge.proc_argv):
                    if err:
                        result_json['result'] = 'UNKNOWN_ERROR'
                        result_json['info'] = err
                    else:
                        out = json.loads(out)
                        result_json['test_case'] = out['test_case']
                        result_json['ti_use'] = out['ti_use']
                        result_json['mem_use'] = out['mem_use']
                        result_json['result'] = out['result']




                    await client.send(json.dumps(result_json))

            else:
                # 传输过程中可能出现了问题, 进行重连
                pass


if __name__ == '__main__':
    with open('./setting_client.json', mode='rt', encoding='utf-8') as f:
        client_json = json.load(f)
    asyncio.run(run_client(client_json['ip'], client_json['port']))

