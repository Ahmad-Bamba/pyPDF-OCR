#!/bin/bash

# argument 1: start AC
# argument 2: end AC
# argument 3: dir
# argument 4: filename
# argument 5: instance

for i in $(seq $1 $2)
do
    python3 process_covers.py --AC $i --filename $4 --dir $3 --instance $5
    rm -rf images$5/ plaintext$5/
    echo "Finished $i"
done
