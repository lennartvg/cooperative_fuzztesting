from subprocess import call
from subprocess import check_output
import subprocess
import sys
import os

# input arguments
fuzzer = None
covtracker_dir = None
afl_dir = None
# runtime
NR_OF_THREADS = 4


''' Functions '''


def parse_arguments():
    global fuzzer, covtracker_dir
    if not (len(sys.argv) == 3 or len(sys.argv) == 4):
        print '\nUsage:\t\tpython2.7 metric_speed.py <lf_or_afl> <covtracker_dir> <afl_dir(only for afl)>'
        print 'Usage example:\tpython2.7 metric_speed.py lf r_lf_out'
        print 'Usage example:\tpython2.7 metric_speed.py afl r_afl_out afl_out\n'
        sys.exit()
    else:
        fuzzer = str(sys.argv[1])
        covtracker_dir = str(sys.argv[2])


def validate_input_arguments():
    global fuzzer, afl_dir, covtracker_dir
    if not ((fuzzer == 'afl' or fuzzer == 'lf') and os.path.isdir(covtracker_dir) is True):
        print '\nInput arguments validation failed.\n'
        sys.exit()
    if fuzzer == 'afl':
        afl_dir = str(sys.argv[3])
        if not (os.path.isdir(afl_dir) is True):
            print '\nInput arguments validation failed.\n'
            sys.exit()


def calculate_average_afl_exec_speed():
    global covtracker_dir, afl_dir
    logfile_paths = get_afl_logfile_paths()
    average_exec_speeds = get_afl_average_exec_speeds(logfile_paths)
    results_path = './' + covtracker_dir + '/speed.txt'
    results_file = open(results_path, 'w')
    results_file.write('\nSummed up average AFL execution speed over all threads is: ' +
                       str(sum(average_exec_speeds)) + ' executions per second.\n\n')
    print '\nSpeed metric information has been written to ' + results_path + '.\n'
    results_file.close()


def get_afl_logfile_paths():
    global afl_dir
    result = []
    for i in range(NR_OF_THREADS):
        afl_thread = i + 1
        logfile_path = './' + afl_dir + '/' + str(afl_thread) + '/fuzzer_stats'
        result.append(logfile_path)
    return result


def get_afl_average_exec_speeds(logfile_paths):
    result = []
    for logfile_path in logfile_paths:
        logfile = open(logfile_path, 'r')
        logfile_contents = logfile.read().strip().splitlines()
        logfile.close()
        start_time = int(logfile_contents[0].split()[2])
        end_time = int(logfile_contents[1].split()[2])
        total_execs = int(logfile_contents[4].split()[2])
        avg_execs = total_execs / (end_time - start_time)
        result.append(avg_execs)
    return result


def calculate_average_lf_exec_speed():
    global covtracker_dir
    dev_null = open(os.devnull, 'w')
    logs_dir = './' + covtracker_dir + '/logs'
    logfile_names = get_lf_logfile_names(dev_null, logs_dir)
    average_exec_speeds = get_lf_average_exec_speeds(logs_dir, logfile_names)

    results_path = './' + covtracker_dir + '/speed.txt'
    results_file = open(results_path, 'w')
    results_file.write('\nSummed up average LF execution speed over all threads is: ' +
                       str(sum(average_exec_speeds)) + ' executions per second.\n\n')
    print '\nSpeed metric information has been written to ' + results_path + '.\n'
    results_file.close()
    dev_null.close()


def get_lf_logfile_names(dev_null, logs_dir):
    global covtracker_dir
    call('mkdir ' + logs_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('cp *.log ' + logs_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    logfiles_ls = check_output('ls ' + logs_dir, shell=True)
    return logfiles_ls.strip().split()


def get_lf_average_exec_speeds(logs_dir, logfile_names):
    result = []
    for logfile_name in logfile_names:
        logfile = open(logs_dir + '/' + logfile_name, 'r')
        final_stats_lines = logfile.read().strip().splitlines()[-6:]
        logfile.close()
        for line in final_stats_lines:
            if 'stat::average_exec_per_sec:' in line:
                average_execs = line.split()[1]
                result.append(int(average_execs))
                break
    return result


''' Program '''

parse_arguments()
validate_input_arguments()
if fuzzer == 'afl':
    calculate_average_afl_exec_speed()
else:
    calculate_average_lf_exec_speed()


