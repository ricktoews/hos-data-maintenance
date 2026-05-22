# Hearts of Space Data Pipeline

Pipeline for retrieving Hearts of Space program metadata,
loading it into MySQL, generating OpenAI embeddings,
and supporting semantic search through the hos-search API.

---

## Purpose

This project maintains a local searchable archive of
Hearts of Space program data.

The pipeline:

1. Retrieves raw JSON program data from the HOS API
2. Loads normalized data into MySQL
3. Generates semantic embeddings using OpenAI
4. Supports embedding-based mood and similarity search

The raw JSON is retained locally so the database can
be rebuilt without needing to re-fetch historical data.

---

## Directory Structure

```text
hearts-of-space-data/
├── build_program_embeddings.py
├── fetch_programs.py
├── json/
├── load_new_programs.py
├── README.md
├── requirements.txt
├── scripts/
├── update_hos.sh
└── venv/
```

### Main Scripts

- `fetch_programs.py`
  Retrieves program JSON from the HOS API.

- `load_new_programs.py`
  Loads newly retrieved programs into normalized MySQL tables.

- `build_program_embeddings.py`
  Generates embeddings for programs not yet embedded.

- `update_hos.sh`
  Runs the complete update pipeline.

### Supporting Directories

- `json/`
  Cached raw program JSON files.

- `scripts/`
  Experimental, retired, or utility scripts retained for reference.

- `venv/`
  Python virtual environment.

---

## Running the Full Update Pipeline

From the project directory:

```bash
./update_hos.sh
```

This performs:

1. Fetch latest program JSON
2. Insert new programs into MySQL
3. Generate embeddings for newly inserted programs
4. Restart the `hos-search` service so updated embeddings are loaded into memory

The exact commands are defined in `update_hos.sh`.

---

## Running Individual Steps Manually

Activate the virtual environment first:

```bash
source venv/bin/activate
```

Fetch latest programs:

```bash
python fetch_programs.py
```

Load newly retrieved programs into MySQL:

```bash
python load_new_programs.py
```

Generate embeddings for programs not yet embedded:

```bash
python build_program_embeddings.py
```

Restart the search API service:

```bash
sudo systemctl restart hos-search
```

---

## Cron Job

Weekly automated update:

```cron
1 0 * * 6 /home/rtoews/projects/hearts-of-space-data/update_hos.sh >> /home/rtoews/projects/hearts-of-space-data/update.log 2>&1
```

Runs every Saturday at 12:01 AM.

---

## Virtual Environment

Create:

```bash
python3 -m venv venv
```

Activate:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Configuration

### MySQL Credentials

Stored in:

```text
/etc/hearts-of-space/mysql.json
```

### OpenAI API Key

Stored in:

```text
/etc/hearts-of-space/.openai_key
```

---

## Embeddings

Embedding model:

```text
text-embedding-3-small
```

Embeddings are stored in the `program_embeddings` table.

Programs are embedded only once unless embeddings are manually regenerated.

---

## Notes

- Programs are identified internally by `id`
  and publicly by `program_number`.

- `fetch_programs.py` stops after several consecutive missing program numbers.

- The pipeline is designed to be idempotent:
  rerunning it should not duplicate data.

- Raw JSON retention is intentional and serves as a rebuild/archive layer.
