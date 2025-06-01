from fastapi import FastAPI, Path, HTTPException, status, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pathlib import Path as FilePath
import shutil
import json

##########################################################################
#
# Globals
#
##########################################################################

app = FastAPI(
    title="DataOps API (P3)",
    description="Prototype API to package and serve raw data files based on (NC, ID_RUN, SUB_RUN) selection. " \
    "It mimics calls to an HPC in the cloud service.",
    version="0.1.0"
)

DATA_ROOT = FilePath("/data/ML/big-data-full")
DB_AVAILABLE_RUNS_FILE = FilePath("/tmp/available_runs.json")

if DB_AVAILABLE_RUNS_FILE.exists():
    AVAILABLE_RUNS = json.loads(DB_AVAILABLE_RUNS_FILE.read_text())
else:
    AVAILABLE_RUNS = {}  # {"Zr49Cu49Al2": [{"id_run":"1", "sub_runs":["0", "1"]]}, {"id_run":"2", "sub_runs":["0"]}]}

NC_FIELD_DESC = "The NC for which raw data generation is requested"
NC_FIELD_EXAMPLE = "Zr49Cu49Al2"
ID_RUN_FIELD_DESC = "Unique identifier string that represents the scheduled run"
ID_RUN_FIELD_EXAMPLE = "21"
SUB_RUN_FIELD_DESC = "Unique identifier string that represents a sub-run of a scheduled run"
SUB_RUN_FIELD_EXAMPLE = "8"
STATUS_SCHEDULED = "SCHEDULED"

##########################################################################
#
# Subroutines
#
##########################################################################

##########################################################################
#
# Endpoints for different resources types and scopes
#
# TODO: review status codess
#
# TODO: review error handling: consistent and descriptive error responses,
#  with machine-readable codes and human-readable messages.
#
##########################################################################

class NCDataGenerationRequest(BaseModel):
    nc: str = Field(..., description=NC_FIELD_DESC, example=NC_FIELD_EXAMPLE)
class NCDataGenerationResponse(BaseModel):
    nc: str = Field(..., description=NC_FIELD_DESC, example=NC_FIELD_EXAMPLE)
    id_run: str = Field(..., description=ID_RUN_FIELD_DESC, example=ID_RUN_FIELD_EXAMPLE)
    status: str = Field(..., example=STATUS_SCHEDULED)

@app.post(
        "/v1/generate/{nc}",
        response_model=NCDataGenerationResponse,
        status_code=status.HTTP_200_OK,
        summary="Schedules the generation raw data for a given nominal composition (NC)",
        description="""
        Schedules the generation of a 100-atom cell with random distribution of atoms for a given 
        NC with a Classical Molecular Dynamics (CMD) simulation, as well as 
        all additional atomistic simulations for the generation of training raw data.
        It will generate all input and output files for the atomistic simulations with LAMMPS, 
        electronic structure with Quantum ESPRESSO (DFT), LOBSTER (bond strength labels), and 
        QUIP+quippy (SOAP descriptors).
        """,
        responses={
                404: {"description": "NC not found or no more raw data available"},
                200: {"description": "Calculations successfully scheduled for NC"},
        }
)
async def schedule_nc_raw_data_generation(
    nc: str = Path(..., description=NC_FIELD_DESC)
):
    
    # Extract existing id_run values and convert to integers
    existing_id_runs = [int(run["id_run"]) for run in AVAILABLE_RUNS.get(nc, [])]

    # Find the next id_run
    next_id_run = str(max(existing_id_runs, default=0) + 1) # TODO: non-sequential integer ID_RUN numbers

    nc_dir = DATA_ROOT / nc
    nc_id_run_dir = nc_dir / "c/md/lammps/100" / next_id_run
    nc_sub_run_dir = nc_id_run_dir  / "2000/0"

    if not nc_dir.exists():
        raise HTTPException(
            status_code=404, detail=f"Directory for nominal composition (ND) '{nc}' not found"
        )

    if not nc_id_run_dir.exists() or not nc_sub_run_dir.exists():
        raise HTTPException(
            status_code=404, detail=f"Directory for ID_RUN '{next_id_run}' or for SUB_RUN '0' not found for NC '{nc}'"
        )

    # Schedule for SUB_RUN 0
    AVAILABLE_RUNS.setdefault(nc, []).append({"id_run":next_id_run, "sub_runs": ["0"]})

    # Persist to file
    DB_AVAILABLE_RUNS_FILE.write_text(json.dumps(AVAILABLE_RUNS, indent=2))

    return {
        "nc": nc,
        "id_run": next_id_run,
        "status": STATUS_SCHEDULED
    }

##########################################################################

class NCDataAugmentationRequest(BaseModel):
    nc: str = Field(..., description=NC_FIELD_DESC, example=NC_FIELD_EXAMPLE)
    id_run: str = Field(..., description=ID_RUN_FIELD_DESC, example=ID_RUN_FIELD_EXAMPLE)
class NCDataAugmentationResponse(BaseModel):
    nc: str = Field(..., description=NC_FIELD_DESC, example=NC_FIELD_EXAMPLE)
    id_run: str = Field(..., description=ID_RUN_FIELD_DESC, example=ID_RUN_FIELD_EXAMPLE)
    status: str = Field(..., example=STATUS_SCHEDULED)

@app.post(
        "/v1/generate/{nc}/{id_run}/augment",
        response_model=NCDataAugmentationResponse,
        status_code=status.HTTP_200_OK,
        summary="Schedules data augmentation for a given nominal composition (NC)",
        description="""
        Schedules data augmentation to increase structural diversity for a given 
        NC. This is achieved by applying geometric transformations 
        (shear, tension, compression) to the 100-atom cell in SUB_RUN 0.
        It will generate all input and output files for the atomistic simulations with LAMMPS, 
        electronic structure with Quantum ESPRESSO (DFT), LOBSTER (bond strength labels), and 
        QUIP+quippy (SOAP descriptors).
        """,
        responses={
                404: {"description": "NC or ID_RUN not found"},
                200: {"description": "Calculations successfully scheduled for NC"},
        }
)
def augment_nc_id_run(
    nc: str = Path(..., description=NC_FIELD_DESC),
    id_run: str = Path(..., description=ID_RUN_FIELD_DESC)
): # TODO: allow user pass the set of SUB_RUNs to be added; instead of adding 1 to 14

    # Check if the requested RUN_ID is available
    run_entry = next((run for run in AVAILABLE_RUNS.get(nc, []) if run["id_run"] == id_run), None)

    if run_entry == None:
        raise HTTPException(status_code=404, detail=f"NC '{nc}' or ID_RUN '{id_run}' not available")

    # Scheduling sub-runs from 1 to 14
    nc_sub_run_dir = DATA_ROOT / nc / "c/md/lammps/100" / id_run / "2000"

    if not nc_sub_run_dir.exists():
        raise HTTPException(
            status_code=404, detail=f"Directory for SUB_RUNs not found for NC '{nc}' and ID_RUN '{id_run}'"
        )

    # NOTE: set() inherently removes duplicates
    current_sub_runs = set(run_entry.get("sub_runs", []))

    new_sub_runs = {str(i) for i in range(1, 15)}

    # NOTE: .union() merges the two sets but keeps only unique values
    run_entry["sub_runs"] = sorted(current_sub_runs.union(new_sub_runs), key=int)

    # Persist to file
    DB_AVAILABLE_RUNS_FILE.write_text(json.dumps(AVAILABLE_RUNS, indent=2))

    return {
        "nc": nc,
        "id_run": id_run,
        "status": STATUS_SCHEDULED
    }

##########################################################################

@app.get(
        "/v1/generate/{nc}/{id_run}/{sub_run}",
        status_code=status.HTTP_200_OK,
        summary="Generates raw data package for a given nominal composition (NC), run ID (ID_RUN), and sub-run (SUB_RUN)",
        description="""
        Generates a ZIP archive containing the raw files associated with a given 
        NC, ID_RUN, and SUB_RUN.
        It includes: (i) DFT input/output files (**.scf.in**, **.scf.out**); (ii) Bond strength labels (**ICOHPLIST.lobster**); 
        (iii) SOAP descriptors (**SOAPS.vec**). **Returns:** ZIP archive for download.
        """,
        responses={
                404: {"description": "SUB_RUN not found for nominal composition (NC)"},
                200: {"description": "ZIP archive containing the requested dataset successfully generated"},
        }
)
def get_generated_nc_raw_data(
    nc: str = Path(..., description=NC_FIELD_DESC),
    id_run: str = Path(..., description=ID_RUN_FIELD_DESC),
    sub_run: str = Path(..., description=SUB_RUN_FIELD_DESC)
):

    # Check if the requested SUB_RUN is available
    run_entry = next((run for run in AVAILABLE_RUNS.get(nc, []) if run["id_run"] == id_run), None)

    if run_entry == None:
        raise HTTPException(status_code=404, detail=f"NC '{nc}' or ID_RUN '{id_run}' not available")

    sub_run_exists = sub_run in run_entry["sub_runs"] if run_entry else False

    if not sub_run_exists:
        raise HTTPException(status_code=404, detail=f"SUB_RUN '{sub_run}' is not available for NC '{nc}', ID_RUN '{id_run}'")

    # Collecting files
    target_dir = DATA_ROOT / nc / "c/md/lammps/100" / id_run / "2000" / sub_run
    soaps_file = DATA_ROOT / f"{nc}-SOAPS" / "c/md/lammps/100" / id_run / "2000" / sub_run / "SOAPS.vec"

    if not target_dir.exists():
        raise HTTPException(status_code=404, detail="Target sub-run not found")

    temp_dir = FilePath("/tmp") / f"{nc}_{id_run}_{sub_run}"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    # Copy the directory contents
    for item in target_dir.iterdir():
        shutil.copy(item, temp_dir)

    # Copy SOAPs file
    if soaps_file.exists():
        shutil.copy(soaps_file, temp_dir)

    # Create ZIP archive
    archive_path = shutil.make_archive(str(temp_dir), 'zip', root_dir=temp_dir)

    return FileResponse(
        path=archive_path,
        filename=FilePath(archive_path).name,
        media_type='application/zip'
    )

##########################################################################

@app.get(
        "/v1/generate/available",
        status_code=status.HTTP_200_OK,
        summary="Returns the full set of available raw data",
        description="""
        **Returns** the full set of available raw data.
        """
)
def get_available_raw_data(): # TODO: support for pagination/filtering
    return AVAILABLE_RUNS
