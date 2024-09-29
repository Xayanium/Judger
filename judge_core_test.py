import subprocess
import sys
import time
import os

def run_with_strace(command, output_file):
    """
    Use strace to run a command and log its system calls to an output file.

    :param command: The command to run (as a list of arguments).
    :param output_file: The file to which strace output will be written.
    """
    try:
        # Run the command with strace
        with open(output_file, 'w') as file:
            # Execute strace with the specified command
            process = subprocess.Popen(['strace', '-o', output_file, '-tt', '-T'] + command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print(f"Started monitoring with strace, PID: {process.pid}")

            # Wait for the process to complete
            out, err = process.communicate()
            print("Process finished. Strace output written to:", output_file)

            if out:
                print("Standard Output:", out.decode())
            if err:
                print("Standard Error:", err.decode())

    except Exception as e:
        print("An error occurred:", e)

def main():
    # The command to monitor, replace this with the command you want to run
    command = ['python3', 'compile.py']  # Replace 'your_program.py' with the actual program to monitor

    # The output file for strace
    output_file = 'strace_output.log'

    # Run the command with strace and log the output
    run_with_strace(command, output_file)

if __name__ == "__main__":
    main()
