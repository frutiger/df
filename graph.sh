#!/bin/bash

echo "digraph Profiles {"
find . -maxdepth 1 -type d | cut -c3- | while read profile; do
    if [ -f "$profile/parents" ]; then
        cat "$profile/parents" | while read parent; do
            echo "  \"$profile\" -> \"$parent\""
        done
    fi
done
echo "}"
