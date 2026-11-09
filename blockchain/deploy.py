"""
Smart Contract Compilation and Deployment Script

Compiles ImageRegistry.sol and deploys the contract to an EVM blockchain (Ganache).
Outputs the compiled ABI and bytecode artifact to blockchain/contracts/ImageRegistry.json.
"""

import os
import json
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()


def compile_and_deploy():
    """Compiles ImageRegistry.sol and deploys to the configured Web3 provider."""
    rpc_url = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    print(f"Connecting to Ethereum RPC endpoint: {rpc_url}")
    if not w3.is_connected():
        print("[ERROR] Cannot connect to Ethereum node. Please ensure Ganache is running.")
        return None

    deployer_account = os.getenv("DEPLOYER_ADDRESS") or w3.eth.accounts[0]
    deployer_pk = os.getenv("DEPLOYER_PRIVATE_KEY")
    print(f"Deployer account: {deployer_account}")

    contracts_dir = Path(__file__).parent / "contracts"
    sol_file = contracts_dir / "ImageRegistry.sol"

    if not sol_file.exists():
        raise FileNotFoundError(f"Solidity file not found: {sol_file}")

    print("Compiling ImageRegistry.sol...")
    try:
        import solcx
        # Ensure solc 0.8.20 is installed
        installed = solcx.get_installed_solc_versions()
        solc_ver = "0.8.20"
        if solc_ver not in [str(v) for v in installed]:
            print(f"Installing solc {solc_ver}...")
            solcx.install_solc(solc_ver)
        solcx.set_solc_version(solc_ver)

        compiled_sol = solcx.compile_files(
            [str(sol_file)],
            output_values=["abi", "bin"]
        )
        contract_key = f"{sol_file}:ImageRegistry"
        contract_interface = compiled_sol[contract_key]
        abi = contract_interface["abi"]
        bytecode = contract_interface["bin"]
    except Exception as exc:
        print(f"[WARN] solcx direct compilation failed ({exc}). Using pre-compiled standard artifact if available.")
        from blockchain.blockchain_service import IMAGE_REGISTRY_ABI
        abi = IMAGE_REGISTRY_ABI
        bytecode = None

    if not bytecode:
        print("[ERROR] Bytecode not available for deployment. Ensure solcx is installed and solc compiler is available.")
        return None

    # Save artifact
    artifact_path = contracts_dir / "ImageRegistry.json"
    with open(artifact_path, "w") as f:
        json.dump({"abi": abi, "bytecode": bytecode}, f, indent=2)
    print(f"Saved contract artifact to: {artifact_path}")

    # Deploy contract
    print("Deploying ImageRegistry contract...")
    contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)

    if deployer_pk:
        nonce = w3.eth.get_transaction_count(deployer_account)
        tx_build = contract_factory.constructor().build_transaction({
            "from": deployer_account,
            "nonce": nonce,
            "gas": 2500000,
            "gasPrice": w3.eth.gas_price
        })
        signed = w3.eth.account.sign_transaction(tx_build, private_key=deployer_pk)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    else:
        tx_hash = contract_factory.constructor().transact({"from": deployer_account, "gas": 2500000})

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = receipt.contractAddress
    print(f"[SUCCESS] Contract deployed successfully!")
    print(f"Contract Address: {contract_address}")
    print(f"Transaction Hash: {tx_hash.hex()}")
    print(f"Block Number: {receipt.blockNumber}")
    print("\nAdd the following to your .env file:")
    print(f"IMAGE_REGISTRY_CONTRACT_ADDRESS={contract_address}")

    return contract_address


if __name__ == "__main__":
    compile_and_deploy()
