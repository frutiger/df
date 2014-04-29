#!/bin/bash

if [[ $# < 1 ]]; then
    echo "Usage: $0 -c [ <platform> | reset ]"
    echo "   -c: This is a child run (do not reset)"
    exit
fi

childrun=0
while getopts "c" option; do
    case $option in
        c) childrun=1
           shift ;;
    esac
done

dir=$(dirname $0)
platform=$1
sourcedir=$dir/$platform
if [ $TARGETDIR ]; then targetdir=$TARGETDIR; else targetdir=$(echo ~); fi
datafile=$targetdir/.dotfiles.data
if [ ! -f $datafile ]; then
    touch $datafile
fi

function is_managed() {
    grep -q "^$1$" $datafile
    return $?
}

function manage() {
    if is_managed $1; then
        return
    fi

    echo "$1" >> $datafile
}

function rmemptydir() {
    if [ -z $(find "$1/" -type f -print -quit 2>/dev/null) ]; then
        rmemptydir $(dirname "$1")
    fi
}

function reset() {
    cat $datafile | while read file; do
        target="$targetdir/$file"
        if [ -e "$target" ]; then
            rm -r "$target"
            rmemptydir $(dirname "$target")
        fi
    done
    rm $datafile
}

if [ $1 = "reset" ]; then
    reset
    exit
fi

if [ $childrun == 0 ]; then
    reset
fi

if [ ! -d $sourcedir ]; then
    echo "Usage: $0 [ <platform> | reset ]"
    echo
    echo "Valid platforms:"
    find $dir -maxdepth 1 -type d | while read p; do
        platform=$(basename "$p")
        if ! [[ "$platform" =~ \. ]]; then
            echo "$platform"
        fi
    done

    exit
fi

if [ -e $sourcedir/parents ]; then
    cat "$sourcedir/parents" | while read parent; do
        if ! $0 -c "$parent"; then
            exit
        fi
    done
fi

find "$sourcedir" -type f | while read source; do
    file=${source#$sourcedir/}

    if [ -z "$file" ]; then
        continue
    fi

    if [ "$file" = "parents" ]; then
        continue
    fi

    if [ "$file" = ".git" ]; then
        continue
    fi

    target="$targetdir/$file"
    if [ -e "$target" ]; then
        if ! is_managed "$file"; then
            echo "Error: $target is unmanaged and already exists"
            reset
            exit -1
        fi
    fi

    manage "$file"

    targetparent=$(dirname "$target")
    if ! [ -d $targetparent ]; then
        if [ -f $targetparent ]; then
            echo "Error: $targetparent already exists and is a file"
            reset
            exit -1
        else
            mkdir -p "$targetparent"
        fi
    fi
    cat "$source" >> "$target"
done

