# import relative files
from web_viewer import webview_run
import warnings

#import API's 
import sys
import threading
import json
import os
import subprocess

warnings.filterwarnings("ignore", message="URL.raw is deprecated.")


# os.environ["OS_ACTIVITY_MODE"] = "disable"

read_fd, write_fd = os.pipe()
os.set_inheritable(write_fd, True)

# Transfer the filedesc through env
env = os.environ.copy()
env["WRITE_FD"] = str(write_fd)

def main():
    config = None
    with open('config.json') as f: 
        config = json.load(f)

    process = subprocess.Popen(
        ["python3", "src/zsh_shell.py"],
        env=env,               
        pass_fds=(write_fd,)  
    )
    print("Hit <ENTER> to start...")
    webview_run(config, read_fd)

if __name__ == '__main__':
    main()