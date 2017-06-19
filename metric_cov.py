from subprocess import call
from subprocess import check_output
import sys
import subprocess
import os

# input arguments
nosan_bin = None
covtracker_dir = None


''' Functions '''


def parse_arguments():
    # python2.7 metric_cov.py nosan_ossfuzz r_lf_out
    # python2.7 metric_cov.py nosan_ossfuzz r_afl_out
    # python2.7 metric_cov.py nosan_client r_outlf_client
    global nosan_bin, covtracker_dir
    if not (len(sys.argv) == 3):
        print '\nUsage:\t\tpython2.7 metric_cov.py <nosan_binary> <covtracker_dir>'
        print 'Usage example:\tpython2.7 metric_cov.py nosan_bin r_covtracker_dir\n'
        sys.exit()
    else:
        nosan_bin = str(sys.argv[1])
        covtracker_dir = str(sys.argv[2])


def validate_input_arguments():
    global nosan_bin, covtracker_dir
    if not (os.path.isdir(covtracker_dir) is True and os.path.isfile(nosan_bin) is True):
        print '\nlibfuzz.py:\tInput arguments validation failed.\n'
        sys.exit()


def produce_coverage_results():
    global nosan_bin, covtracker_dir
    nr_of_guards = None
    dev_null = open(os.devnull, 'w')
    results_path = './' + covtracker_dir + '/cov.txt'
    temp_path = './' + covtracker_dir + '/temp.txt'
    call('rm ' + results_path, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('rm ' + temp_path, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    corpus_dirs = get_corpus_directories()
    call('touch ' + results_path, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('touch ' + temp_path, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    results_file = open(results_path, 'a')
    counter = 1

    for corpus in corpus_dirs:
        temp_file = open(temp_path, 'w')
        coverage_cmd = './' + nosan_bin + ' ./' + covtracker_dir + '/' + str(corpus) + ' -runs=0'
        call(coverage_cmd, stdout=temp_file, stderr=subprocess.STDOUT, shell=True)
        temp_file.close()
        temp_file = open(temp_path, 'r')
        output_lines = temp_file.read().strip().splitlines()
        temp_file.close()
        if corpus == 0:
            nr_of_guards = get_nr_of_guards(output_lines)
        initialized_coverage = get_initialized_coverage(output_lines)
        coverage_ratio = initialized_coverage / nr_of_guards
        to_print = str(corpus) + ':' + str('%.4f' % coverage_ratio) + ':' + output_lines[-1].split()[1]
        call('echo \"' + to_print + '\"', stdout=results_file, stderr=subprocess.STDOUT, shell=True)
        print 'Corpus ' + str(counter) + '/' + str(len(corpus_dirs)) + ' has been processed.'
        counter += 1
        temp_file.close()
    results_file.close()
    dev_null.close()


def get_corpus_directories():
    global covtracker_dir
    ls_command_output = check_output('ls ' + covtracker_dir, shell=True)
    corpus_dirs = ls_command_output.strip().split()
    for i in range(len(corpus_dirs)):
        corpus_dirs[i] = int(corpus_dirs[i])
    return sorted(corpus_dirs)


def get_nr_of_guards(output_lines):
    for i in range(len(output_lines)):
        output_line = output_lines[i].split()
        for j in range(len(output_line)):
            if 'guards):' in output_line[j]:
                return float(output_line[j - 1][1:])
    return None


def get_initialized_coverage(output_lines):
    for i in range(len(output_lines)):
        output_line = output_lines[i].split()
        for j in range(len(output_line)):
            if 'INITED' in output_line[j]:
                return float(output_line[j + 2])
    return None


''' Functions '''

parse_arguments()
validate_input_arguments()
produce_coverage_results()


