#!/usr/bin/bash

if [[ $# < 1 ]]
then
  echo "Usage: $0 [ <platform> | reset ]"
  exit
fi

dir=$(dirname $0)
platform=$1
sourcedir=$dir/$platform
targetdir=~
datafile=$targetdir/.dotfiles.data
if [ ! -f $datafile ]
then
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
  if is_owned $1
  then
    return
  fi

  if is_managed $1
  then
    return
  fi

  echo "$platform:$1" >> $datafile
}

if [ $1 = "reset" ]
then
  cat $datafile | while read line
  do
    rm "$targetdir/$(echo $line | cut -d: -f2)"
  done
  rm $datafile
  exit
fi

if [ ! -d $sourcedir ]
then
  echo "Usage: $0 [ <platform> | reset ]"
  echo
  echo "Valid platforms:"
  find $dir -maxdepth 1 -type d | while read p
  do
    platform=$(basename $p)
    if ! [[ $platform =~ \. ]]
    then
      echo $platform
    fi
  done

  exit
fi

if [ -e $sourcedir/parent ]
then
  ./$0 $(cat $sourcedir/parent)
fi

find $sourcedir -type f | while read source
do
  file=$(basename $source)
  target=$targetdir/$file
  if [ $file = "parent" ]
    then continue
  fi

  if [ -e $target ]
  then
    if ! is_managed $file
    then
      echo "Error: $target is unmanaged and already exists"
      exit
    elif is_owned $file
    then
      rm $target
    fi
  fi

  own $file

  cat "$source" >> $target
done

