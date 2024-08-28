# coding: utf-8
# @Author: Xayanium

import time
import psutil
import subprocess


def monitor_process(process_name, interval=0.5):
    """
    Monitor the resource usage of a Python process by name.

    :param process_name: Name of the Python script to monitor (e.g., "myscript.py").
    :param interval: Interval in seconds between each monitoring update.
    """
    # Start the process
    process = subprocess.Popen(["python", process_name])

    try:
        while True:
            # Get the process object
            proc = psutil.Process(process.pid)

            # # 获取进程的亲和性设置
            # affinity = proc.cpu_affinity()
            # # 获取系统中的逻辑处理器数量
            # num_logical_cpus = psutil.cpu_count(logical=True)
            # # 输出进程的亲和性和逻辑处理器的数量
            # print(f"PID: {proc.pid}, Affinity: {affinity}, Logical CPUs: {num_logical_cpus}")

            cpu_usage = proc.cpu_percent(interval=interval)

            # Print CPU and memory usage
            print(f"PID: {proc.pid}, CPU: {cpu_usage}%, Memory: {proc.memory_percent()}%")

            # Sleep for the specified interval
            # time.sleep(interval)
    except KeyboardInterrupt:
        print("Monitoring stopped.")
    finally:
        # Clean up the process if it's still running
        if process.poll() is None:
            process.terminate()
            process.wait()


if __name__ == "__main__":
    # Replace "example_script.py" with the name of your script
    monitor_process("compile.py", interval=0.1)
