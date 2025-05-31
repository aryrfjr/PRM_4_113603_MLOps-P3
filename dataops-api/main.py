from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import shutil

app = FastAPI()

DATA_ROOT = Path("/data/ML/big-data-full")

@app.get("/generate/{nc}/{id_run}/{sub_run}")
def generate_dataset(nc: str, id_run: str, sub_run: str):
    target_dir = DATA_ROOT / nc / "c/md/lammps/100" / id_run / "2000" / sub_run
    dump_file = DATA_ROOT / nc / "zca-th300.dump"
    soaps_file = DATA_ROOT / f"{nc}-SOAPS" / "c/md/lammps/100" / id_run / "2000" / sub_run / "SOAPS.vec"

    if not target_dir.exists():
        raise HTTPException(status_code=404, detail="Target run not found")

    temp_dir = Path("/tmp") / f"{nc}_{id_run}_{sub_run}"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    # Copy the directory contents
    for item in target_dir.iterdir():
        shutil.copy(item, temp_dir)

    # Copy extra files (dump and SOAP)
    if dump_file.exists():
        shutil.copy(dump_file, temp_dir)
    if soaps_file.exists():
        shutil.copy(soaps_file, temp_dir)

    # Create ZIP archive
    archive_path = shutil.make_archive(str(temp_dir), 'zip', root_dir=temp_dir)

    return FileResponse(
        path=archive_path,
        filename=Path(archive_path).name,
        media_type='application/zip'
    )
