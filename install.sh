#!/bin/bash

target_dir="$HOME/.claude/skills"
mkdir -p "$target_dir"

for dir in */ ; do
    if [ -d "$dir" ]; then
        ln -sfn "$(realpath "$dir")" "$target_dir/$(basename "$dir")"
    fi
done
