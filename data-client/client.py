import requests
import zipfile
import io
from pathlib import Path

API_URL = "http://dataops-api:8000/generate/Zr49Cu49Al2/21/0"

response = requests.get(API_URL)
if response.status_code == 200:
    z = zipfile.ZipFile(io.BytesIO(response.content))
    extract_path = Path("/app/output")
    extract_path.mkdir(parents=True, exist_ok=True)
    z.extractall(extract_path)
    print(f"Files extracted to {extract_path}")
else:
    print(f"Failed to fetch data: {response.status_code}")

