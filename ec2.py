import boto3
import os
import time
from dotenv import load_dotenv
from os.path import join, dirname

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

AWS_ACCESS_KEY = os.getenv("IAM_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("IAM_SECRET_KEY")
REGION_NAME = os.getenv("REGION_NAME")

IMAGE_ID = os.getenv("IMAGE_ID")
INSTANCE_TYPE = os.getenv("INSTANCE_TYPE")
KEY_NAME = os.getenv("SSH_KEY_NAME")
SECURITY_GROUP_IDS = [os.getenv("SECURITY_GROUP_ID")]

ec2 = boto3.client("ec2",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION_NAME
)

def describe_ec2_instances():
    """Describe all EC2 instances
    Returns:
    {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-01234567890123456",
                        "InstanceType": "t3.large",
                        "State": {
                            "Name": "running"
                        },
                        "PublicIpAddress": "192.168.1.100",
                        "PrivateIpAddress": "192.168.1.100",
                        "KeyName": "kevin1",
                        "SecurityGroups": [
                            {
                                "GroupName": "kevin1",
                                "GroupId": "sg-01234567890123456"
                            }
                        ]
                    }
    """
    response = ec2.describe_instances()
    return response["Reservations"]

def create_ec2_instance(name: str):
    """Create an EC2 instance
    Args:
        name: The name of the instance
    Returns: Instance ID and Public IP address
        Instance.id
    """

    tag_specifications = [
        {
            "ResourceType": "instance",
            "Tags": [
                {
                    "Key": "Name",
                    "Value": name
                }
            ]
        }
    ]

    instance_params = {
        "ImageId":IMAGE_ID,
        "MinCount":1,
        "MaxCount":1,
        "InstanceType":"t3.large",
        "KeyName":KEY_NAME,
        "SecurityGroupIds":SECURITY_GROUP_IDS,
        # "UserData":user_data,
        "TagSpecifications":tag_specifications
    }

    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY, 
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME
    )

    ec2r = session.resource('ec2')
    instances = ec2r.create_instances(**instance_params)

    return instances[0].id

def create_ec2_instance_by_image(name: str, image_id: str):
    """Create an EC2 instance by image
    Args:
        name: The name of the instance
        image_id: The ID of the image
    Returns: Instance ID and Public IP address
    """
    tag_specifications = [
        {
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": name}]
        }
    ]

    instance_params = {
        "ImageId":image_id,
        "MinCount":1,
        "MaxCount":1,
        "InstanceType":"t3.large",
        "KeyName":KEY_NAME,
        "SecurityGroupIds":SECURITY_GROUP_IDS,
        "TagSpecifications":tag_specifications
    }
    
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY, 
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME
    )

    ec2r = session.resource('ec2')
    instances = ec2r.create_instances(**instance_params)

    return instances[0].id, instances[0].public_ip_address
    

def terminate_ec2_instance(instance_id):
    # Terminate an EC2 instance
    """
    Args:
        instance_id: The ID of the instance to terminate
    Returns:
        response: The response from the terminate request
        {
            'TerminatingInstances': [{'InstanceId': 'i-0d871b6e201a9a0f0',
            'CurrentState': {'Code': 32, 'Name': 'shutting-down'},
            'PreviousState': {'Code': 16, 'Name': 'running'}}],
            'ResponseMetadata': {'RequestId': 'bf0eaedd-c217-4310-bcff-0ee4626ad3d3',
            'HTTPStatusCode': 200,
            'HTTPHeaders': {'x-amzn-requestid': 'bf0eaedd-c217-4310-bcff-0ee4626ad3d3',
            'cache-control': 'no-cache, no-store',
            'strict-transport-security': 'max-age=31536000; includeSubDomains',
            'content-type': 'text/xml;charset=UTF-8',
            'content-length': '426',
            'date': 'Wed, 04 Jun 2025 23:09:10 GMT',
            'server': 'AmazonEC2'},
            'RetryAttempts': 0}
        }
    """
    ec2 = boto3.resource('ec2',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME
    )

    # Retrieve the instance to be terminated
    instance = ec2.Instance(instance_id)

    # Terminate the EC2 instance
    response = instance.terminate()

    # Wait for the instance to terminate
    # instance.wait_until_terminated() # It takes 10~20 seconds depends on environment

    print("Terminated instance:", instance_id)
    return response


def reboot_ec2_instance(instance_id):
    """Reboot an EC2 instance
    Args:
        instance_id: The ID of the instance
    Returns:
        response: The response from the reboot request
    """
    ec2 = boto3.resource('ec2',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME
    )

    instance = ec2.Instance(instance_id)
    response = instance.reboot()

    return response

def stop_ec2_instance(instance_id):
    """Stop an EC2 instance
    Args:
        instance_id: The ID of the instance
    Returns:
        response: The response from the stop request
    """
    ec2 = boto3.resource('ec2',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME
    )

    instance = ec2.Instance(instance_id)
    response = instance.stop()

    return response

def start_ec2_instance(instance_id):
    """Start an EC2 instance
    Args:
        instance_id: The ID of the instance
    Returns:
        response: The response from the start request
    """
    ec2 = boto3.resource('ec2',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME
    )

    instance = ec2.Instance(instance_id)
    response = instance.start()

    return response

def get_ec2_instance(instance_id):
    """Get an EC2 instance
    Args:
        instance_id: The ID of the instance
    Returns:
        instance: The instance object
    """
    ec2 = boto3.resource('ec2',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME
    )

    instance = ec2.Instance(instance_id)    

    return instance

def get_ec2_instance_public_ip(instance_id):
    """Get the public IP address of an EC2 instance
    Args:
        instance_id: The ID of the instance
    Returns:
        public_ip_address: The public IP address of the instance
    """
    ec2 = boto3.resource('ec2',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION_NAME
    )

    # Retrieve the instance to be terminated
    instance = ec2.Instance(instance_id)

    return instance.public_ip_address

def wait_for_instance_state(instance_id, desired_state, timeout=300):
    """Wait for an instance to reach a desired state
    Args:
        instance_id: The ID of the instance
        desired_state: The desired state ('running', 'stopped', 'terminated')
        timeout: Maximum time to wait in seconds
    Returns:
        bool: True if the instance reached the desired state, False if timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        instance = get_ec2_instance(instance_id)
        current_state = instance.state['Name']
        print(f"Current instance state: {current_state}")
        
        if current_state == desired_state:
            return True
            
        time.sleep(10)
    
    return False

def test_ec2_operations():
    """Test all EC2 instance operations"""
    print("Starting EC2 instance operations test...")
    
    # 1. Create a new instance
    print("\n1. Creating a new EC2 instance...")
    instance_id = create_ec2_instance("test_instance_by_cursor_1")
    print(f"Created instance: {instance_id}")
    print("Waiting for instance to be running...")
    if not wait_for_instance_state(instance_id, 'running'):
        print("Timeout waiting for instance to start")
        return
    
    # 2. Get instance details
    print("\n2. Getting instance details...")
    instance = get_ec2_instance(instance_id)
    print(f"Instance state: {instance.state['Name']}")
    print("Waiting 20 seconds before next operation...")
    time.sleep(20)
    
    # 3. Get public IP
    print("\n3. Getting public IP...")
    ip = get_ec2_instance_public_ip(instance_id)
    print(f"Public IP: {ip}")
    print("Waiting 20 seconds before next operation...")
    time.sleep(20)
    
    # 4. Stop the instance
    print("\n4. Stopping the instance...")
    stop_response = stop_ec2_instance(instance_id)
    print("Stop response:", stop_response)
    print("Waiting for instance to be stopped...")
    if not wait_for_instance_state(instance_id, 'stopped'):
        print("Timeout waiting for instance to stop")
        return
    
    # 5. Start the instance
    print("\n5. Starting the instance...")
    start_response = start_ec2_instance(instance_id)
    print("Start response:", start_response)
    print("Waiting for instance to be running...")
    if not wait_for_instance_state(instance_id, 'running'):
        print("Timeout waiting for instance to start")
        return
    
    # 6. Reboot the instance
    print("\n6. Rebooting the instance...")
    reboot_response = reboot_ec2_instance(instance_id)
    print("Reboot response:", reboot_response)
    print("Waiting for instance to be running after reboot...")
    if not wait_for_instance_state(instance_id, 'running'):
        print("Timeout waiting for instance to start after reboot")
        return
    
    # 7. List all instances
    print("\n7. Listing all instances...")
    instances = describe_ec2_instances()
    for reservation in instances:
        for instance in reservation['Instances']:
            print(f"Instance ID: {instance['InstanceId']}")
            print(f"State: {instance['State']['Name']}")
            print(f"Public IP: {instance.get('PublicIpAddress', 'N/A')}")
            print("---")
    print("Waiting 20 seconds before next operation...")
    time.sleep(20)
    
    # 8. Terminate the instance
    print("\n8. Terminating the instance...")
    terminate_response = terminate_ec2_instance(instance_id)
    print("Terminate response:", terminate_response)
    print("Waiting for instance to be terminated...")
    if not wait_for_instance_state(instance_id, 'terminated'):
        print("Timeout waiting for instance to terminate")
        return
    
    print("\nEC2 instance operations test completed!")

# if __name__ == "__main__":
    # test_ec2_operations()