#!/usr/bin/env python
"""
title:           A CLI tool for exporting log data containing errors from Elasticsearch into a CSV file.
description:     Command line utility, written in Python, for filtering Elasticsearch in Lucene query syntax or Query DSL syntax and exporting result as documents into a CSV file. JAM page: https://jam4.sapjam.com/wiki/show/ssUqcuNJ5uFymEhOMgbsZr
usage:           ./log_error_filter.py
                 ./log_error_filter.py -c tx-brok.* -u http://login:password@<elasticsearch URL:PORT> -t '2017-08-29T21:47:14+00:00,2017-08-29T21:47:15+00:00' -o ~/file.csv
"""


import sys
import argparse
import imp
import subprocess
import shlex


def import_module_check():
    try:
        imp.find_module('es2csv')
    except ImportError as err:
        print "\n{0}\nPlease install the 'es2csv' module. The module can be found at: https://pypi.python.org/pypi/es2csv/2.4.1\n".format(err)
        sys.exit(1)


def execute_query(query, opts):
    cmd = 'es2csv -u {0} -q \'{1}\' -r -o {2} -S @timestamp'.format(opts.url, query, opts.output_file)
    try:
        args = shlex.split(cmd)
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        print "\nFailed to execute: '{0}'".format(cmd)
        sys.exit(1)
    except OSError as err:
        print "\nFailed to execute: '{0}'\n{1}".format(cmd, err)
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('-c', '--component', dest='component', default='.*', type=str, required=False, help='Select vora component to filter. Default is all components.Support regular expressions.')
    p.add_argument('-u', '--url', dest='url', default='http://localhost:9200', type=str, help='Elasticsearch host URL. Default is %(default)s.')
    p.add_argument('-t', '--time-range', dest='time_range', default='week-to-date', type=str, required=False, metavar='TIME', help='Specify time range. Default is %(default)s. \
    format YYYY-MM-DDTHH:MM:SS+00:00,YYYY-MM-DDTHH:MM:SS+00:00, starting time and ending time inclusive.')
    p.add_argument('-o', '--output-file', dest='output_file', default='log_error.csv', type=str, required=False, metavar='FILE', help='CSV file location. Default file named log_error.csv locating in current folder')
    # p.add_argument('-m', '--max', dest='max_result_num', default=600000, type=int, required=False, metavar='int', help='Maximum number of results to return when to query')

    opts = p.parse_args()
    if opts.time_range == 'week-to-date':
        query = '{"query":{"bool":{"must":[{"regexp":{"datahub_sap_com_app_component":"' + opts.component + '"}},{"regexp":{"log_message":".*"}}]}}}'
    else:
        time_pair = opts.time_range.split(',')
        assert len(time_pair) == 2, "Time Format Error: Cannot parse time format"
        query = '{"query":{"bool":{"must":[{"range":{"@timestamp":{"gte":"' + time_pair[0] + '","lte":"' + time_pair[1] + '"}}}]}}}'

    import_module_check()
    execute_query(query, opts)


if __name__ == '__main__':
    main()
