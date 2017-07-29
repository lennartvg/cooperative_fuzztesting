# VU_cooperative_fuzz

-<strong>run_lf.py:</strong><br>
Runs libFuzzer for 6 hours on 4 threads, and starts the covtracker.<br>
Usage: run_lf.py <lf_binary> <seed_corp_dir> <out_corp_dir> <dictionary(optional)><br>
<br>


-<strong>run_afl.py:</strong><br>
Runs AFL for 6 hours on 4 threads, and starts the covtracker.<br>

<br>

-<strong>run_cooperative.py:</strong><br>
Runs the cooperative fuzzer of AFL and libFuzzer, for 12 hours on 4 threads (per round: afl 40min, lf 20min). <br>
Uses an inbuilt coverage tracker that copies the synthesized corpus every time a fuzzer finishes its timeframe.<br>
Usage: <italic>run_cooperative.py</italic> <lf_binary> <afl_binary> <seed_corp_dir> <out_corp_dir> <dictionary(optional)> 
<br>

-<strong>covtracker.py:</strong><br>
Periodically copies the current corpus to the directory "r_<specified_output_corpus>" (and collects all of them here).<br> Currently the measurement interval is set to 1 hour.<br>

<br>

-<strong>metric_cov.py:</strong><br>
Calculates the coverage progression given a collection of corpora (takes the folder produced by covtracker as input).<br>

<br>

-<strong>metric_speed.py:</strong><br>
Calculates the average speed over multiple threads for the AFL and libFuzzer stand-alone setups (provided the output corpus (AFL) or log files (libFuzzer)). <br>


