# Tokamak Layer2 MCP PoC

A Tokamak Layer2 MCP PoC providing Tokamak Networks' Layer2 interaction tools.

## Features

### Account Management
- Create and manage Ethereum accounts
- Get account balances
- Save and retrieve accounts from a database
- Local database storage for account management

### Blockchain Interaction
- Get block information
- Query latest block details
- Get specific block by number
- Async support for better performance

### Devnet Operations
- Create and destroy Devnet instances
- Check instance status
- Automated EC2 instance management
- SSH-based remote command execution

## Performance Metrics

### Devnet Creation Timing Analysis

| Stage | Time Taken | Description |
|-------|------------|-------------|
| **Total Devnet Creation Process** | 157.10s | Total time for Devnet creation and initialization |
| ├─ Devnet Deployment | 138.12s | Contract deployment and initialization time |
| ├─ EC2 Instance Creation | ~10s | EC2 instance creation and startup time |
| ├─ SSH Connection Setup | ~5s | Wait time for SSH connection availability |
| └─ Other Initialization | ~3.98s | Docker permission setup and other tasks |

| **Devnet Deployment Detailed Steps** | Time Taken | Description |
|--------------------------------------|------------|-------------|
| L1 Node Startup | ~30s | Layer 1 node initialization and startup |
| L2 Node Startup | ~40s | Layer 2 node initialization and startup |
| Contract Deployment | ~50s | Smart contract deployment and initialization |
| Account Initialization | ~10s | Developer account creation and ETH allocation |
| Other Configuration | ~8.12s | Permission setup and other configuration tasks |

The timing analysis shows that contract deployment and node initialization processes take up the majority of the Devnet creation time, with L2 node startup and contract deployment accounting for approximately 60% of the total time.

## Requirements

### Python Dependencies
- Python 3.10+
- uv (https://docs.astral.sh/uv/)
- FastMCP (https://github.com/jlowin/fastmcp)
- eth-account
- web3
- tinydb
- python-dotenv
- boto3
- paramiko

### AWS Requirements
- AWS account(IAM) with appropriate permissions
- EC2 instance access permissions(AmazonEC2FullAccess)
- AWS credentials configured(SSH and .pem key)
- security group configurations(Allow port 8545/9545 to anyone)
- devnet compiled AMI(it helps to reduce devnet setup time)

### Environment Setup

#### Blockchain Provider
- `ALCHEMY_API_KEY`: Your Alchemy API key for Ethereum mainnet interaction

#### AWS Configuration
- `IAM_ACCESS_KEY`: AWS access key for EC2 instance management
- `IAM_SECRET_KEY`: AWS secret key for EC2 instance management
- `REGION_NAME`: AWS region (e.g., us-east-1) for EC2 instance deployment
- `IMAGE_ID`: AMI ID for EC2 instance
- `INSTANCE_TYPE`: EC2 instance type (default: t3.large)
- `SECURITY_GROUP_ID`: Security group ID for EC2 instance

#### SSH Configuration
- `SSH_USERNAME`: SSH username for EC2 instance (default: ubuntu)
- `SSH_KEY_NAME`: Name of the SSH key pair for EC2 instance access

Example `.env` file:
```
# Blockchain Provider
ALCHEMY_API_KEY=your_alchemy_api_key_here

# AWS Configuration
IAM_ACCESS_KEY=your_aws_access_key_here
IAM_SECRET_KEY=your_aws_secret_key_here
REGION_NAME=us-east-1
IMAGE_ID=ami-xxxxxxxx
INSTANCE_TYPE=t3.large
SECURITY_GROUP_ID=sg-xxxxxxxx

# SSH Configuration
SSH_USERNAME=ubuntu
SSH_KEY_NAME=your-key-pair-name
```

Note: Make sure to replace placeholder values with your actual configuration values.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp
```

2. Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Create a virtual environment (recommended):
```bash
uv venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
```

4. Install dependencies:
```bash
uv pip sync requirements.txt
```

## Setup

1. Create a `.env` file in the project root directory:
```bash
touch .env
```

2. Add your Alchemy API key to the `.env` file:
```
ALCHEMY_API_KEY=your_alchemy_api_key_here
```

To get an Alchemy API key:
1. Visit [Alchemy](https://www.alchemy.com/)
2. Create an account and create a new app
3. Copy your API key

## Usage

Run the server:
```bash
python main.py
```

## Test
```bash
python -m pytest test/test_main.py -v
```

## How to Set Up in Claude Desktop Client

https://modelcontextprotocol.io/quickstart/user#mac-os-linux

### Available Tools

1. Account Management:
   - `create_account`: Create new Ethereum accounts
   - `save_account`: Save account details to local database
   - `get_all_accounts`: Retrieve all saved accounts
   - `get_account`: Get specific account details
   - `delete_account`: Remove an account from database

2. Blockchain Interaction:
   - `get_balance`: Check ETH balance of an address
   - `get_latest_block`: Get latest block information
   - `get_block_by_number`: Get specific block details
   - `send_transaction`: Send ETH to another address
     - Parameters:
       - `from`: Sender's address
       - `to`: Recipient's address 
       - `value`: Amount of ETH to send in wei

3. Devnet Management:
   - `create_new_devnet`: Create a new Devnet instance
   - `destroy_devnet`: Terminate a Devnet instance
   - `check_instance_status`: Check Devnet instance status

## Security Notes

- Private keys are stored locally in a TinyDB database
- Never share your private keys or .env file
- Keep your database file secure
- Consider using environment variables for sensitive data

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License

Copyright (c) 2024 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.