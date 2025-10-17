#!/bin/bash
# install_ersem_fabm0d_genkai.sh

CMAKE_FLAG=""
while getopts "f:" flag; do
    case "${flag}" in
        f) CMAKE_FLAG=${OPTARG};;
    esac
done

CPU="$(nproc)"
FABM_HOST=0d

# --- Genkai HPC environment setup ---------------------------------------
export PATH=/home/app/intel/2025.1.3/netcdf/4.9.2/bin:/home/app/intel/2025.1.3/netcdf-fortran/4.6.1/bin:/home/app/intel/2025.1.3/hdf5/1.14.4/bin:$PATH
export CMAKE_FLAG="-DNetCDF_ROOT=/home/app/intel/2024.1/netcdf/4.9.2 \
  -DNETCDF_DIR=/home/app/intel/2024.1/netcdf/4.9.2 \
  -DNetCDF_FORTRAN_PATH=/home/app/intel/2024.1/netcdf-fortran/4.6.1 \
  -DHDF5_ROOT=/home/app/intel/2025.1.3/hdf5/1.14.4 \
  -DCMAKE_PREFIX_PATH=/home/app/intel/2024.1/netcdf-fortran/4.6.1"
# ------------------------------------------------------------------------

# Specify ifx or gfortran (ifort is obsolete and not supported).
# Prefer Intel oneAPI ifx; fall back to gfortran.
if command -v ifx >/dev/null 2>&1; then
  CMAKE_Fortran_COMPILER=ifx
  FC=ifx
elif command -v gfortran >/dev/null 2>&1; then
  CMAKE_Fortran_COMPILER=gfortran
  FC=gfortran
else
  echo "Error: neither ifx nor gfortran found in PATH." >&2
  echo "Hint: install Intel oneAPI Fortran (ifx) or GNU Fortran (gfortran)."
  exit 1
fi

# You may want to use -O3 for better performance but check whether the change in results are acceptable.
# Default of -O2 will be used with commenting out the next line.
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
