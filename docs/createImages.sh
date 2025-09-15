#!/bin/zsh

for file in *.mmd; do
    echo "Converting $file..."
    mmdc -i "$file" -o "${file%.mmd}.png" -t neutral -b white
  done
