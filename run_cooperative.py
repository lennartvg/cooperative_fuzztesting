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
remove_temp_corpus_dirs = None
# runtime
running_fuzz_procs = []
TOTAL_RUNTIME = 60 * 60 * 12  # in seconds
SWITCH_TIME_AFL = 60 * 40  # in seconds
SWITCH_TIME_LF = 60 * 20  # in seconds
runtime_counter = 0
NR_OF_THREADS = 4
dev_null = None
covtracker_dir = None
crashes_dir = None
TEMP_DIR_IN_LIBF = 'temp_in_libfuzzer'
TEMP_DIR_OUT_LIBF = 'temp_out_libfuzzer'
MERGED_DIR_LIBF = 'final_libfuzzer'
TEMP_MINIMIZE_DIR1 = 'temp_minimize_dir1'
TEMP_MINIMIZE_DIR2 = 'temp_minimize_dir2'


''' Functions '''


def parse_arguments():
    global lf_bin, afl_bin, seed_corp, out_corp, dictio, dict_specified
    if not (len(sys.argv) == 5 or len(sys.argv) == 6):
        print '\nUsage:\t\tpython2.7 run_cooperative.py <lf_binary> <afl_binary> <seed_corp_dir> ' \
              '<out_corp_dir> <dictionary(optional)> '
        print 'Usage example:\tpython2.7 run_cooperative.py lf_bin afl_bin cmin_seed_dir output_dir example.dict'
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


def validate_input_arguments():
    global lf_bin, afl_bin, seed_corp, out_corp, dictio
    if not (os.path.isdir(seed_corp) is True and os.path.isdir(out_corp) is True
            and os.path.isfile(lf_bin) is True and os.path.isfile(afl_bin) is True):
        print '\nInput arguments validation failed.\n'
        sys.exit()
    if dict_specified is True:
        if not (os.path.isfile(dictio) is True):
            print '\nInput arguments validation failed.\n'
            sys.exit()
    if os.path.isdir(TEMP_DIR_IN_LIBF) or os.path.isdir(TEMP_DIR_OUT_LIBF) or os.path.isdir(MERGED_DIR_LIBF) or \
            os.path.isdir(TEMP_MINIMIZE_DIR1) or os.path.isdir(TEMP_MINIMIZE_DIR2):
        print '\nTemp directory already exist.\n'
        sys.exit()


def generate_run_commands():
    global lf_run_cmd, afl_default_run_cmd, afl_firstrun_cmd, out_corp, seed_corp, lf_bin, dictio
    lf_run_options = ' -jobs=1000 -workers=' + str(NR_OF_THREADS) + ' -print_final_stats=1 -rss_limit_mb=0'
    if dict_specified:
        afl_firstrun_cmd = 'afl-fuzz -i ' + seed_corp + ' -o ' + out_corp + ' -m none -x ' + dictio
        afl_default_run_cmd = 'afl-fuzz -i ' + MERGED_DIR_LIBF + ' -o ' + out_corp + ' -m none -x ' + dictio
        lf_run_cmd = './' + lf_bin + ' ' + TEMP_DIR_OUT_LIBF + ' ' + TEMP_DIR_IN_LIBF + \
                     lf_run_options + ' -dict=' + dictio
    else:
        afl_firstrun_cmd = 'afl-fuzz -i ' + seed_corp + ' -o ' + out_corp + ' -m none'
        afl_default_run_cmd = 'afl-fuzz -i ' + MERGED_DIR_LIBF + ' -o ' + out_corp + ' -m none'
        lf_run_cmd = './' + lf_bin + ' ' + TEMP_DIR_OUT_LIBF + ' ' + TEMP_DIR_IN_LIBF + lf_run_options


def initialize_cooperative_fuzzer():
    global dev_null, out_corp, covtracker_dir, crashes_dir, seed_corp
    print '\nrun_cooperative.py:\t>> Fuzz testing with libFuzzer and AFL.'
    print 'run_cooperative.py:\t>> Number of threads is set to ' + str(NR_OF_THREADS) + '.'
    print 'run_cooperative.py:\t>> Total runtime is set to ' + str(TOTAL_RUNTIME) + ' seconds.'
    print 'run_cooperative.py:\t>> Switch time is set to ' + str(SWITCH_TIME_AFL) + ' seconds.'
    call('echo core >/proc/sys/kernel/core_pattern', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    # call('echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor', stdout=dev_null,
    #      stderr=subprocess.STDOUT, shell=True)
    covtracker_dir = 'r_cov_' + out_corp
    crashes_dir = 'r_cr_' + out_corp

    # make directories to save state
    call('rm -rf ' + covtracker_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('rm -rf ' + crashes_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('mkdir ' + covtracker_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('mkdir ' + crashes_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)

    # save seed corpus
    cov_save_location = './' + covtracker_dir + '/0'
    cov_save_command = 'cp ./' + seed_corp + '/* ' + cov_save_location
    call('mkdir ' + cov_save_location, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(cov_save_command, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)


def run_cooperative_fuzzer():
    global dev_null, out_corp, runtime_counter
    dev_null = open(os.devnull, 'w')
    counter = 1
    while True:
        try:
            runtime_counter += SWITCH_TIME_AFL
            exec_afl_iteration(counter)
            runtime_counter += SWITCH_TIME_LF
            exec_lf_iteration(counter)

            if runtime_counter == TOTAL_RUNTIME:
                print '\nrun_cooperative.py:\tFuzz testing has finished after ' + str(TOTAL_RUNTIME) + ' seconds.'
                close_program()

            minimize_corpus()
            counter += 1
        except KeyboardInterrupt:
            print '\nrun_cooperative.py:\tReceived interrupt...exiting.\n'
            close_program()


def exec_afl_iteration(counter):
    global afl_firstrun_cmd, afl_default_run_cmd, dev_null, covtracker_dir, runtime_counter, out_corp
    print '\nrun_cooperative.py:\tAFL - started iteration ' + str(counter) + '.'

    # always start with new output corpus
    call('rm -rf ' + out_corp, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('mkdir ' + out_corp, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)

    # start AFL from seed corpus, or from libFuzzer input corpus
    if counter == 1:
        afl_run_multi_threaded(afl_firstrun_cmd)
    else:
        afl_run_multi_threaded(afl_default_run_cmd)
    time.sleep(SWITCH_TIME_AFL)

    # clean up
    close_current_fuzz_job()
    store_current_afl_state()
    print 'run_cooperative.py:\tAFL - finished iteration ' + str(counter) + '.'


def afl_run_multi_threaded(run_cmd):
    global dev_null, afl_bin, running_fuzz_procs
    fuzzer_id = 1

    # start main fuzzing instance
    main_run_cmd = run_cmd + ' -M ' + str(fuzzer_id) + ' ./' + afl_bin
    proc = Popen(main_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
    running_fuzz_procs.append(proc)

    # start secondary fuzzing instances
    for i in range(NR_OF_THREADS - 1):
        fuzzer_id += 1
        secondary_run_cmd = run_cmd + str(' -S ' + str(fuzzer_id) + ' ./' + afl_bin)
        proc = Popen(secondary_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
        running_fuzz_procs.append(proc)


def store_current_afl_state():
    global covtracker_dir, crashes_dir, out_corp

    # save current corpus
    cov_save_location = './' + covtracker_dir + '/' + str(runtime_counter)
    cov_save_command = 'cp ./' + out_corp + '/1/queue/* ' + cov_save_location
    call('mkdir ' + cov_save_location, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(cov_save_command, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)

    # save crashes
    for thread in range(NR_OF_THREADS):
        thread_instance = thread + 1
        crashes_save_command = 'cp ./' + out_corp + '/' + str(thread_instance) + '/crashes/* ' + crashes_dir
        call(crashes_save_command, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)


def exec_lf_iteration(counter):
    global dev_null, lf_run_cmd, running_fuzz_procs, out_corp
    print '\nrun_cooperative.py:\tlibFuzzer - started iteration ' + str(counter) + '.'

    # prepare directories for libFuzzer
    call('rm -rf ' + TEMP_DIR_IN_LIBF, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('rm -rf ' + TEMP_DIR_OUT_LIBF, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('rm -rf ' + MERGED_DIR_LIBF, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('mkdir ' + TEMP_DIR_IN_LIBF, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('mkdir ' + TEMP_DIR_OUT_LIBF, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('mkdir ' + MERGED_DIR_LIBF, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)

    # prepare input corpus and start fuzzing
    get_input_corpus = 'cp ./' + out_corp + '/1/queue/* ' + TEMP_DIR_IN_LIBF
    call(get_input_corpus, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    proc = Popen(lf_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
    running_fuzz_procs.append(proc)
    time.sleep(SWITCH_TIME_LF)

    # clean up
    close_current_fuzz_job()
    store_current_lf_state()
    print 'run_cooperative.py:\tlibFuzzer - finished iteration ' + str(counter) + '.'


def store_current_lf_state():
    global covtracker_dir, crashes_dir
    call('cp ./' + TEMP_DIR_IN_LIBF + '/* ' + MERGED_DIR_LIBF, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('cp ./' + TEMP_DIR_OUT_LIBF + '/* ' + MERGED_DIR_LIBF, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)

    # save current corpus
    cov_save_location = './' + covtracker_dir + '/' + str(runtime_counter)
    cov_save_command = 'cp ./' + MERGED_DIR_LIBF + '/* ' + cov_save_location
    call('mkdir ' + cov_save_location, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(cov_save_command, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)

    # save crashes
    crashes_save_command = 'mv crash-* ' + crashes_dir
    call(crashes_save_command, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)


def minimize_corpus():
    testcases_to_minimize = find_testcases_over_1mb()
    if len(testcases_to_minimize) != 0:
        generate_corpus_minimization_commands()
        print 'run_cooperative.py:\tMinimizing testcases over 1MB...'
        execute_minimization_sequence(testcases_to_minimize)
        print 'run_cooperative.py:\tTestcases minimized.'
    else:
        print 'run_cooperative.py:\tMinimization was not required... continuing without minimization.'


def find_testcases_over_1mb():
    global out_corp
    files_to_minimize = []
    disk_usage_dir = './' + MERGED_DIR_LIBF + '/*'
    disk_usage_output = check_output('du -sh ' + disk_usage_dir, shell=True)
    testcase_list = disk_usage_output.strip().splitlines()

    # create list with paths for testcases that need minimization
    for testcase in testcase_list:
        testcase_size = testcase.split()[0]
        if 'M' in testcase_size:
            files_to_minimize.append(testcase.split()[1])
    return files_to_minimize


def generate_corpus_minimization_commands():
    global afl_minimize_cmd, make_temp_corpus_dirs, remove_temp_corpus_dirs, out_corp, lf_bin, afl_bin
    remove_temp_corpus_dirs = 'rm -rf ' + TEMP_MINIMIZE_DIR1 + ' ' + TEMP_MINIMIZE_DIR2
    make_temp_corpus_dirs = 'mkdir ' + TEMP_MINIMIZE_DIR1 + ' ' + TEMP_MINIMIZE_DIR2
    afl_minimize_cmd = 'afl-cmin -i ' + TEMP_MINIMIZE_DIR1 + ' -o ' + TEMP_MINIMIZE_DIR2 + \
                       ' -m none -- ./' + afl_bin


def execute_minimization_sequence(testcases_to_minimize):
    global make_temp_corpus_dirs, afl_minimize_cmd, remove_temp_corpus_dirs, dev_null, out_corp

    # prepare directories for minimization
    call(remove_temp_corpus_dirs, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(make_temp_corpus_dirs, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)

    # move test cases that need minimization to a temp directory
    for testcase_path in testcases_to_minimize:
        move_cmd = 'mv ' + testcase_path + ' ' + TEMP_MINIMIZE_DIR1
        call(move_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)

    # minimize and incorporate minimzed testcases
    call(afl_minimize_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    return_minimized_testcases = 'mv ./' + TEMP_MINIMIZE_DIR2 + '/* ' + MERGED_DIR_LIBF
    call(return_minimized_testcases, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)


def close_program():
    close_current_fuzz_job()
    clean_all_temp_dirs()
    dev_null.close()
    sys.exit()


def close_current_fuzz_job():
    global running_fuzz_procs
    for proc in running_fuzz_procs:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    running_fuzz_procs = []


def clean_all_temp_dirs():
    call('rm -rf ' + MERGED_DIR_LIBF, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('rm -rf ' + TEMP_DIR_IN_LIBF, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('rm -rf ' + TEMP_DIR_OUT_LIBF, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('rm -rf ' + TEMP_MINIMIZE_DIR1, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('rm -rf ' + TEMP_MINIMIZE_DIR2, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)


''' Program '''

parse_arguments()
validate_input_arguments()
generate_run_commands()

initialize_cooperative_fuzzer()
run_cooperative_fuzzer()


