"""
Streamlit Web Application: Blockchain-Assisted Secure Image Encryption Dashboard
"""

import io
import os
import requests
import streamlit as st
from PIL import Image

# Page Configuration
st.set_page_config(
    page_title="Blockchain Secure Image Encryption",
    page_icon="🛡️",
    layout="wide"
)

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")


def check_backend_health():
    """Checks the health of the FastAPI backend service."""
    try:
        resp = requests.get(f"{BACKEND_API_URL}/health", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


# Sidebar Navigation & Telemetry
st.sidebar.title("🛡️ Secure Image Hub")
st.sidebar.markdown("**Blockchain-Assisted Confidentiality & Verification**")
st.sidebar.divider()

health_data = check_backend_health()
if health_data:
    st.sidebar.success("Backend: Online (HTTP 200)")
    eth_status = health_data.get("services", {}).get("blockchain", {}).get("connected", False)
    ipfs_status = health_data.get("services", {}).get("storage", {}).get("connected", False)

    if eth_status:
        st.sidebar.success("Blockchain Node: Connected")
    else:
        st.sidebar.warning("Blockchain Node: Offline / Standby")

    if ipfs_status:
        st.sidebar.success("IPFS Daemon: Connected")
    else:
        st.sidebar.warning("IPFS Daemon: Offline / Standby")
else:
    st.sidebar.error("Backend: Offline (Waiting on port 8000)")
    st.sidebar.caption("Run: `python -m uvicorn backend.main:app --port 8000`")

st.sidebar.divider()
st.sidebar.info(
    "**Architecture Standard**: AES-256-GCM, Chaotic Tent Map & Hybrid Chaotic-AES "
    "+ SHA-256 content addressing + Ethereum smart contract access controls."
)

# Header
st.title("Blockchain-Assisted Secure Image Encryption")
st.caption("Cryptographic image protection, decentralized IPFS storage, and immutable on-chain verification.")

# Primary Tabs
tab_upload, tab_verify, tab_access, tab_system = st.tabs([
    "📤 Upload & Encrypt",
    "🔍 Verify & Decrypt",
    "🔑 Access Delegation",
    "⚙️ System Status"
])

# -------------------------------------------------------------
# TAB 1: UPLOAD & ENCRYPT
# -------------------------------------------------------------
with tab_upload:
    st.subheader("1. Ingest, Encrypt & Register Image")
    st.write("Upload an image to encrypt using the selected cipher, compute SHA-256 digest, and store on IPFS.")

    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader("Select Image File (PNG, JPEG, WebP)", type=["png", "jpg", "jpeg", "webp"])
        owner_address = st.text_input(
            "Owner Ethereum Address",
            value="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            help="Public Ethereum address claiming ownership."
        )
        selected_algorithm = st.selectbox(
            "Encryption Algorithm",
            options=["AES-256-GCM", "Hybrid-Chaotic-AES", "Chaotic-Tent-Map"],
            index=0,
            help="AES-256-GCM (default FIPS AEAD), Hybrid-Chaotic-AES (chaotic confusion/diffusion + AES-GCM), or Chaotic-Tent-Map."
        )
        custom_key = st.text_input(
            "Custom 256-bit Key (Hex, Optional)",
            placeholder="Leave blank to automatically generate secure random key",
            type="password"
        )
        upload_button = st.button("Encrypt & Register on Blockchain", type="primary")

    with col2:
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption=f"Original Preview: {uploaded_file.name} ({image.size[0]}x{image.size[1]}px)", use_container_width=True)

    if upload_button:
        if not uploaded_file:
            st.error("Please upload an image file first.")
        elif not owner_address:
            st.error("Owner Ethereum address is required.")
        else:
            with st.spinner("Executing cryptographic encryption & registration pipeline..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {"owner_address": owner_address, "algorithm": selected_algorithm}
                    if custom_key:
                        data["key_hex"] = custom_key

                    resp = requests.post(f"{BACKEND_API_URL}/upload", files=files, data=data, timeout=30)

                    if resp.status_code == 200:
                        result = resp.json()
                        st.success("✅ Image Encrypted & Registered Successfully!")

                        st.json({
                            "Image ID": result["image_id"],
                            "Owner": result["owner"],
                            "SHA-256 Digest": result["image_hash"],
                            "IPFS CID": result["ipfs_cid"],
                            "Blockchain Tx": result.get("transaction_hash") or "Pending Ganache Deployment",
                            "Encryption Algorithm": result["encryption_metadata"]["algorithm"]
                        })

                        st.warning(
                            f"**Save Your Decryption Parameters Securely (Never Shared On-Chain):**\n\n"
                            f"`Algorithm`: `{result['encryption_metadata']['algorithm']}`\n\n"
                            f"`Key (Hex)`: `{result['key_hex']}`\n\n"
                            f"`Nonce (Hex)`: `{result['encryption_metadata']['nonce']}`\n\n"
                            f"`Tag (Hex)`: `{result['encryption_metadata']['tag']}`"
                        )
                    else:
                        st.error(f"Upload failed ({resp.status_code}): {resp.text}")
                except Exception as exc:
                    st.error(f"Could not reach backend service: {exc}")


# -------------------------------------------------------------
# TAB 2: VERIFY & DECRYPT
# -------------------------------------------------------------
with tab_verify:
    st.subheader("2. Integrity Verification & Authorized Decryption")
    st.write("Cross-check IPFS ciphertext against the blockchain record, and decrypt authorized images.")

    v_col1, v_col2 = st.columns([1, 1])

    with v_col1:
        query_image_id = st.text_input("Image ID (bytes32 hex)", placeholder="0x...")
        requester_wallet = st.text_input("Requester Wallet Address", value="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")
        dec_algorithm = st.selectbox(
            "Cipher Algorithm",
            options=["Auto-detect", "AES-256-GCM", "Hybrid-Chaotic-AES", "Chaotic-Tent-Map"],
            index=0,
            help="Select the encryption algorithm used during upload, or Auto-detect from server metadata."
        )
        dec_key = st.text_input("Symmetric Key (Hex)", type="password")
        dec_nonce = st.text_input("Nonce (Hex)")
        dec_tag = st.text_input("Authentication Tag (Hex)")

        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            verify_btn = st.button("Verify Integrity", type="secondary")
        with c_btn2:
            decrypt_btn = st.button("Decrypt Image", type="primary")

    with v_col2:
        if verify_btn and query_image_id:
            with st.spinner("Checking on-chain hash attestation..."):
                try:
                    resp = requests.get(f"{BACKEND_API_URL}/images/{query_image_id}/verify", timeout=15)
                    if resp.status_code == 200:
                        v_res = resp.json()
                        if v_res["is_valid"]:
                            st.success(f"✅ Cryptographic Integrity Verified: {v_res['status']}")
                        else:
                            st.error(f"❌ Integrity Violation: {v_res['status']}")
                        st.json(v_res)
                    else:
                        st.error(f"Verification request failed: {resp.text}")
                except Exception as exc:
                    st.error(f"Service error: {exc}")

        if decrypt_btn:
            if not query_image_id or not dec_key or not dec_nonce or not dec_tag:
                st.error("Please supply Image ID, Key, Nonce, and Tag.")
            else:
                with st.spinner("Authenticating with access control & decrypting..."):
                    try:
                        payload = {
                            "key_hex": dec_key,
                            "nonce_hex": dec_nonce,
                            "tag_hex": dec_tag,
                            "requester_address": requester_wallet
                        }
                        if dec_algorithm != "Auto-detect":
                            payload["algorithm"] = dec_algorithm
                        resp = requests.post(f"{BACKEND_API_URL}/images/{query_image_id}/decrypt", json=payload, timeout=30)
                        if resp.status_code == 200:
                            recovered_img = Image.open(io.BytesIO(resp.content))
                            st.success("✅ Image Authenticated & Decrypted Successfully!")
                            st.image(recovered_img, caption="Recovered Image", use_container_width=True)
                        elif resp.status_code == 403:
                            st.error("⛔ Access Denied: Wallet address is not authorized on-chain.")
                        elif resp.status_code == 400:
                            st.error("❌ Authentication Failed: Corrupted ciphertext or wrong key/tag.")
                        else:
                            st.error(f"Decryption failed ({resp.status_code}): {resp.text}")
                    except Exception as exc:
                        st.error(f"Service error: {exc}")


# -------------------------------------------------------------
# TAB 3: ACCESS DELEGATION
# -------------------------------------------------------------
with tab_access:
    st.subheader("3. Role-Based Access Control Delegation")
    st.write("Grant or revoke decryption rights for other Ethereum wallet addresses on-chain.")

    acl_image_id = st.text_input("Target Image ID", key="acl_img_id")
    target_grantee = st.text_input("Grantee / Revokee Ethereum Address")
    current_owner = st.text_input("Owner Wallet Address", key="acl_owner", value="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")

    act_col1, act_col2 = st.columns(2)
    with act_col1:
        grant_btn = st.button("Grant Permission", type="primary")
    with act_col2:
        revoke_btn = st.button("Revoke Permission", type="secondary")

    if grant_btn and acl_image_id and target_grantee:
        with st.spinner("Submitting permission grant to ledger..."):
            try:
                resp = requests.post(
                    f"{BACKEND_API_URL}/images/{acl_image_id}/grant-access",
                    json={"target_user_address": target_grantee, "owner_address": current_owner},
                    timeout=15
                )
                if resp.status_code == 200:
                    st.success(f"Permission successfully granted to {target_grantee}")
                else:
                    st.error(f"Grant failed: {resp.text}")
            except Exception as exc:
                st.error(f"Service error: {exc}")

    if revoke_btn and acl_image_id and target_grantee:
        with st.spinner("Submitting permission revocation to ledger..."):
            try:
                resp = requests.post(
                    f"{BACKEND_API_URL}/images/{acl_image_id}/revoke-access",
                    json={"target_user_address": target_grantee, "owner_address": current_owner},
                    timeout=15
                )
                if resp.status_code == 200:
                    st.success(f"Permission successfully revoked from {target_grantee}")
                else:
                    st.error(f"Revoke failed: {resp.text}")
            except Exception as exc:
                st.error(f"Service error: {exc}")


# -------------------------------------------------------------
# TAB 4: SYSTEM STATUS
# -------------------------------------------------------------
with tab_system:
    st.subheader("4. Architecture Diagnostics & Environment")
    if health_data:
        st.json(health_data)
    else:
        st.info("FastAPI service is currently offline. Start the backend with: `python -m uvicorn backend.main:app`")
