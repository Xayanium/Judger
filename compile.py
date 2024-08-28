# coding: utf-8
# @Author: Xayanium

import json
import subprocess
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import time


class JudgeInfo:
    def __init__(self, t_case, ti_lim, mem_lim, exec_path, in_path, out_path, err_path, ans_path, is_spj):
        self.t_case = t_case
        self.ti_lim = ti_lim
        self.mem_lim = mem_lim
        self.exec_path = exec_path
        self.in_path = in_path
        self.out_path = out_path
        self.err_path = err_path
        self.ans_path = ans_path
        self.is_spj = is_spj


def compile_code(lan, name):
    proc_args = ''
    if lan == 'c':
        proc_args = f'gcc ./tmp/{name}.c -o ./tmp/{name} -O2 -Wall'
    elif lan == 'cpp':
        proc_args = f'g++ ./tmp/{name}.cpp -o ./tmp/{name} -O2 -Wall'
    elif lan == 'java':
        proc_args = f'javac ./tmp/Main.java -d ./tmp'

    proc = subprocess.Popen(proc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    if not err:
        print('compile successful')
    else:
        if err.decode('utf-8').find('error') != -1:
            print('compile error')
            print(err.decode('utf-8'))
        else:
            print('compile successful')
        return


# def run_code(_lan, _name, _t_case, _ti_lim, _mem_lim, _exec_path, _in_path, _out_path, _err_path, _ans_path, _is_spj):
    # proc_args = {'id': _t_case, 'ti_lim': _ti_lim, 'mem_lim': _mem_lim,
    #              'exec_path': _exec_path, 'in_path': _in_path, 'out_path': _out_path,
    #              'err_path': _err_path, 'ans_path': _ans_path, 'is_spj': _is_spj
    #              }
    # proc_json = ['/home/xa/JudgeHost/output/judge', json.dumps(proc_args)]
def run_code(proc_args: list[str]):
    proc = subprocess.Popen(proc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    # if not err:
    #     print('run successful')
    #     print(out.decode('utf-8'))
    # else:
    #     print('run error')
    #     print(err.decode('utf-8'))
    return out.decode('utf-8'), err.decode('utf-8')


if __name__ == '__main__':
    st_time = time.time()

    # 获取当前python文件所在目录
    current_path = os.path.dirname(os.path.abspath(__file__))
    # # 获取当前python文件所在项目的上级目录
    # root_path = os.path.dirname(current_path)

    lan = 'c'
    p_name = 'p0001'
    ti_lim = 1
    mem_lim = 64
    exec_path = f'{current_path}/tmp/{p_name}'
    is_spj = 0
    path = f'{current_path}/problem/{p_name}'

    compile_code(lan, p_name)

    proc_argv = []

    # 将判题json加入列表中, 方便进程池调用
    for file in os.listdir(path + '/in'):
        file_name = file.split('.')[0]
        t_case = file_name.split('_')[1]

        in_path = os.path.join(path + '/in', file)
        ans_path = os.path.join(path + '/out', file_name + '.out')
        out_path = f'{current_path}/tmp/{p_name}_{t_case}.txt'
        err_path = f'{current_path}/tmp/{p_name}er_{t_case}.txt'

        t_case = int(t_case)
        judge_json = {'id': t_case, 'ti_lim': ti_lim, 'mem_lim': mem_lim,
                      'exec_path': exec_path, 'in_path': in_path, 'out_path': out_path,
                      'err_path': err_path, 'ans_path': ans_path, 'is_spj': is_spj
                      }
        proc_json = ['/home/xa/JudgeHost/output/judge', json.dumps(judge_json)]
        proc_argv.append(proc_json)

    print('start process pool')
    # 使用进程池创建判题核心进程
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(run_code, proc_args) for proc_args in proc_argv]

        for future in as_completed(futures):
            # print(future.result())
            out, err = future.result()
            print(out)

        # print(os.getpid())
        print('finish')
        print(f'time usage: {time.time()-st_time}')
        # run_code(lan, p_name, t_case, ti_lim, mem_lim, exec_path, in_path, out_path, err_path, ans_path, is_spj)
    # in_path = '/home/xa/JudgeHost/problem/p0001/in/p0001_5.in'
    # ans_path = '/home/xa/JudgeHost/problem/p0001/out/p0001_5.out'
    # out_path = '/home/xa/JudgeHost/tmp/p0001_5.txt'
    # err_path = '/home/xa/JudgeHost/tmp/p0001er_5.txt'
    # t_case = 2
    # run_code(lan, p_name, t_case, ti_lim, mem_lim, exec_path, in_path, out_path, err_path, ans_path, is_spj)
