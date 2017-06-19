#!/bin/bash

if [ $# -lt 1 ]
then
    echo "Usage: $0 inotifywait-arg [inotifywait-arg ...]" >&2
    echo "Examples:" >&2
    echo "  $0 -r foo/bar" >&2
    echo "  $0 -r foo/bar/baz" >&2
    exit 1
fi

set -e

inotifywait --format '%w%f' -m -e close_write "$@" | \
    while read path
    do
        gdcp.py push $path
    done
