#!/bin/bash

# Remove previous result files
rm -f Time_VSSSetup_*.txt Time_ShareSecret_*.txt Time_CheckShares_*.txt Time_ReconstructSecret_*.txt

# Parameters
num_shares=30
thresholds=(5 10 15 20 25 30)

# Run the Python script 1000 times for each threshold
for VSS_threshold in "${thresholds[@]}"; do
    echo "Running with VSS_threshold=$VSS_threshold and num_shares=$num_shares"

    for ((i=1; i<=1000; i++)); do
        python3 change_share_and_threshold.py "$VSS_threshold" "$num_shares"
    done
done

echo "Completed all runs."
