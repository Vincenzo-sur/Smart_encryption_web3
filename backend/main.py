"""
FastAPI Application Entry Point

Bootstraps the REST API gateway, mounts CORS middleware, registers routers,
and exposes health monitoring endpoints.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.routes.image_routes import router as image_router
from blockchain.blockchain_service import BlockchainService
from storage.ipfs_service import IPFSService

load_dotenv()

app = FastAPI(
    title="Blockchain-Assisted Secure Image Encryption API",
    description="Enterprise REST API for AES-256-GCM image encryption, IPFS storage, and Ethereum integrity verification.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service singletons for health diagnostics
blockchain_svc = BlockchainService()
ipfs_svc = IPFSService()


@app.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint probing Ethereum RPC and IPFS daemon availability."""
    eth_connected = blockchain_svc.is_connected()
    ipfs_connected = ipfs_svc.is_connected()

    return {
        "status": "HEALTHY",
        "services": {
            "blockchain": {
                "connected": eth_connected,
                "rpc_url": blockchain_svc.rpc_url,
                "contract_configured": bool(blockchain_svc.contract_address)
            },
            "storage": {
                "connected": ipfs_connected,
                "api_url": ipfs_svc.api_url,
                "gateway_url": ipfs_svc.gateway_url
            }
        },
        "environment": os.getenv("ENVIRONMENT", "development")
    }


# Mount API Routes
app.include_router(image_router)


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "127.0.0.1")
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
