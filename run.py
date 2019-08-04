import subprocess
import sys
import datetime

while True:
    print('[{}] Starting subprocess'.format(datetime.datetime.now()))
    proc = subprocess.Popen('python log.py', shell=True)
    proc.wait()
