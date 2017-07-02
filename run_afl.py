from subprocess import Popen
from subprocess import call
import subprocess
import signal
import sys
import time
import os

# input arguments
afl_bin = None
seed_corp = None
out_corp = None
dictio = None
dict_specified = False
# run commands
afl_default_run_cmd = None
covtracker_run_cmd = None
# runtime
FUZZER_RUNTIME = 60 * 60 * 6  # in seconds
NR_OF_THREADS = 4


''' Functions '''


def parse_arguments():
    global afl_bin, seed_corp, out_corp, dictio, dict_specified
    if not (len(sys.argv) == 4 or len(sys.argv) == 5):
        print '\nUsage:\t\tpython2.7 run_afl.py <afl_binary> <seed_corp_dir> <out_corp_dir> <dictionary(optional)>'
        print 'Usage example:\tpython2.7 run_afl.py afl_bin cmin_seed_dir output_dir example.dict\n'
        sys.exit()
    else:
        afl_bin = str(sys.argv[1])
        seed_corp = str(sys.argv[2])
        out_corp = str(sys.argv[3])
        if len(sys.argv) == 5:
            dictio = str(sys.argv[4])
            dict_specified = True


def validate_input_arguments():
    global afl_bin, seed_corp, out_corp, dictio
    if not (os.path.isdir(seed_corp) is True and os.path.isdir(out_corp) is True and os.path.isfile(afl_bin) is True):
        print '\nrun_afl.py:\tInput arguments validation failed.\n'
        sys.exit()
    if dict_specified is True:
        if not (os.path.isfile(dictio) is True):
            print '\nrun_afl.py:\tInput arguments validation failed.\n'
            sys.exit()


def generate_run_commands():
    global afl_default_run_cmd, covtracker_run_cmd, seed_corp, out_corp, dictio
    covtracker_run_cmd = 'python2.7 covtracker.py afl ' + seed_corp + ' ' + out_corp
    if dict_specified:
        afl_default_run_cmd = 'afl-fuzz -i ' + seed_corp + ' -o ' + out_corp + ' -m none ' + '-x ' + dictio
    else:
        afl_default_run_cmd = 'afl-fuzz -i ' + seed_corp + ' -o ' + out_corp + ' -m none'


def run_afl():
    global afl_default_run_cmd, covtracker_run_cmd
    dev_null = open(os.devnull, 'w')
    call('echo core >/proc/sys/kernel/core_pattern', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor', stdout=dev_null,
         stderr=subprocess.STDOUT, shell=True)
    afl_procs = None
    covtracker_proc = None
    try:
        afl_procs = start_afl_multi_threaded(dev_null)
        print '\nrun_afl.py:\t\tAFL started, running for ' + str(FUZZER_RUNTIME) + ' seconds...'
        ##
        covtracker_proc = Popen(covtracker_run_cmd, shell=True, preexec_fn=os.setsid)
        print 'run_afl.py:\t\tCoverage tracker started...'
        ##
        time.sleep(FUZZER_RUNTIME)
        print '\nrun_afl.py:\t\tFuzz testing finished after ' + str(FUZZER_RUNTIME) + ' seconds.'
        exit_program(afl_procs, covtracker_proc, dev_null)
    except KeyboardInterrupt:
        print '\nrun_afl.py:\t\tReceived interrupt...'
        exit_program(afl_procs, covtracker_proc, dev_null)


def start_afl_multi_threaded(dev_null):
    global afl_default_run_cmd, afl_bin
    afl_procs = []
    fuzzer_id = 1
    main_run_cmd = afl_default_run_cmd + str(' -M ' + str(fuzzer_id) + ' ./' + afl_bin)
    proc = Popen(main_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
    afl_procs.append(proc)
    for i in range(NR_OF_THREADS - 1):
        fuzzer_id += 1
        secondary_run_cmd = afl_default_run_cmd + str(' -S ' + str(fuzzer_id) + ' ./' + afl_bin)
        proc = Popen(secondary_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
        afl_procs.append(proc)
    return afl_procs


def exit_program(afl_procs, covtracker_proc, dev_null):
    os.killpg(os.getpgid(covtracker_proc.pid), signal.SIGINT)
    time.sleep(1)
    for proc in afl_procs:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    dev_null.close()
    sys.exit()


''' Program '''

parse_arguments()
validate_input_arguments()
generate_run_commands()
run_afl()


