# PRM_4_113603_MLOps-P3: DataOps API Prototype

## 🛠 Overview

A simple, containerized prototype for a **DataOps API service** that packages and serves raw dataset files used in computational materials science or machine learning pipelines. It mimics a call to an HPC in the cloud service and includes:

- A **FastAPI-based API** that bundles files into ZIP archives based on dataset identifiers (`<NC>`, `<ID_RUN>`, `<SUB_RUN>`).
- A **client service** that fetches the ZIP archive via HTTP and extracts it.
- Fully managed via **Docker Compose**, simulating a microservices architecture.

All services are containerized with Docker Compose for reproducibility.

---

## 🧠 How It Works

### 🔸 **dataops-api**
- A REST API built with FastAPI.
- When called with a dataset identifier (`nc`, `id_run`, `sub_run`), it:
  - Searches the `/data` directory for relevant files.
  - Packages the following into a ZIP archive:
    - LAMMPS `.dump` files
    - DFT input/output files (`.scf.in`, `.scf.out`)
    - Bond strength label files (`ICOHPLIST.lobster`)
    - SOAP descriptor files (`SOAPS.vec`)
  - Returns the ZIP archive via HTTP.

- 📚 Swagger UI for API exploration available at:  
  `http://localhost:8000/docs`

---

### 🔸 **data-client**
- A simple Python client that:
  - Connects to the API.
  - Downloads the ZIP archive for a specific dataset.
  - Extracts the contents into the local `./client_output` directory.

- ⚠️ The DataOps endpoint expects files to be placed in the `./data` folder following the same structure used in https://github.com/aryrfjr/PRM_4_113603:
```
./data/
├── Zr49Cu49Al2/
│   ├── zca-th300.dump
│   └── c/md/lammps/100/21/2000/0/   # DFT outputs here
│       ├── Zr49Cu49Al2.scf.in
│       ├── Zr49Cu49Al2.scf.out
│       ├── ICOHPLIST.lobster
│       └── (other files)
├── Zr49Cu49Al2-SOAPS/
│   └── c/md/lammps/100/21/2000/0/SOAPS.vec
```
