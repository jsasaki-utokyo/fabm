#!/usr/bin/env python

from __future__ import print_function
import os.path
import tempfile
import subprocess
import shutil
import sys
import glob
import timeit
import errno
import atexit

script_root = os.path.abspath(os.path.dirname(__file__))
fabm_base = os.path.join(script_root, '../..')

default_fabm_url = 'https://github.com/fabm-model/fabm.git'
default_gotm_url = 'https://github.com/gotm-model/code.git'

def run(*args):
    returncode = subprocess.call(args)
    if returncode != 0:
        print('Command failed: %s' % (args,))
        sys.exit(1)

def git_clone(url, workdir, branch=None):
    run('git', 'clone', url, workdir)
    olddir = os.getcwd()
    os.chdir(workdir)
    if branch is not None:
        run('git', 'checkout', branch)
    run('git', 'submodule', 'update', '--init', '--recursive')
    os.chdir(olddir)

def run_gotm(setup_dir, gotm_exe):
    start = timeit.default_timer()
    p = subprocess.Popen([gotm_exe], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=setup_dir)
    stdoutdata, _ = p.communicate()
    duration = timeit.default_timer() - start
    if p.returncode != 0:
        print('FAILED - last output:')
        last_lines = stdoutdata.rsplit('\n', 10)[1:]
        print('\n'.join(last_lines))
    else:
        print('ok (%.3f s)' % duration)
    return p.returncode == 0, duration

def build(build_dir, source_dir, cmake_path='cmake', *cmake_arguments):
    # Save current working directory
    olddir = os.getcwd()

    # Create and change to build directory
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)
    os.mkdir(build_dir)
    os.chdir(build_dir)

    if os.name == 'nt':
        x64 = sys.maxsize > 2**32
        cmake_arguments = ('-A', 'x64' if x64 else 'Win32') + cmake_arguments

    # Build
    try:
        run(cmake_path, source_dir, *cmake_arguments)
    except EnvironmentError as e:
        if e.errno != errno.ENOENT:
            raise
        print('\n\ncmake executable ("%s") not found. Specify its location on the command line with --cmake.' % cmake_path)
        sys.exit(2)
    run(cmake_path, '--build', '.', '--config', 'Debug')

    # Restore original working directory
    os.chdir(olddir)

def enumerate_testcases(gotm_setup_dir, fabm_testcases):
    with open(os.path.join(gotm_setup_dir, 'output.yaml'), 'w') as f:
        f.write("""
result:
  time_unit: day
  time_step: 1
  time_method: mean
  variables:
    - source: fabm/*
    - source: h
""")

    for current_fabm_yaml in sorted(glob.glob(fabm_testcases)):
        # Copy fabm.yaml
        shutil.copyfile(current_fabm_yaml, os.path.join(gotm_setup_dir, 'fabm.yaml'))

        yield os.path.basename(current_fabm_yaml)

def compare_netcdf(path, ref_path):
    import numpy
    import netCDF4
    perfect = True
    nc = netCDF4.Dataset(path)
    nc_ref = netCDF4.Dataset(ref_path)
    for varname in nc.variables.keys():
        if varname not in nc_ref.variables or varname in ('lon', 'lat', 'h', 'z', 'time'):
            continue
        ncvar = nc.variables[varname]
        ncvar_ref = nc_ref.variables[varname]
        dat = ncvar[...]
        valid = numpy.isfinite(dat)
        if not valid.all():
            print('    %s: %i of %i values are invalid' % (varname, valid.size - valid.sum(), valid.size))
            perfect = False
        else:
            delta = dat - ncvar_ref[...]
            maxdelta = numpy.abs(delta).max()
            perfect = perfect and maxdelta == 0.0
            print('    %s: max abs difference = %s' % (varname, maxdelta))
    nc.close()
    nc_ref.close()
    return perfect

def test(gotm_setup_dir, work_root, cmake_path='cmake', cmake_arguments=(), fabm_url=default_fabm_url, gotm_url=default_gotm_url, fabm_branch=None, gotm_branch=None):
    gotm_base = os.path.join(work_root, 'code/gotm')
    build_dir = os.path.join(work_root, 'build')
    gotm_exe = os.path.join(build_dir, 'gotm')

    # Get latest GOTM [public]
    git_clone(gotm_url, gotm_base, gotm_branch)

    build(build_dir, gotm_base, '-DFABM_BASE=%s' % fabm_base, cmake_path, *cmake_arguments)

    for name in enumerate_testcases(gotm_setup_dir, os.path.join(fabm_base, 'testcases/*.yaml')):
        print('TESTING %s...' % name, end='')
        run_gotm(gotm_setup_dir, gotm_exe)

def compare(gotm_setup_dir, work_root=None, cmake_path='cmake', cmake_arguments=(), fabm_url=default_fabm_url, gotm_url=default_gotm_url, fabm_branch=None, gotm_branch=None, fabm_ref_branch=None, gotm_ref_branch=None):
    assert fabm_branch != fabm_ref_branch or gotm_branch != gotm_ref_branch
    git_clone(fabm_url, os.path.join(work_root, 'code/fabm'), fabm_branch)
    git_clone(gotm_url, os.path.join(work_root, 'code/gotm'), gotm_branch)
    build(os.path.join(work_root, 'build'), os.path.join(work_root, 'code/gotm'), cmake_path, '-DFABM_BASE=%s' % os.path.join(work_root, 'code/fabm'), cmake_arguments)

    git_clone(fabm_url, os.path.join(work_root, 'ref/code/fabm'), fabm_ref_branch)
    git_clone(gotm_url, os.path.join(work_root, 'ref/code/gotm'), gotm_ref_branch)
    build(os.path.join(work_root, 'ref/build'), os.path.join(work_root, 'ref/code/gotm'), cmake_path, '-DFABM_BASE=%s' % os.path.join(work_root, 'ref/code/fabm'), cmake_arguments)

    faster, slower = [], []
    failed, success, crashed = [], [], []
    for name in enumerate_testcases(testcase_dir, os.path.join(work_root, 'code/fabm/testcases/*.yaml')):
        print('TESTING %s...' % name)
        print('  reference...', end='')
        valid_ref, duration_ref = run_gotm(testcase_dir, os.path.join(work_root, 'ref/build/gotm'))
        os.rename(os.path.join(testcase_dir, 'result.nc'), os.path.join(testcase_dir, 'result_ref.nc'))
        print('  target...', end='')
        valid, duration = run_gotm(testcase_dir, os.path.join(work_root, 'build/gotm'))
        if valid and valid_ref:
            if compare_netcdf(os.path.join(testcase_dir, 'result_ref.nc'), os.path.join(testcase_dir, 'result.nc')):
                success.append(name)
            else:
                failed.append(name)
        else:
            crashed.append(name)
        if duration < duration_ref:
            faster.append(name)
        else:
            slower.append(name)

    print('%i perfect matches: %s' % (len(success), ', '.join(success)))
    print('%i mismatches: %s' % (len(failed), ', '.join(failed)))
    print('%i failed to run: %s' % (len(crashed), ', '.join(crashed)))
    print('Faster than reference? %i out of %i times.' % (len(faster), len(faster) + len(slower)))

def test_gotm(args):
    if args.fabm_ref_branch is not None:
        print('Running in comparison mode.')
        compare(args.gotm_setup, args.work_root, args.cmake, args.cmake_arguments, fabm_ref_branch=args.fabm_ref)
    else:
        test(args.gotm_setup, args.work_root, args.cmake, *args.cmake_arguments)

def test_pyfabm(args):
    build_dir = os.path.join(args.work_root, 'build')
    build(build_dir, os.path.join(fabm_base, 'src/drivers/python'), args.cmake, '-DCMAKE_BUILD_TYPE=debug', '-DPYTHON_EXECUTABLE=%s' % sys.executable, *args.cmake_arguments)
    sys.path.insert(0, build_dir)
    import pyfabm
    print('pyfabm loaded from %s (library = %s)' % (pyfabm.__file__, pyfabm.dllpath))
    print('Running FABM testcases with pyfabm:')
    for path in sorted(glob.glob(os.path.join(fabm_base, 'testcases/*.yaml'))):
        print('- %s' % path)
        m = pyfabm.Model(path)
        for d in m.dependencies:
            d.value = 1.
        m.start()
        m.getRates()
    try:
        pyfabm.unload()
    except Exception as e:
        print('Failed to unload pyfabm: %s' % e)

def test_0d(args, gotm_url=default_gotm_url):
    build_dir = os.path.join(args.work_root, 'build')
    gotm_dir = os.path.join(args.work_root, 'code/gotm')
    run_dir = os.path.join(args.work_root, 'run')
    shutil.copytree(os.path.join(fabm_base, 'testcases/0d'), run_dir)
    git_clone(gotm_url, gotm_dir)
    build(build_dir, os.path.join(fabm_base, 'src/drivers/0d'), args.cmake, '-DGOTM_BASE=%s' % gotm_dir, *args.cmake_arguments)
    os.chdir(run_dir)
    exe = os.path.join(build_dir, 'Debug/fabm0d.exe' if os.name == 'nt' else 'fabm0d')
    assert os.path.isfile(exe), '%s not found' % exe
    print('Running FABM testcases with 0d driver:')
    for path in sorted(glob.glob(os.path.join(fabm_base, 'testcases/*.yaml'))):
        print('- %s' % path)
        shutil.copy(path, 'fabm.yaml')
        run(exe)

def clean(workdir):
    print('Clean-up: deleting %s' % workdir)
    shutil.rmtree(workdir, ignore_errors=True)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='This script runs all FABM testcases in either pyfabm or GOTM.')
    parser.add_argument('host', choices=('pyfabm', 'gotm', '0d'), help='Host to use for testing.')
    parser.add_argument('--work_root', help='Path to use for code, testcases, results.', default=None)
    parser.add_argument('--fabm_ref', help='Name of FABM branch/commit to compare results against.', default=None)
    parser.add_argument('--gotm_setup', help='Path to directory with GOTM setup (gotm.yaml, etc.)', default=None)
    parser.add_argument('--cmake', help='path to cmake executable', default='cmake')
    parser.add_argument('--compiler', help='Fortran compiler executable')
    args, cmake_arguments = parser.parse_known_args()
    if args.compiler is not None:
        cmake_arguments.append('-DCMAKE_Fortran_COMPILER=%s' % args.compiler)
    args.cmake_arguments = cmake_arguments

    tmp = args.work_root is None
    if tmp:
        args.work_root = tempfile.mkdtemp()
        atexit.register(clean, args.work_root)
    args.work_root = os.path.abspath(args.work_root)
    print('Root of test directory: %s' % args.work_root)

    {'gotm': test_gotm, 'pyfabm': test_pyfabm, '0d': test_0d}[args.host](args)


