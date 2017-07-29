# Copyright 2017 VU University Amsterdam - C.L. van Gijtenbeek
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from subprocess import Popen
import subprocess
import signal
import sys
import time
import os

# input arguments
lf_bin = None
seed_corp = None
out_corp = None
dictio = None
dict_specified = False
# run commands
lf_run_cmd = None
covtracker_run_cmd = None
# runtime
FUZZER_RUNTIME = 60 * 60 * 6  # in seconds
NR_OF_THREADS = 4


''' Functions '''


def parse_arguments():
    global lf_bin, seed_corp, out_corp, dictio, dict_specified
    if not (len(sys.argv) == 4 or len(sys.argv) == 5):
        print '\nUsage:\t\tpython2.7 run_lf.py <lf_binary> <seed_corp_dir> <out_corp_dir> <dictionary(optional)>'
        print 'Usage example:\tpython2.7 run_lf.py lf_bin cmin_seed_dir output_dir example.dict\n'
        sys.exit()
    else:
        lf_bin = str(sys.argv[1])
        seed_corp = str(sys.argv[2])
        out_corp = str(sys.argv[3])
        if len(sys.argv) == 5:
            dictio = str(sys.argv[4])
            dict_specified = True


def validate_input_arguments():
    global lf_bin, seed_corp, out_corp, dictio
    if not (os.path.isdir(seed_corp) is True and os.path.isdir(out_corp) is True and os.path.isfile(lf_bin) is True):
        print '\nrun_lf.py:\tInput arguments validation failed.\n'
        sys.exit()
    if dict_specified is True:
        if not (os.path.isfile(dictio) is True):
            print '\nrun_lf.py:\tInput arguments validation failed.\n'
            sys.exit()


def generate_run_commands():
    global lf_run_cmd, covtracker_run_cmd, seed_corp, out_corp, lf_bin, dictio
    lf_run_options = '-jobs=1000 -workers=' + str(NR_OF_THREADS) + ' -print_final_stats=1 -rss_limit_mb=0'
    covtracker_run_cmd = 'python2.7 covtracker.py lf ' + seed_corp + ' ' + out_corp
    if dict_specified:
        lf_run_cmd = './' + lf_bin + ' ' + out_corp + ' ' + seed_corp + ' ' + lf_run_options + ' -dict=' + dictio
    else:
        lf_run_cmd = './' + lf_bin + ' ' + out_corp + ' ' + seed_corp + ' ' + lf_run_options


def run_libfuzzer():
    global lf_run_cmd, covtracker_run_cmd
    dev_null = open(os.devnull, 'w')
    lf_proc = None
    covtracker_proc = None
    try:
        # start libfuzzer
        lf_proc = Popen(lf_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
        print '\nrun_lf.py:\t\tlibFuzzer started, running for ' + str(FUZZER_RUNTIME) + ' seconds...'

        # start the coverage tracker
        covtracker_proc = Popen(covtracker_run_cmd, shell=True, preexec_fn=os.setsid)
        print 'run_lf.py:\t\tCoverage tracker started...'

        time.sleep(FUZZER_RUNTIME)
        print '\nrun_lf.py:\t\tFuzz testing finished after ' + str(FUZZER_RUNTIME) + ' seconds.'
        exit_program(lf_proc, covtracker_proc, dev_null)
    except KeyboardInterrupt:
        print '\nrun_lf.py:\t\tReceived interrupt...'
        exit_program(lf_proc, covtracker_proc, dev_null)


def exit_program(lf_proc, covtracker_proc, dev_null):
    os.killpg(os.getpgid(covtracker_proc.pid), signal.SIGINT)
    time.sleep(1)
    os.killpg(os.getpgid(lf_proc.pid), signal.SIGTERM)
    dev_null.close()
    sys.exit()


''' Program '''

parse_arguments()
validate_input_arguments()
generate_run_commands()
run_libfuzzer()

