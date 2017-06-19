from subprocess import call
from subprocess import Popen
from subprocess import check_output
import subprocess
import signal
import sys
import time
import os

# input arguments
lf_bin = None
afl_bin = None
seed_corp = None
out_corp = None
dictio = None
dict_specified = False
# run commands
afl_firstrun_cmd = None
afl_default_run_cmd = None
lf_run_cmd = None
covtracker_run_cmd = None
# minimization commands
make_temp_corpus_dirs = None
afl_minimize_cmd = None
move_testcases_to_queue = None
remove_temp_corpus_dirs = None
# runtime
TOTAL_RUNTIME = 60 * 60 * 6  # in seconds
SWITCH_TIME_AFL = 60 * 40  # in seconds
SWITCH_TIME_LF = 60 * 20  # in seconds
NR_OF_THREADS = 4
dev_null = None
running_fuzz_procs = []
covtracker_proc = None

# temp_in, temp_out, new_input
# MAKE THIS ONE NICE


''' Functions '''


def parse_arguments():
    # python2.7 run_switcher.py lf_ossfuzz afl_ossfuzz cmin_ossfuzz switcher_out sql.dict
    # python2.7 run_switcher.py lf_client afl_client cmin_client outsw_client
    global lf_bin, afl_bin, seed_corp, out_corp, dictio, dict_specified
    if not (len(sys.argv) == 5 or len(sys.argv) == 6):
        print '\nUsage:\t\tpython2.7 run_switcher.py <lf_binary> <afl_binary> <seed_corp_dir> ' \
              '<out_corp_dir> <dictionary(optional)> '
        print 'Usage example:\tpython2.7 run_switcher.py lf_bin afl_bin cmin_seed_dir output_dir example.dict'
        print '\nMake sure all the test cases are in the root directory of the (afl-cmin minimized) seed corpus.\n'
        sys.exit()
    else:
        lf_bin = str(sys.argv[1])
        afl_bin = str(sys.argv[2])
        seed_corp = str(sys.argv[3])
        out_corp = str(sys.argv[4])
        if len(sys.argv) == 6:
            dict_specified = True
            dictio = str(sys.argv[5])


def generate_run_commands():
    global lf_run_cmd, afl_default_run_cmd, afl_firstrun_cmd, out_corp, seed_corp, lf_bin, \
        afl_bin, dictio, covtracker_run_cmd
    lf_run_options = ' -jobs=1000 -workers=' + str(NR_OF_THREADS) + ' -print_final_stats=1 -rss_limit_mb=0'
    covtracker_run_cmd = 'python2.7 covtracker.py afl ' + seed_corp + ' ' + out_corp
    if dict_specified:
        afl_firstrun_cmd = 'afl-fuzz -i ' + seed_corp + ' -o ' + out_corp + ' -m none -x ' + dictio
        afl_default_run_cmd = 'afl-fuzz -i new_input -o ' + out_corp + ' -m none -x ' + dictio
        lf_run_cmd = './' + lf_bin + ' temp_out temp_in' + lf_run_options + ' -dict=' + dictio
    else:
        afl_firstrun_cmd = 'afl-fuzz -i ' + seed_corp + ' -o ' + out_corp + ' -m none'
        afl_default_run_cmd = 'afl-fuzz -i new_input -o ' + out_corp + ' -m none'
        lf_run_cmd = './' + lf_bin + ' temp_out temp_in' + lf_run_options


def generate_corpus_minimization_commands():
    global afl_minimize_cmd, make_temp_corpus_dirs, remove_temp_corpus_dirs, move_testcases_to_queue, \
        out_corp, lf_bin, afl_bin
    make_temp_corpus_dirs = 'mkdir ./' + out_corp + '/1/temp1 ./' + out_corp + '/1/temp2'
    afl_minimize_cmd = 'afl-cmin -i ./' + out_corp + '/1/temp1 -o ./' + out_corp + '/1/temp2 -m none -- ./' + afl_bin
    move_testcases_to_queue = 'mv ./' + out_corp + '/1/temp2/* ./' + out_corp + '/1/queue'
    remove_temp_corpus_dirs = 'rm -rf ./' + out_corp + '/1/temp1 ./' + out_corp + '/1/temp2'


def run_double_fuzzing():
    global dev_null
    dev_null = open(os.devnull, 'w')
    counter = 1
    switch_counter = 0
    print '\nrun_switcher.py:\t>> Fuzz testing with libFuzzer and AFL.'
    print 'run_switcher.py:\t>> Number of threads is set to ' + str(NR_OF_THREADS) + '.'
    print 'run_switcher.py:\t>> Total runtime is set to ' + str(TOTAL_RUNTIME) + ' seconds.'
    print 'run_switcher.py:\t>> Switch time is set to ' + str(SWITCH_TIME_AFL) + ' seconds.'
    call('echo core >/proc/sys/kernel/core_pattern', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor', stdout=dev_null,
         stderr=subprocess.STDOUT, shell=True)
    while True:
        try:
            exec_afl_iteration(counter)
            switch_counter += SWITCH_TIME_AFL
            exec_lf_iteration(counter)
            switch_counter += SWITCH_TIME_LF
            if switch_counter == TOTAL_RUNTIME:
                print '\nrun_switcher.py:\tFuzz testing has finished after ' + str(TOTAL_RUNTIME) + ' seconds.'
                close_program()
            minimize_corpus()
            counter += 1
        except KeyboardInterrupt:
            print '\nrun_switcher.py:\tReceived interrupt...exiting.\n'
            close_program()


def exec_afl_iteration(counter):
    global afl_firstrun_cmd, afl_default_run_cmd, dev_null, running_fuzz_procs, \
        covtracker_run_cmd, covtracker_proc, out_corp
    print '\nrun_switcher.py:\tAFL - started iteration ' + str(counter) + '.'
    if counter == 1:
        afl_run_multi_threaded(afl_firstrun_cmd)
        covtracker_proc = Popen(covtracker_run_cmd, shell=True, preexec_fn=os.setsid)
        print 'run_switcher.py:\tCoverage tracker started.'
    else:
        call('rm -rf ' + out_corp, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
        call('mkdir ' + out_corp, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
        afl_run_multi_threaded(afl_default_run_cmd)
    time.sleep(SWITCH_TIME_AFL)
    if counter != 1:
        call('rm -rf new_input', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    close_current_fuzz_job()
    print 'run_switcher.py:\tAFL - finished iteration ' + str(counter) + '.'


def afl_run_multi_threaded(run_cmd):
    global dev_null, out_corp, afl_bin, running_fuzz_procs
    fuzzer_id = 1
    main_run_cmd = run_cmd + str(' -M ' + str(fuzzer_id) + ' ./' + afl_bin)
    proc = Popen(main_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
    running_fuzz_procs.append(proc)
    for i in range(NR_OF_THREADS - 1):
        fuzzer_id += 1
        secondary_run_cmd = run_cmd + str(' -S ' + str(fuzzer_id) + ' ./' + afl_bin)
        proc = Popen(secondary_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
        running_fuzz_procs.append(proc)


def exec_lf_iteration(counter):
    global dev_null, lf_run_cmd, running_fuzz_procs, out_corp
    print '\nrun_switcher.py:\tlibFuzzer - started iteration ' + str(counter) + '.'
    call('mkdir temp_in', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('mkdir temp_out', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    copy_from_afl_corp = 'cp ./' + out_corp + '/1/queue/* temp_in'
    call(copy_from_afl_corp, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    proc = Popen(lf_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
    running_fuzz_procs.append(proc)
    time.sleep(SWITCH_TIME_LF)
    close_current_fuzz_job()
    call('mkdir new_input', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('cp ./temp_in/* new_input', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('cp ./temp_out/* new_input', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('rm -rf temp_in', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('rm -rf temp_out', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    print 'run_switcher.py:\tlibFuzzer - finished iteration ' + str(counter) + '.'


def minimize_corpus():
    testcases_to_minimize = find_testcases_over_1mb()
    if len(testcases_to_minimize) != 0:
        print 'run_switcher.py:\tMinimizing testcases over 1MB...'
        execute_minimization_sequence(testcases_to_minimize)
        print 'run_switcher.py:\tTestcases minimized.'
    else:
        print 'run_switcher.py:\tMinimization was not required... continuing without minimization.'


def find_testcases_over_1mb():
    global out_corp
    files_to_minimize = []
    disk_usage_dir = './' + out_corp + '/1/queue/*'
    disk_usage_output = check_output('du -sh ' + disk_usage_dir, shell=True)
    testcase_list = disk_usage_output.strip().splitlines()
    for testcase in testcase_list:
        testcase_size = testcase.split()[0]
        if 'M' in testcase_size:
            files_to_minimize.append(testcase.split()[1])
    return files_to_minimize


def execute_minimization_sequence(testcases_to_minimize):
    global make_temp_corpus_dirs, afl_minimize_cmd, remove_temp_corpus_dirs, \
        move_testcases_to_queue, dev_null, out_corp
    call('touch minimized.txt', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(make_temp_corpus_dirs, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    for testcase_path in testcases_to_minimize:
        move_cmd = 'mv ' + testcase_path + ' ./' + out_corp + '/1/temp1'
        call(move_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(afl_minimize_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(move_testcases_to_queue, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(remove_temp_corpus_dirs, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)


def close_program():
    global covtracker_proc
    os.killpg(os.getpgid(covtracker_proc.pid), signal.SIGINT)
    time.sleep(1)
    close_current_fuzz_job()
    dev_null.close()
    sys.exit()


def close_current_fuzz_job():
    global running_fuzz_procs
    for proc in running_fuzz_procs:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    running_fuzz_procs = []


''' Program '''

parse_arguments()
generate_run_commands()
generate_corpus_minimization_commands()
run_double_fuzzing()


