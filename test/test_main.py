import asyncio
import pytest
import pytest_asyncio
import os
import logging
import time

from tinydb import TinyDB, Query
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use a separate test database
TEST_DB_PATH = "test.db"
db = TinyDB(TEST_DB_PATH)

from main import (
    get_balance,
    create_account,
    create_account_from_mnemonic,
    save_account,
    save_many_accounts,
    get_all_accounts,
    get_account,
    delete_account,
    get_latest_block,
    get_block_by_number,
    create_new_devnet,
    get_ec2_instance,
    terminate_ec2_instance,
    wait_for_instance_state,
    destroy_devnet,
    check_instance_status,
    send_transaction,
)

from ssh import (
    wait_for_ssh_ready,
    exec_command,
    exec_command_interactive,
)
from ec2 import (
    create_ec2_instance,
    get_ec2_instance_public_ip,
)

# Test data
TEST_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Example Ethereum address
TEST_MNEMONIC = "test test test test test test test test test test test junk"

# Fixture to clean up test database
@pytest.fixture(autouse=True)
def cleanup_db():
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest_asyncio.fixture(scope="function")
async def devnet_instance():
    """Fixture to create a devnet instance for testing."""
    test_name = f"test_devnet_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    instance = await create_new_devnet(test_name)
    yield instance
    # Cleanup after test
    await destroy_devnet(instance["instance_id"])

@pytest.mark.asyncio
async def test_get_balance():
    """Test getting balance of an Ethereum address"""
    result = await get_balance(TEST_ADDRESS)
    assert isinstance(result, dict)
    assert "address" in result
    assert "balance" in result
    assert result["address"] == TEST_ADDRESS
    assert isinstance(result["balance"], int)

@pytest.mark.asyncio
async def test_create_account():
    """Test creating a new Ethereum account"""
    result = await create_account(2)  # Create 2 accounts
    assert isinstance(result, list)
    assert len(result) == 2
    for account in result:
        assert "address" in account
        assert "private_key" in account
        assert account["address"].startswith("0x")
        assert account["private_key"].startswith("0x")

@pytest.mark.asyncio
async def test_create_account_from_mnemonic():
    """Test creating an account from mnemonic"""
    result = await create_account_from_mnemonic(TEST_MNEMONIC)
    assert isinstance(result, dict)
    assert "address" in result
    assert "private_key" in result
    assert result["address"].startswith("0x")
    # private_key can be either bytes or str
    if isinstance(result["private_key"], bytes):
        assert result["private_key"].startswith(b"0x")
    else:
        assert result["private_key"].startswith("0x")

@pytest.mark.asyncio
async def test_save_and_get_account():
    """Test saving and retrieving an account"""
    # Create and save an account
    accounts = await create_account(1)
    account = accounts[0]
    
    # Save the account
    save_result = await save_account(account["address"], account["private_key"])
    assert save_result["message"] == "Account saved successfully"
    
    # Get the account
    get_result = await get_account(account["address"])
    assert len(get_result) > 0
    assert get_result[0]["address"] == account["address"]
    assert get_result[0]["private_key"] == account["private_key"]
    
    # Clean up
    await delete_account(account["address"])

@pytest.mark.asyncio
async def test_save_many_accounts():
    """Test saving multiple accounts"""
    # Create multiple accounts
    accounts = await create_account(3)
    
    # Save the accounts
    save_result = await save_many_accounts(accounts)
    assert save_result["message"] == "Accounts saved successfully"
    
    # Get all accounts
    all_accounts = await get_all_accounts()
    assert len(all_accounts) >= len(accounts)
    
    # Clean up
    for account in accounts:
        await delete_account(account["address"])

@pytest.mark.asyncio
async def test_get_latest_block():
    """Test getting the latest block information"""
    result = await get_latest_block()
    assert isinstance(result, dict)
    assert "block_number" in result
    assert "timestamp" in result
    assert "miner" in result
    assert "hash" in result
    assert isinstance(result["block_number"], int)
    assert isinstance(result["timestamp"], int)

@pytest.mark.asyncio
async def test_get_block_by_number():
    """Test getting information about a specific block"""
    # First get the latest block number
    latest_block = await get_latest_block()
    block_number = latest_block["block_number"]
    
    # Then get that specific block
    result = await get_block_by_number(block_number)
    assert isinstance(result, dict)
    assert result["block_number"] == block_number
    assert "timestamp" in result
    assert "miner" in result
    assert "hash" in result

@pytest.mark.asyncio
async def test_create_new_devnet(devnet_instance, caplog):
    """Test creating a new Devnet Layer1 instance (fixture 사용)"""
    caplog.set_level(logging.INFO)
    result = devnet_instance
    assert isinstance(result, dict)
    assert "name" in result
    assert "instance_id" in result
    assert "public_ip" in result
    # Get instance details
    instance = get_ec2_instance(result["instance_id"])
    assert instance.state["Name"] == "running"
    # 로그 출력 확인
    for record in caplog.records:
        print(f"Log: {record.message}")

@pytest.mark.asyncio
async def test_check_instance_status(devnet_instance, caplog):
    """Test checking EC2 instance status (devnet_instance 활용)"""
    caplog.set_level(logging.INFO)
    result = devnet_instance
    status = await check_instance_status(result["instance_id"])
    assert isinstance(status, dict)
    assert "instance_id" in status
    assert "state" in status
    assert "public_ip" in status
    assert status["state"] == "running"
    # 로그 출력 확인
    for record in caplog.records:
        print(f"Log: {record.message}")

@pytest.mark.asyncio
async def test_destroy_devnet(devnet_instance, caplog):
    """Test destroying a Devnet instance (fixture 사용)"""
    caplog.set_level(logging.INFO)
    result = devnet_instance
    # Verify the instance was created and stored in DB
    assert isinstance(result, dict)
    assert "name" in result
    assert "instance_id" in result
    assert "public_ip" in result
    assert "layer1_url" in result
    assert "layer2_url" in result
    
    # Destroy the instance
    destroy_result = await destroy_devnet(result["instance_id"])
    assert isinstance(destroy_result, dict)
    assert "message" in destroy_result
    assert "destroyed successfully" in destroy_result["message"]
    
    # Wait for instance to be fully terminated
    await asyncio.to_thread(wait_for_instance_state, result["instance_id"], "terminated")
    
    # Verify instance is terminated
    instance = get_ec2_instance(result["instance_id"])
    assert instance.state["Name"] == "terminated"
    
    # Verify instance is removed from DB
    devnet = db.search(Query().instance_id == result["instance_id"])
    assert len(devnet) == 0
    # 로그 출력 확인
    for record in caplog.records:
        print(f"Log: {record.message}")

@pytest.mark.asyncio
async def test_devnet_creation_and_destroy_time():
    """Test execution time of devnet creation and destruction using a single instance."""
    print("\n=== Devnet Creation and Destruction Time Measurement ===")
    
    # Create devnet name with current timestamp
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    devnet_name = f"devnet_time_{current_time}"
    
    # Create new devnet and measure creation time
    start_time = time.time()
    devnet = await create_new_devnet(devnet_name)
    creation_time = time.time() - start_time
    
    print(f"\nDevnet creation total time: {creation_time:.2f} seconds")
    print(f"Devnet details: {devnet}")
    
    # Wait for a moment to ensure devnet is fully created
    await asyncio.sleep(5)
    
    # Measure destroy time
    destroy_start = time.time()
    result = await destroy_devnet(devnet["instance_id"])
    destroy_time = time.time() - destroy_start
    
    print(f"\nDevnet destruction time: {destroy_time:.2f} seconds")
    print(f"Destroy result: {result}")
    
    print(f"\nTotal time (creation + destruction): {creation_time + destroy_time:.2f} seconds")

@pytest.mark.asyncio
async def test_devnet_creation_steps_time():
    """Test execution time of each step in devnet creation."""
    print("\n=== Detailed Devnet Creation Steps Time Measurement ===")
    
    # Create devnet name with current timestamp
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    devnet_name = f"devnet_steps_{current_time}"
    
    start_time = time.time()
    
    # Step 1: Create EC2 instance
    instance_id = create_ec2_instance(devnet_name)
    instance_time = time.time() - start_time
    print(f"\nEC2 instance creation time: {instance_time:.2f} seconds")
    
    # Step 2: Wait for instance state
    wait_start = time.time()
    wait_result = wait_for_instance_state(instance_id, "running")
    wait_time = time.time() - wait_start
    print(f"Instance state change time: {wait_time:.2f} seconds")
    
    # Step 3: Get public IP
    ip_start = time.time()
    public_ip = get_ec2_instance_public_ip(instance_id)
    ip_time = time.time() - ip_start
    print(f"Get public IP time: {ip_time:.2f} seconds")
    
    # Step 4: Wait for SSH
    ssh_start = time.time()
    ssh_ready = wait_for_ssh_ready(public_ip)
    ssh_time = time.time() - ssh_start
    print(f"SSH ready time: {ssh_time:.2f} seconds")
    
    # Step 5: Set docker permissions
    docker_start = time.time()
    docker_permission = exec_command(public_ip, "sudo chmod 666 /var/run/docker.sock")
    docker_time = time.time() - docker_start
    print(f"Docker permission setup time: {docker_time:.2f} seconds")
    
    # Step 6: Deploy devnet
    deploy_start = time.time()
    deploy_result = exec_command_interactive(public_ip, "trh-sdk deploy")
    deploy_time = time.time() - deploy_start
    print(f"Devnet deployment time: {deploy_time:.2f} seconds")
    
    total_time = time.time() - start_time
    print(f"\nTotal devnet creation time: {total_time:.2f} seconds")
    
    # Clean up
    await destroy_devnet(instance_id)

@pytest.mark.asyncio
async def test_get_devnet_instance():
    """Test getting a specific devnet instance."""
    # Add test data to database
    test_instance = {
        "type": "devnet",
        "name": "test-devnet",
        "instance_id": "i-test123",
        "public_ip": "127.0.0.1",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "layer1_url": "http://127.0.0.1:8545",
        "layer2_url": "http://127.0.0.1:9545",
    }
    db.insert(test_instance)
    
    # Test getting the instance
    result = db.search(Query().instance_id == "i-test123")
    assert result is not None
    assert result[0]["instance_id"] == "i-test123"
    assert result[0]["type"] == "devnet"
    
    # Cleanup
    db.remove(Query().instance_id == "i-test123")

@pytest.mark.asyncio
async def test_get_all_devnets():
    """Test getting all devnet instances."""
    # Add test data to database
    test_instances = [
        {
            "type": "devnet",
            "name": "test-devnet-1",
            "instance_id": "i-test123",
            "public_ip": "127.0.0.1",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "layer1_url": "http://127.0.0.1:8545",
            "layer2_url": "http://127.0.0.1:9545",
        },
        {
            "type": "devnet",
            "name": "test-devnet-2",
            "instance_id": "i-test456",
            "public_ip": "127.0.0.2",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "layer1_url": "http://127.0.0.2:8545",
            "layer2_url": "http://127.0.0.2:9545",
        }
    ]
    db.insert_multiple(test_instances)
    
    # Test getting all instances
    results = db.search(Query().type == "devnet")
    assert len(results) >= 2
    assert any(d["instance_id"] == "i-test123" for d in results)
    assert any(d["instance_id"] == "i-test456" for d in results)
    
    # Cleanup
    db.remove(Query().type == "devnet")

@pytest.mark.asyncio
async def test_send_transaction_layer1_specific_account(devnet_instance):
    """Test sending a transaction on Layer1 using the specific account"""
    # Test account details
    from_private_key = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
    
    # Create a new account to send to
    to_accounts = await create_account(1)
    to_address = to_accounts[0]["address"]
    
    # Send transaction
    tx_result = await send_transaction(
        from_private_key=from_private_key,
        to_address=to_address,
        amount_ether=1.0,  # 1 ETH
        type="Layer1",
        url=devnet_instance["layer1_url"]
    )
    
    assert isinstance(tx_result, dict)
    assert "tx" in tx_result
    assert "hash" in tx_result
    assert tx_result["hash"].startswith("0x")
    
    # Wait for transaction to be mined
    await asyncio.sleep(2)
    
    # Check balances after transaction
    from_balance = await get_balance(tx_result["tx"]["from"])
    to_balance = await get_balance(to_address)
    
    print(f"\nTransaction Details:")
    print(f"From: {tx_result['tx']['from']}")
    print(f"To: {to_address}")
    print(f"Amount: {tx_result['value']} wei")
    print(f"Transaction Hash: {tx_result['hash']}")
    print(f"From Balance: {from_balance['balance']} wei")
    print(f"To Balance: {to_balance['balance']} wei")

@pytest.mark.asyncio
async def test_send_transaction_layer2_specific_account(devnet_instance):
    """Test sending a transaction on Layer2 using a specific account."""
    # Clean up database before test
    db.remove(Query().type == "transaction")
    
    # Test account details
    test_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    test_private_key = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
    
    # Create a new account to receive the transaction
    accounts = await create_account(1)
    to_account = accounts[0]
    
    # Save accounts to database
    await save_account(test_address, test_private_key)
    await save_many_accounts(accounts)
    
    # Get initial balances
    from_balance_before = await get_balance(test_address, url=devnet_instance["layer2_url"])
    to_balance_before = await get_balance(to_account["address"], url=devnet_instance["layer2_url"])
    
    print(f"From Balance Before: {from_balance_before['balance']} wei")
    print(f"To Balance Before: {to_balance_before['balance']} wei")
    
    # Send 1 ETH from test account to new account on Layer2
    result = await send_transaction(
        from_private_key=test_private_key,
        to_address=to_account["address"],
        amount_ether=1,
        type="Layer2",
        url=devnet_instance["layer2_url"]
    )
    
    # Verify transaction result
    assert isinstance(result, dict)
    assert "tx" in result
    assert result["tx"]["from"].lower() == test_address.lower()
    assert result["tx"]["to"].lower() == to_account["address"].lower()
    assert result["tx"]["value"] == 10**18
    
    # Wait for transaction to be mined
    await asyncio.sleep(2)
    
    # Get final balances
    from_balance_after = await get_balance(test_address, url=devnet_instance["layer2_url"])
    to_balance_after = await get_balance(to_account["address"], url=devnet_instance["layer2_url"])

    # Calculate expected balances considering gas costs
    expected_from_balance = from_balance_before["balance"] - 10**18 - result["tx"]["gas"] * result["tx"]["gasPrice"]
    expected_to_balance = to_balance_before["balance"] + 10**18

    # Print balance details for debugging
    print(f"From Balance After: {from_balance_after['balance']} wei")
    print(f"Expected From Balance: {expected_from_balance} wei")
    print(f"To Balance After: {to_balance_after['balance']} wei")
    print(f"Expected To Balance: {expected_to_balance} wei")
    
    # Verify balances with a small tolerance for gas price fluctuations
    assert abs(from_balance_after["balance"] - expected_from_balance) <= 10**16  # 0.01 ETH tolerance
    assert abs(to_balance_after["balance"] - expected_to_balance) <= 10**16  # 0.01 ETH tolerance
    
    # Clean up
    await delete_account(test_address)

if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v", "-s"]))  # -s 옵션 추가
