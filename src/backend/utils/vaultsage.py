import os
import httpx

VAULTSAGE_API_KEY = os.environ.get("VAULTSAGE_API_KEY")

def get_or_create_directory(vaultsage_path: str) -> str:
    if not VAULTSAGE_API_KEY:
        return None
    target_directory_id = None
    try:
        dirs_res = httpx.get(
            "https://api.vaultsage.ai/api/v1/directories/",
            headers={"X-Api-Key": VAULTSAGE_API_KEY},
            timeout=30.0
        )
        if dirs_res.status_code == 200:
            dirs_data = dirs_res.json().get("data", [])
            for d in dirs_data:
                if d.get("directory_name") == vaultsage_path:
                    target_directory_id = d.get("directory_id")
                    break
        if not target_directory_id:
            create_res = httpx.post(
                "https://api.vaultsage.ai/api/v1/directories/",
                headers={"X-Api-Key": VAULTSAGE_API_KEY},
                json={"directory_name": vaultsage_path},
                timeout=30.0
            )
            if create_res.status_code == 200:
                target_directory_id = create_res.json().get("directory_id")
    except Exception as e:
        print("Failed to get or create VaultSage directory:", e)
    return target_directory_id

def upload_file_to_vaultsage(filename: str, content: bytes, content_type: str, directory_id: str) -> bool:
    if not VAULTSAGE_API_KEY:
        return False
    try:
        upload_url = "https://api.vaultsage.ai/api/v1/files/"
        if directory_id:
            upload_url += f"?directory_id={directory_id}"
            
        res = httpx.post(
            upload_url,
            headers={"X-Api-Key": VAULTSAGE_API_KEY},
            files=[('files', (filename, content, content_type))],
            timeout=360.0
        )
        print(f"VaultSage upload status for {filename}: {res.status_code}")
        return res.status_code == 200 or res.status_code == 201
    except Exception as e:
        print(f"Failed to upload {filename} to Vaultsage: {e}")
        return False
