#!/bin/bash

cd /home/rtoews/projects/hearts-of-space-data

source venv/bin/activate

python fetch_programs.py
python load_new_programs.py
python build_program_embeddings.py

sudo systemctl restart hos-search
