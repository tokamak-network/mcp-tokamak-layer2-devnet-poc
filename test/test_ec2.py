import pytest
import asyncio
import os
import time
from datetime import datetime

from ec2 import (
    create_ec2_instance,
    terminate_ec2_instance,
    get_ec2_instance,
    get_ec2_instance_public_ip,
    wait_for_instance_state,
    describe_ec2_instances,
)

# Test data
TEST_INSTANCE_NAME = f"test-instance-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

@pytest.fixture(autouse=True)
def cleanup_test_instances():
    """Cleanup test instances after each test."""
    yield
    # Get all instances with test prefix
    instances = describe_ec2_instances()
    for reservation in instances:
        for instance in reservation.get('Instances', []):
            for tag in instance.get('Tags', []):
                if tag['Key'] == 'Name' and tag['Value'].startswith('test-instance-'):
                    terminate_ec2_instance(instance['InstanceId'])

@pytest.mark.asyncio
async def test_create_and_terminate_instance():
    """Test creating and terminating an EC2 instance."""
    # Create instance
    instance_id = create_ec2_instance(TEST_INSTANCE_NAME)
    assert instance_id is not None
    
    # Wait for instance to be running
    await asyncio.to_thread(wait_for_instance_state, instance_id, "running")
    
    # Get instance details
    instance = get_ec2_instance(instance_id)
    assert instance is not None
    assert instance.state['Name'] == 'running'
    
    # Get public IP
    public_ip = get_ec2_instance_public_ip(instance_id)
    assert public_ip is not None
    
    # Terminate instance
    terminate_result = terminate_ec2_instance(instance_id)
    assert terminate_result is not None
    
    # Wait for instance to be terminated
    await asyncio.to_thread(wait_for_instance_state, instance_id, "terminated")
    
    # Verify instance is terminated
    instance = get_ec2_instance(instance_id)
    assert instance.state['Name'] == 'terminated'

@pytest.mark.asyncio
async def test_instance_state_transitions():
    """Test EC2 instance state transitions."""
    # Create instance
    instance_id = create_ec2_instance(TEST_INSTANCE_NAME)
    
    # Test running state
    await asyncio.to_thread(wait_for_instance_state, instance_id, "running")
    instance = get_ec2_instance(instance_id)
    assert instance.state['Name'] == 'running'
    
    # Test stopping state
    instance.stop()
    await asyncio.to_thread(wait_for_instance_state, instance_id, "stopped")
    instance = get_ec2_instance(instance_id)
    assert instance.state['Name'] == 'stopped'
    
    # Test starting state
    instance.start()
    await asyncio.to_thread(wait_for_instance_state, instance_id, "running")
    instance = get_ec2_instance(instance_id)
    assert instance.state['Name'] == 'running'
    
    # Cleanup
    terminate_ec2_instance(instance_id)
    await asyncio.to_thread(wait_for_instance_state, instance_id, "terminated")

@pytest.mark.asyncio
async def test_get_instance_details():
    """Test getting EC2 instance details."""
    # Create instance
    instance_id = create_ec2_instance(TEST_INSTANCE_NAME)
    
    # Wait for instance to be running
    await asyncio.to_thread(wait_for_instance_state, instance_id, "running")
    
    # Get instance details
    instance = get_ec2_instance(instance_id)
    assert instance is not None
    assert instance.id == instance_id
    assert instance.instance_type == os.getenv("INSTANCE_TYPE", "t3.large")
    assert instance.image_id == os.getenv("IMAGE_ID")
    
    # Get public IP
    public_ip = get_ec2_instance_public_ip(instance_id)
    assert public_ip is not None
    assert isinstance(public_ip, str)
    
    # Cleanup
    terminate_ec2_instance(instance_id)
    await asyncio.to_thread(wait_for_instance_state, instance_id, "terminated")

@pytest.mark.asyncio
async def test_describe_instances():
    """Test describing EC2 instances."""
    # Create test instance
    instance_id = create_ec2_instance(TEST_INSTANCE_NAME)
    
    # Wait for instance to be running
    await asyncio.to_thread(wait_for_instance_state, instance_id, "running")
    
    # Get all instances
    instances = describe_ec2_instances()
    assert instances is not None
    assert len(instances) > 0
    
    # Find our test instance
    test_instance = None
    for reservation in instances:
        for instance in reservation.get('Instances', []):
            if instance['InstanceId'] == instance_id:
                test_instance = instance
                break
        if test_instance:
            break
    
    assert test_instance is not None
    assert test_instance['InstanceId'] == instance_id
    assert test_instance['State']['Name'] == 'running'
    
    # Cleanup
    terminate_ec2_instance(instance_id)
    await asyncio.to_thread(wait_for_instance_state, instance_id, "terminated")

@pytest.mark.asyncio
async def test_instance_timeout():
    """Test instance state transition timeout."""
    # Create instance
    instance_id = create_ec2_instance(TEST_INSTANCE_NAME)
    
    # Test timeout with invalid state
    with pytest.raises(Exception):
        await asyncio.to_thread(wait_for_instance_state, instance_id, "invalid_state", timeout=5)
    
    # Cleanup
    terminate_ec2_instance(instance_id)
    await asyncio.to_thread(wait_for_instance_state, instance_id, "terminated") 