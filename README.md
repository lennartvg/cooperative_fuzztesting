# VU_cooperative_fuzz

-run_lf.py: 
runs libFuzzer for 6 hours on 4 threads, and starts the covtracker

-run_afl.py:
runs AFL for 6 hours on 4 threads, and starts the covtracker

-run_cooperative.py:
runs the cooperative fuzzer of AFL and libFuzzer, for 12 hours on 4 threads (per round: afl 40min, lf 20min)
has an inbuilt coverage tracker

-covtracker.py:
periodically copies the current corpus to the directory "r_<specified_output_corpus>" (and collects all of them here)

-metric_cov.py:
will calculate the coverage progression given a collection of corpora (takes the folder produced by covtracker as input)
  
-metric_speed.py:
can calculate the average speed over multiple threads for the AFL and libFuzzer stand-alone setups (provided the log files)


