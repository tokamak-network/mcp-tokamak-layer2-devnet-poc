# my_server.py
import secrets
import asyncio
import os
import logging

from typing import Literal, Dict, Any
from datetime import datetime
from fastmcp import FastMCP, Context

from eth_account import Account
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware

from tinydb import TinyDB, Query

from ec2 import (
    get_ec2_instance_public_ip,
    get_ec2_instance,
    wait_for_instance_state,
    create_ec2_instance,
    terminate_ec2_instance,
    get_ec2_instance_public_ip,
)

from ssh import (
    wait_for_ssh_ready,
    exec_command,
    exec_command_interactive,
)

from dotenv import load_dotenv
from os.path import join, dirname

from eth_utils import to_hex
from hexbytes import HexBytes

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

db = TinyDB("db.json")

mcp = FastMCP(
    name="MyServer"
)

def get_web3(url: str, type:Literal["Layer1", "Layer2"]="Layer2"):
    if type == "Layer2":
        return AsyncWeb3(AsyncHTTPProvider(url))
    else:
        w3 = AsyncWeb3(AsyncHTTPProvider(url))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware(), layer=0)
        return w3



@mcp.tool()
async def get_balance(address: str, url: str=ALCHEMY_URL, type:Literal["Layer1", "Layer2"]="Layer2") -> dict:
    """Get the balance of an Ethereum address."""
    if type == "Layer2":
        w3 = AsyncWeb3(AsyncHTTPProvider(url))
    else:
        w3 = AsyncWeb3(AsyncHTTPProvider(url))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware(), layer=0)
    balance = await w3.eth.get_balance(address)
    return {
        "address": address,
        "balance": balance
    }

@mcp.tool()
async def create_account(number_of_accounts: int=1) -> dict:
    """Create a new Ethereum account."""
    accounts = []
    for i in range(number_of_accounts):
        private_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(private_key)
        accounts.append({"address": account.address, "private_key": private_key})
    return accounts

@mcp.tool()
async def create_account_from_mnemonic(mnemonic: str, index: int=0, passphrase: str="") -> dict:
    """Create a new Ethereum account from a mnemonic."""
    Account.enable_unaudited_hdwallet_features()
    path = f"m/44'/60'/0'/0/{index}"
    account = Account.from_mnemonic(mnemonic, passphrase, path)
    return {
        "address": account.address,
        "private_key": "0x" + account.key.hex()
    }

@mcp.tool()
async def save_account(address: str, private_key: str) -> dict:
    """Save an Ethereum account to the database."""
    db.insert(
        {
            "address": address,
            "private_key": private_key,
            "type": "account",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    return {"message": "Account saved successfully"}

@mcp.tool()
async def save_many_accounts(accounts: list[dict]) -> dict:
    """Save multiple Ethereum accounts to the database."""
    db.insert_multiple(accounts)
    return {"message": "Accounts saved successfully"}

@mcp.tool()
async def get_all_accounts() -> list:
    """Get all Ethereum accounts from the database."""
    return db.search(Query().type == "account")

@mcp.tool()
async def get_account(address: str) -> dict:
    """Get an Ethereum account from the database."""
    return db.search(Query().address == address)

@mcp.tool()
async def delete_account(address: str) -> dict:
    """Delete an Ethereum account from the database."""
    Account = Query()
    removed = db.remove(Account.address == address)
    if removed:
        return {"message": f"Account {address} deleted successfully"}
    return {"message": f"Account {address} not found"}

@mcp.tool()
async def get_all_transactions() -> list:
    """Get all Ethereum transactions from the database."""
    return db.search(Query().type == "transaction")

@mcp.tool()
async def send_transaction(
    from_private_key: str,
    to_address: str,
    amount_ether: float,
    type: str = "Layer2",
    url: str = ALCHEMY_URL
) -> Dict[str, Any]:
    """
    Send a transaction between accounts.
    
    Args:
        from_private_key: Private key of the sender account
        to_address: Address of the recipient
        amount_ether: Amount of ETH to send
        type: Network type ("Layer1" or "Layer2")
        
    Returns:
        Dict containing transaction details
    """
    try:
        w3 = get_web3(url, type)
        
        # Create account from private key
        account = Account.from_key(from_private_key)
        address_from = account.address
        
        # Convert amount to Wei
        amount_wei = w3.to_wei(amount_ether, 'ether')
        
        #get gas price
        gas_price = await w3.eth.gas_price
        
        # Get nonce
        nonce = await w3.eth.get_transaction_count(address_from)
        
        # Get chain ID
        chain_id = await w3.eth.chain_id

        gas_limit = 200000  # Reduced from 200000
        
        # Use dynamic maxFeePerGas based on current gas price
        max_fee_per_gas = min(gas_price * 2, 2000000000)  # Cap at 2 Gwei
        
        tx_raw = {
            'from': address_from,
            'to': to_address,
            'value': amount_wei,
            'nonce': nonce,
            'gas': gas_limit,
            'maxFeePerGas': max_fee_per_gas,
            'maxPriorityFeePerGas': 1000000000, # 1 Gwei
            'chainId': chain_id
        }
        
        # Sign transaction
        signed_tx = w3.eth.account.sign_transaction(tx_raw, from_private_key)
        
        # Send transaction
        tx_hash = await w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Wait for transaction receipt
        receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)

        # Convert receipt to dictionary
        receipt_dict = dict(receipt)
        # Convert hex values to strings
        for key, value in receipt_dict.items():
            if isinstance(value, (bytes, HexBytes)):
                receipt_dict[key] = value.hex()

        db.insert({
            "type": "transaction",
            "tx": tx_raw,
            "receipt": receipt_dict,
            "hash": to_hex(tx_hash),
            "status": "success",
            "layer": type,
        })
        
        return {
            "tx": {
                "from": address_from,
                "to": to_address,
                "value": amount_wei,
                "gas": gas_limit,
                "gasPrice": gas_price,
                "hash": to_hex(tx_hash),
                "block_number": receipt.blockNumber,
                "gas": receipt.gasUsed,
                "gasPrice": gas_price
            },
            "hash": to_hex(tx_hash),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Transaction failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@mcp.tool()
async def get_latest_block(url: str=ALCHEMY_URL, type:Literal["Layer1", "Layer2"]="Layer2") -> dict:
    """Get the latest Ethereum block information."""

    w3 = get_web3(url, type)
    
    # Get latest block
    block = await w3.eth.get_block('latest')
    
    return {
        "block_number": block.number,
        "timestamp": block.timestamp,
        "miner": block.miner,
        "difficulty": block.difficulty,
        "total_transactions": len(block.transactions),
        "gas_used": block.gasUsed,
        "gas_limit": block.gasLimit,
        "base_fee_per_gas": block.baseFeePerGas,
        "hash": block.hash.hex()
    }

@mcp.tool()
async def get_block_by_number(block_number: int, url: str=ALCHEMY_URL, type:Literal["Layer1", "Layer2"]="Layer2") -> dict:
    """Get information about a specific block number."""
    w3 = get_web3(url, type)
    
    # Get block by number
    block = await w3.eth.get_block(block_number)
    
    return {
        "block_number": block.number,
        "timestamp": block.timestamp,
        "miner": block.miner,
        "difficulty": block.difficulty,
        "total_transactions": len(block.transactions),
        "gas_used": block.gasUsed,
        "gas_limit": block.gasLimit,
        "base_fee_per_gas": block.baseFeePerGas,
        "hash": block.hash.hex()
    }

@mcp.tool()
async def create_new_devnet(name: str, ctx: Context = None) -> dict:
    """Create a new Devnet Layer1 instance.
    
    Args:
        name: Name of the devnet instance
        ctx: MCP Context object, automatically provided when called from MCP client
             (e.g., Claude Desktop). None when called from regular Python code.
    """
    # Helper function to handle progress reporting
    # Uses Context.report_progress when available (MCP client calls)
    # Falls back to regular logging when Context is None (direct Python calls)
    def log_progress(message: str):
        if ctx:
            asyncio.create_task(ctx.report_progress(message))
        logger.info(message)

    instance_id = create_ec2_instance(name)
    log_progress(f"Created EC2 instance: {instance_id}")
    
    wait_result = wait_for_instance_state(instance_id, "running")
    log_progress(f"Instance state change result: {wait_result}")
    
    public_ip = get_ec2_instance_public_ip(instance_id)
    log_progress(f"Got public IP: {public_ip}")
    
    ssh_ready = wait_for_ssh_ready(public_ip)
    log_progress(f"SSH ready result: {ssh_ready}")
    
    docker_permission = exec_command(public_ip, "sudo chmod 666 /var/run/docker.sock")
    log_progress(f"Docker permission result: {docker_permission}")
    
    deploy_result = exec_command_interactive(public_ip, "trh-sdk deploy")
    log_progress(f"Deploy result: {deploy_result}")
    
    devnet = {
        "type": "devnet",
        "name": name,
        "instance_id": instance_id,
        "public_ip": public_ip,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "layer1_url": f"http://{public_ip}:8545",
        "layer2_url": f"http://{public_ip}:9545",
    }
    db.insert(devnet)
    return devnet

@mcp.tool()
async def destroy_devnet(instance_id: str) -> dict:
    """Destroy a Devnet instance."""
    devnet = db.search(Query().instance_id == instance_id)
    if not devnet:
        return {"message": f"Devnet instance {instance_id} not found"}
    
    destroy_result = exec_command(devnet[0]["public_ip"], "trh-sdk destroy")
    logger.info(f"Destroy result: {destroy_result}")
    
    terminate_result = terminate_ec2_instance(instance_id)
    logger.info(f"Terminate result: {terminate_result}")
    
    db.update({'status': 'terminated'}, Query().instance_id == instance_id)
    return {"message": f"Devnet instance {instance_id} destroyed successfully"}

@mcp.tool()
async def check_instance_status(instance_id: str) -> dict:
    """Check the status of an EC2 instance."""
    instance = get_ec2_instance(instance_id)
    return {
        "instance_id": instance_id,
        "state": instance.state["Name"],
        "public_ip": instance.public_ip_address if instance.public_ip_address else None
    }

@mcp.tool()
async def devnet(instance_id: str) -> dict:
    """Get a Devnet instance."""
    return db.search(Query().instance_id == instance_id)

@mcp.tool()
async def list_all_devnets() -> list:
    """Get all Devnet instances."""
    return db.search(Query().type == "devnet")

#TODO : transaction 조회 기능 추가


async def main():
    await mcp.run_async(transport="stdio")

# if __name__ == "__main__":
#     mcp.run(transport="stdio")
    
    # To use a different transport, e.g., HTTP:
    # mcp.run(transport="streamable-http", host="127.0.0.1", port=9000)

if __name__ == "__main__":
    asyncio.run(main())