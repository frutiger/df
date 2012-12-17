#!/usr/bin/bash

if [[ $# < 1 ]]; then
    echo "Usage: $0 [ <platform> | reset ]"
    exit
fi

dir=$(dirname $0)
platform=$1
sourcedir=$dir/$platform
targetdir=~
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

if [ $1 = "reset" ]; then
    cat $datafile | while read line; do
        file="$(echo $line | cut -d: -f2)"
        target="$targetdir/$file"
        if [ -e "$target" ]; then
            rm -r "$target"
        fi
    done
    rm $datafile
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

if [ -e $sourcedir/parent ]; then
    $(readlink -f $0) $(cat "$sourcedir"/parent)
fi

find "$sourcedir/" | while read source; do
    file=${source#$sourcedir/}

    if [ -z "$file" ]; then
        continue
    fi

    if [ "$file" = "parent" ]; then
        continue
    fi

    target="$targetdir/$file"
    if [ -e "$target" ]; then
        if ! is_managed "$file"; then
            echo "Error: $target is unmanaged and already exists"
            exit
        elif is_owned "$file"; then
            rm -r "$target"
        fi
    fi

    own "$file"

    if [ -d "$source" ]; then
        mkdir -p "$target"
    else
        mkdir -p $(dirname "$target")
        cat "$source" >> "$target"
    fi
done

