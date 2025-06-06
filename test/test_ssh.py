import time

from ssh import (
    exec_command, 
    exec_command_interactive, 
    wait_for_ssh_ready,
)

from ec2 import (
    create_ec2_instance,
    get_ec2_instance_public_ip,
    wait_for_instance_state,
    terminate_ec2_instance,
)

def test_ssh():
    # create ec2 instance
    instance_id = create_ec2_instance("test_ssh_1")
    # wait for instance state to be running
    wait_for_instance_state(instance_id, "running")
    # get public ip
    public_ip = get_ec2_instance_public_ip(instance_id) 
    # print instance info
    print("instance name: test_ssh_1")
    print(f"Instance ID: {instance_id}")
    print(f"Public IP: {public_ip}")
    wait_for_ssh_ready(public_ip)
    print("--------------------------------")

    # echo 'Hello, World!'
    stdout, stderr = exec_command(public_ip, "echo 'Hello, World!'")
    print(f"echo 'Hello, World!': stdout: {stdout}")
    print(f"echo 'Hello, World!': stderr: {stderr}")
    time.sleep(10)
    print("--------------------------------")

    # trh-sdk version
    stdout, stderr = exec_command(public_ip, "trh-sdk version")
    print(f"trh-sdk version: stdout: {stdout}")
    print(f"trh-sdk version: stderr: {stderr}")
    time.sleep(10)
    print("--------------------------------")

    # docker permission
    stdout, stderr = exec_command(public_ip, "sudo chmod 666 /var/run/docker.sock")
    print(f"sudo chmod 666 /var/run/docker.sock: stdout: {stdout}")
    print(f"sudo chmod 666 /var/run/docker.sock: stderr: {stderr}")
    time.sleep(10)
    print("--------------------------------")

    # trh-sdk deploy, using interactive mode
    stdout, stderr = exec_command_interactive(public_ip, "trh-sdk deploy")
    print("trh-sdk deploy")
    print(f"trh-sdk deploy: stdout: {stdout}")
    print(f"trh-sdk deploy: stderr: {stderr}")
    time.sleep(10)
    print("--------------------------------")

    # checking devnet layer1
    stdout, stderr = exec_command(public_ip, "cast chain-id --rpc-url http://localhost:8545")
    print(f"cast chain-id --rpc-url http://localhost:8545: stdout: {stdout}")
    print(f"cast chain-id --rpc-url http://localhost:8545: stderr: {stderr}")
    time.sleep(10)
    print("--------------------------------")

    # checking devnet layer2
    stdout, stderr = exec_command(public_ip, "cast chain-id --rpc-url http://localhost:9545")
    print(f"cast chain-id --rpc-url http://localhost:9545: stdout: {stdout}")
    print(f"cast chain-id --rpc-url http://localhost:9545: stderr: {stderr}")
    time.sleep(10)
    print("--------------------------------")

    # trh-sdk destroy
    stdout, stderr = exec_command(public_ip, "trh-sdk destroy")
    print("trh-sdk destroy")
    print(f"trh-sdk destroy: stdout: {stdout}")
    print(f"trh-sdk destroy: stderr: {stderr}")
    time.sleep(10)
    print("--------------------------------")

    # terminate ec2 instance
    terminate_ec2_instance(instance_id)
    wait_for_instance_state(instance_id, "terminated", timeout=600)

if __name__ == "__main__":
    test_ssh()


