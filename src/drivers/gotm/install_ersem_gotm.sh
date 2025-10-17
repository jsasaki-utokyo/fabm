#!/bin/bash
# install_ersem_gotm.sh

CMAKE_FLAG=""
while getopts ":f:" flag; do
    case "${flag}" in
        f) CMAKE_FLAG=${OPTARG};;
    esac
done

CPU="$(nproc)"
FABM_HOST=gotm
# Select ifx, ifort, or gfortran
CMAKE_Fortran_COMPILER=ifort
# You may want to use -O3 for better performance but check whether the change in results are acceptable.
# Default of -O2 will be used with commenting out the next line.
# FFLAGS=-O3
GOTM_BASE=~/Github/gotm/code
FABM_ERSEM_BASE=~/Github/ersem
FABM_BASE=~/Github/fabm/
CMAKE_INSTALL_PREFIX=~/local/fabm-${CMAKE_Fortran_COMPILER}/${FABM_HOST}

echo "Building GOTM-FABM-ERSEM"
rm -rf ~/build  # Delete if exits.
mkdir ~/build && cd ~/build
cmake $GOTM_BASE -DFABM_BASE=$FABM_BASE -DFABM_ERSEM_BASE=$FABM_ERSEM_BASE -DCMAKE_Fortran_COMPILER=$CMAKE_Fortran_COMPILER -DCMAKE_INSTALL_PREFIX=$CMAKE_INSTALL_PREFIX -DCMAKE_BUILD_TYPE=$CMAKE_BUILD_TYPE $CMAKE_FLAG
make install -j $CPU
