from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import shutil

app = FastAPI()

DATA_ROOT = Path("/data")

@app.get("/generate/{nc}/{id_run}/{sub_run}")
def generate_dataset(nc: str, id_run: str, sub_run: str):
    target_dir = DATA_ROOT / nc / "c/md/lammps/100" / id_run / "2000" / sub_run
    dump_file = DATA_ROOT / nc / "zca-th300.dump"
    soaps_file = DATA_ROOT / f"{nc}-SOAPS" / "c/md/lammps/100" / id_run / "2000" / sub_run / "SOAPS.vec"

    if not target_dir.exists():
        raise HTTPException(status_code=404, detail="Target run not found")

    archive_path = Path("/tmp") / f"{nc}_{id_run}_{sub_run}.zip"
    with shutil.make_archive(str(archive_path).replace(".zip", ""), 'zip', root_dir=target_dir):
        pass

    # Add extra files manually if needed (like dump and SOAPS)
    shutil.copy(dump_file, target_dir / "zca-th300.dump")
    shutil.copy(soaps_file, target_dir / "SOAPS.vec")

    return FileResponse(path=archive_path, filename=archive_path.name, media_type='application/zip')

