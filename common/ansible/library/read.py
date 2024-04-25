#!/usr/bin/python

import shlex
import sys
import os.path
import json


def reducer(acc, arg):
    if "=" in arg:
        (key, value) = arg.split("=")
        acc[key] = value
    return acc


def fail(msg):
    print json.dumps({
        "failed": True,
        "msg": msg
    })
    sys.exit(1)


def required(dictionary, key):
    value = dictionary.get(key)
    if value is None:
        fail("%s is not present but required" % key)
    return value

# Basic arg parsing
args_file = sys.argv[1]
args_data = file(args_file).read()
arguments = reduce(reducer, shlex.split(args_data), {})

src = required(arguments, "src")

if not os.path.isfile(src):
    print json.dumps({
        "failed": True,
        "msg": "File does not exist at '%s'" % src
    })
    sys.exit(1)

f = open(src, 'r')
try:
    print json.dumps({
        "file": f.read()
    })
finally:
    f.close()
