import paramiko
import os
import time
import socket

from dotenv import load_dotenv
from os.path import join, dirname

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Use the key file from the current directory
# KEY_PATH = join(dirname(__file__), 'kevin1.pem')
KEY_PATH = os.getenv("SSH_KEY_PATH")
USERNAME = os.getenv("SSH_USERNAME")

PRE_COMMAND = """
export PATH=/home/ubuntu/.local/share/pnpm:/home/ubuntu/.nvm/versions/node/v20.16.0/bin:/home/ubuntu/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/usr/local/go/bin:/home/ubuntu/.foundry/bin:$PATH;
"""

def exec_command(
        hostname, 
        command,
        username="ubuntu", 
        key_path=KEY_PATH, 
        precommand=PRE_COMMAND,
    ):
    # print(f"Using key: {key_path}, username: {username}")  # 디버깅용 출력
    key = paramiko.RSAKey.from_private_key_file(key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=hostname, username=username, pkey=key)
    sin,sout,serr = client.exec_command(precommand+command,get_pty=False)
    
    return sout.read().decode(), serr.read().decode()

def exec_command_interactive(
        hostname, 
        command,
        username="ubuntu", 
        key_path=KEY_PATH, 
        precommand=PRE_COMMAND,
    ):
    key = paramiko.RSAKey.from_private_key_file(key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(hostname=hostname, username=username, pkey=key)

    # print('started...')
    stdin, stdout, stderr = client.exec_command(precommand+command, get_pty=True)

    output = ''
    for line in iter(stdout.readline, ""):
        print(line, end="")
        output += line
    # print('finished.')

    return output, stderr.read().decode()

def wait_for_ssh_ready(host, port=22, timeout=300):
    """Wait until SSH port (22) is open"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=5):
                print("SSH port is now open.")
                return True
        except Exception:
            print("SSH port is not open yet. Retrying...")
            time.sleep(5)
    print("SSH port did not open. (timeout)")
    return False