import requests
import time
from pathlib import Path
import zipfile
import io

API_URL = "http://dataops-api:8000/generate/Zr49Cu49Al2/21/0"

output_dir = Path("/app/output")
output_dir.mkdir(parents=True, exist_ok=True)

for attempt in range(10):
    try:
        print(f"[Attempt {attempt + 1}] Connecting to {API_URL} ...")
        response = requests.get(API_URL)

        if response.status_code == 200:
            z = zipfile.ZipFile(io.BytesIO(response.content))
            z.extractall(output_dir)
            print(f"[SUCCESS] Files extracted to {output_dir.resolve()}")
            break
        else:
            print(f"[ERROR] API responded with status {response.status_code}")
            time.sleep(3)
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection failed: {e}")
        time.sleep(3)
else:
    print("[FAILED] Could not connect to API after multiple attempts.")
