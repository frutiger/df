#!/bin/bash

if [[ $# < 1 ]]; then
    echo "Usage: $0 [ <platform> | reset ]"
    exit
fi

dir=$(dirname $0)
platform=$1
sourcedir=$dir/$platform
targetdir=$(echo ~)
datafile=$targetdir/.dotfiles.data
if [ ! -f $datafile ]; then
    touch $datafile
fi

function is_managed() {
    grep -q ":$1$" $datafile
    return $?
}

function is_owned() {
    grep -q "$platform:$1$" $datafile
    return $?
}

function own() {
    if is_owned $1; then
        return
    fi

    if is_managed $1; then
        return
    fi

    echo "$platform:$1" >> $datafile
}

function rmemptydir() {
    if ! [ $(find "$1" -type f -print -quit) ]; then
        rm -r "$1"
        rmemptydir $(dirname "$1")
    fi
}

function reset() {
    cat $datafile | while read line; do
        file="$(echo $line | cut -d: -f2)"
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
        if ! $0 "$parent"; then
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
        elif is_owned "$file"; then
            rm -r "$target"
        fi
    fi

    own "$file"

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

