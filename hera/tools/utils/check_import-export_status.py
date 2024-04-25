#!/usr/bin/env python

import sys

sys.path.append('/project')
from junit_xml import TestSuite, TestCase

def generate_xml_report(import_result, export_result):
    check_cases = []
    case = TestCase('IMPORT', "import-export_check")
    if int(import_result) != 0:
        case.add_failure_info('import test failed!')
    check_cases.append(case)
    case = TestCase('EXPORT', "import-export_check")
    if int(export_result) != 0:
        case.add_failure_info('export test failed!')
    check_cases.append(case)
    suite = TestSuite("import-export_check", check_cases)
    with open('/infrabox/upload/testresult/import-export_check_result.xml', 'w') as f:
        TestSuite.to_file(f, [suite])

if __name__ == "__main__":
    generate_xml_report(sys.argv[1], sys.argv[2])
