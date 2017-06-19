# VU_cooperative_fuzz

-run_lf.py: 
starts libFuzzer for X time on Y threads, and starts covtracker

-run_afl.py:
starts AFL for X time on Y threads, and starts covtracker

-run_switcher.py:
runs the cooperative fuzzer of AFL and libFuzzer, for X time on Y threads, and starts covtracker_sw

-covtracker.py:
periodically copies the current corpus to a new folder (and collects all of them here)
  
-covtracker_sw.py:
specialized covtracker, which is used by the switcher

-metric_cov.py:
will calculate the coverage for a collection of corpora (takes the folder produced by covtracker as input)
  
-metric_speed.py:
can calculate the average speed over multiple threads for the AFL and libFuzzer stand-alone setups (provided the log files)


