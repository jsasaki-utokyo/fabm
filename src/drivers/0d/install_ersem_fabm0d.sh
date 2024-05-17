#!/bin/bash

CMAKE_FLAG=""
while getopts "f:" flag; do
    case "${flag}" in
        f) CMAKE_FLAG=${OPTARG};;
    esac
done

CPU="$(nproc)"
FABM_HOST=0d

# Select ifort or gfortran
CMAKE_Fortran_COMPILER=ifort
# FFLAGS=-O3

GOTM_BASE=~/Github/gotm/code
FABM_ERSEM_BASE=~/Github/ersem
FABM_BASE=~/Github/fabm/src/drivers/$FABM_HOST
# CMAKE_BUILD_TYPE=Debug

CMAKE_INSTALL_PREFIX=~/local/fabm-${CMAKE_Fortran_COMPILER}/${FABM_HOST}

echo $CMAKE_FLAG

rm -rf ~/build  # Delete if exits.
mkdir ~/build && cd ~/build
cmake $FABM_BASE -DGOTM_BASE=$GOTM_BASE -DFABM_ERSEM_BASE=$FABM_ERSEM_BASE -DFABM_HOST=$FABM_HOST -DCMAKE_Fortran_COMPILER=$CMAKE_Fortran_COMPILER -DCMAKE_INSTALL_PREFIX=$CMAKE_INSTALL_PREFIX -DCMAKE_BUILD_TYPE=$CMAKE_BUILD_TYPE $CMAKE_FLAG
make install -j $CPU
