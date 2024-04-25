#!/usr/bin/python
import xml.dom.minidom
from xml.dom.minidom import Node
import sys
import json
import re

try:
    dom = xml.dom.minidom.parse(sys.argv[1])
    root = dom.documentElement
    componentVersion = {}
    for element in root.getElementsByTagName('properties'):
        for x in element.childNodes:
            if x.nodeType == Node.ELEMENT_NODE:
                matchObj = re.match(r'hldep.(.*).version', x.tagName, re.M|re.I)
                if matchObj:
                    componentVersion[matchObj.group(1)] = x.firstChild.data

    print(json.dumps(componentVersion))
    sys.exit(0)
except xml.parsers.expat.ExpatError as e:
    sys.exit(1)
