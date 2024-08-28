import subprocess
import json

# proc_args = ["/home/xa/JudgeCore/test/python_test/output/libcalc.so"]
#
# proc = subprocess.Popen(proc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# out, err = proc.communicate()
# # print(out.decode('utf-8'))
# # print(json.loads(out.decode('utf-8')))
# res = json.loads(out.decode('utf-8'))
# print(res)
# print(res['a/b'])


def run(max_time,
        max_memory,
        max_stack,
        max_output,
        input_path,
        output_path,
        error_path,
        exe_path,
        log_path
        ):

    int_vars = ["max_time", "max_memory", "max_stack", "max_output"]
    str_vars = ["input_path", "output_path", "error_path", "exe_path", "log_path"]

    proc_args = [""]

    for item in int_vars:
        value = vars()[item]
        if isinstance(value, int):
            proc_args.append(f"--{item}={value}")

    for item in str_vars:
        value = vars()[item]
        if isinstance(value, str):
            proc_args.append(f"--{item}={value}")

    proc = subprocess.Popen(proc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if not err:
        return json.loads(out.decode('utf-8'))

