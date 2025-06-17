#!/bin/bash

# List of target directories
folders=("embeddings" "sec-edgar-filings" "tmp" "logs")

for dir in "${folders[@]}"; do
  if [ -d "$dir" ]; then
    echo "Cleaning $dir..."
    find "$dir" -mindepth 1 ! -name '.gitignore' -exec rm -rf {} +
  else
    echo "Directory $dir does not exist."
  fi
done
