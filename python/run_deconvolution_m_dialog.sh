#!/bin/bash

dir=$(zenity --file-selection \
       --title "Select Directory Containing Files to Deconvolve" \
       --directory "/home/${USER}/")

bead_file=$(zenity --file-selection \
       --title "Select bead File (.csv)" \
       --filename "/home/${USER}/" \
       --file-filter=*.csv)

if [[ -d $dir ]] && [[ -f $bead_file ]] && [[ $bead_file != " " ]]
then
  for f in $dir/*.ome.tif
  do
    echo "Deconvolving file $f ..."  
    python run_deconvolution_m.py $f --bead $bead_file
  done
else
  zenity --error \
  --text=".ome.tif  and .csv bead file(s) required. No deconvolution performed" \
  --no-wrap \
  --no-markup \
  --ellipsize
fi