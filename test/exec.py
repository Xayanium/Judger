import subprocess

process = subprocess.Popen(['./a.out'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = process.communicate()
print(out, err)

