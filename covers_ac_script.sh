#!/bin/bash

# argument 1: number of ACs
# argument 2: dir
# argument 3: filename


for i in $(seq 1 $1)
do
    python3 process_covers.py --AC $i --filename $3 --dir $2
done
