# VU_cooperative_fuzz

-run_lf.py: 
Runs libFuzzer for 6 hours on 4 threads, and starts the covtracker.<br>
Usage: run_lf.py <lf_binary> <seed_corp_dir> <out_corp_dir> <dictionary(optional)>
<hr>
-run_afl.py:
Runs AFL for 6 hours on 4 threads, and starts the covtracker.

-run_cooperative.py:
Runs the cooperative fuzzer of AFL and libFuzzer, for 12 hours on 4 threads (per round: afl 40min, lf 20min). Uses an inbuilt coverage tracker that copies the synthesized corpus every time a fuzzer finishes its timeframe.

-covtracker.py:
Periodically copies the current corpus to the directory "r_<specified_output_corpus>" (and collects all of them here). Currently the measurement interval is set to 1 hour.

-metric_cov.py:
Calculates the coverage progression given a collection of corpora (takes the folder produced by covtracker as input).
  
-metric_speed.py:
Calculates the average speed over multiple threads for the AFL and libFuzzer stand-alone setups (provided the output corpus (AFL) or log files (libFuzzer)).


