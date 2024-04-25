import xml.dom.minidom
import sys
try:
    dom = xml.dom.minidom.parse(sys.argv[1])
    root = dom.documentElement
    failures = root.getAttribute('failures')
    errors = root.getAttribute('errors')
    skips = root.getAttribute('skipped')
    tests = root.getAttribute('tests')
    print("Errors: {} Failures: {} Skipped: {} Tests: {}".format(
        errors, failures, skips, tests))
    sys.exit(0) if errors == '0' and failures == '0' else sys.exit(1)
except xml.parsers.expat.ExpatError as e:
    print("File: {} {} ".format(sys.argv[1], e.message))
    sys.exit(1)
