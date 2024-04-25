#!/usr/bin/env python

import sys

def getSkipValidation(git_log_file):
    skip_validation = False
    with open(git_log_file) as f:
        lines = f.readlines()
        for l in lines:
            if l.startswith('InfraBox: skip_test_cycle_validation'):
                skip_validation = True

    return skip_validation

if __name__ == "__main__":
    git_log_path = sys.argv[1]
    if getSkipValidation(git_log_path):
        exit(0)
    else:
        exit(1)
