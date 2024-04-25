#!/usr/bin/python
import xml.dom.minidom
import sys

try:
    dom = xml.dom.minidom.parse(sys.argv[1])
    root = dom.documentElement
    versionTag = root.getElementsByTagName(sys.argv[2])[0]
    print(versionTag.childNodes[0].data)
except Exception as e:
    #print(str(e))
    pass
