#!/bin/bash

duration=0
pages=0

function show_help {
  echo "Usage: $0 [-d DURATION] PAGES"
}

while getopts "hd:" opt; do
    case "$opt" in
    h)  show_help
        exit 0
        ;;
    d)  duration=$OPTARG
        ;;
    esac
done

shift $((OPTIND-1))

[ "$1" = "--" ] && shift

if [ -z "$1" ]; then
  show_help
  exit 0
fi

bytes=$(("$1" * 4096))

exec stress-ng --vm-bytes ${bytes} --vm-keep --vm 1 --vm-rw 1 -t ${duration}

