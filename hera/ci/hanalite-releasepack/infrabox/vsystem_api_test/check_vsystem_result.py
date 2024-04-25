#!/usr/bin/python
import  xml.dom.minidom
import sys
import os

dom = xml.dom.minidom.parse(sys.argv[1])
root = dom.documentElement
# if only 1 test case(build failed), return 1
# else return 0(multiple test cases)
test_list= root.getElementsByTagName("testcase")
if len(test_list) == 1:
    sys.exit(1)
else:
    sys.exit(0)
