from subprocess import call
import sys
import subprocess
import os
import time

# input arguments
fuzzer = None
seed_corp_dir = None
out_corp_dir = None
# runtime
start_time = None
results_dir = None
TIME_INTERVAL = 60 * 60  # in seconds


''' Functions '''


def parse_arguments():
    global seed_corp_dir, out_corp_dir, results_dir, fuzzer
    time.sleep(1)
    if not (len(sys.argv) == 4):
        print '\ncovtracker.py:\tUsage:\t\tpython2.7 covtracker.py <afl_or_lf_or_coop> <seed_corp_dir> <out_corp_dir>'
        print 'covtracker.py:\tUsage example:\tpython2.7 covtracker.py lf cmin_seed_dir out_dir\n'
        print 'covtracker.py:\tUsage example:\tpython2.7 covtracker.py afl cmin_seed_dir out_dir\n'
        sys.exit()
    else:
        fuzzer = str(sys.argv[1])
        seed_corp_dir = str(sys.argv[2])
        out_corp_dir = str(sys.argv[3])
    results_dir = 'r_' + out_corp_dir


def run_coverage_tracker():
    global seed_corp_dir, out_corp_dir, results_dir, start_time, fuzzer
    dev_null = open(os.devnull, 'w')
    time_counter = 0

    # initialize directory to save all measured corpora
    call('rm -rf ' + results_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('mkdir ' + results_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    print 'covtracker.py:\t\tUsing ' + results_dir + ' as output folder.'

    # set AFL corpus to save
    if fuzzer == 'afl':
        out_corp_dir = out_corp_dir + '/1/queue'

    start_time = int('%.0f' % time.time())
    while True:
        try:
            if time_counter == 0:
                save_current_corpus(time_counter, dev_null, seed_corp_dir)
            else:
                save_current_corpus(time_counter,  dev_null, out_corp_dir)
            time.sleep(TIME_INTERVAL)
            time_counter += TIME_INTERVAL
        except KeyboardInterrupt:
            print 'covtracker.py:\t\tReceived interrupt...'
            save_current_corpus('final', dev_null, out_corp_dir)
            print 'covtracker.py:\t\tFinal corpus saved.\n'
            dev_null.close()
            quit()


def save_current_corpus(time_counter, dev_null, corpus_to_save):
    global results_dir, start_time, seed_corp_dir
    if time_counter == 'final':
        current_time = int('%.0f' % time.time())
        time_counter = current_time - start_time

    # create folder to save the current corpus, and save it
    save_location = './' + results_dir + '/' + str(time_counter)
    call('mkdir ' + save_location, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    copy_current_corpus = 'cp ./' + corpus_to_save + '/* ' + save_location
    call(copy_current_corpus, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)

    if fuzzer == 'lf':
        # in case of libFuzzer, we have to add the seed corpus,
        # since the output corpus only provides additional coverage on top of the seed corpus
        copy_seed_corpus = 'cp ./' + seed_corp_dir + '/* ' + save_location
        call(copy_seed_corpus, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    print 'covtracker.py:\t\tSaved current corpus at ' + str(time_counter) + ' seconds.'


''' Program '''

parse_arguments()
run_coverage_tracker()


