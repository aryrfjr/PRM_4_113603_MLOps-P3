from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import shutil

app = FastAPI(
    title="DataOps API P3",
    description="Prototype API to package and serve raw data files based on (NC, ID_RUN, SUB_RUN) selection. " \
    "It mimics a call to an HPC in the cloud service",
    version="0.1.0"
)

DATA_ROOT = Path("/data/ML/big-data-full")

@app.get(
        "/generate/{nc}/{id_run}/{sub_run}",
        summary="Generate data package",
        description="""
Generate a ZIP archive containing the raw files associated with a given 
nominal composition (NC), run ID, and sub-run.

It includes:
- LAMMPS `.dump` file
- DFT input/output files (`.scf.in`, `.scf.out`)
- Bond strength labels (`ICOHPLIST.lobster`)
- SOAP descriptors (`SOAPS.vec`)

**Returns:** ZIP archive for download.
""",
        response_description="A ZIP archive containing the requested dataset."
)
def generate_dataset(nc: str, id_run: str, sub_run: str):
    """
    Parameters:
    - **nc**: Nominal Composition (e.g., Zr49Cu49Al2)
    - **id_run**: Run ID (e.g., 21)
    - **sub_run**: Sub-run ID (e.g., 0)

    Returns:
    - ZIP file containing data files for the specified identifiers.
    """
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
