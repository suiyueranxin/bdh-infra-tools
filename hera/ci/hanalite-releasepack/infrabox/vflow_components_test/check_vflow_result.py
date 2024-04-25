#!/usr/bin/python
import  xml.dom.minidom
import sys
try:
  dom = xml.dom.minidom.parse(sys.argv[1])
  root = dom.documentElement
  failures = root.getAttribute('failures')
  errors = root.getAttribute('errors')
  print "errors: %s failures: %s tests: %s" % (root.getAttribute('errors'), root.getAttribute('failures'), root.getAttribute('tests'))
  sys.exit(0) if errors == '0' and failures == '0' else  sys.exit(1)
except xml.parsers.expat.ExpatError, e:
  print "file %s %s " % (sys.argv[1], e.message)
  sys.exit(1)
