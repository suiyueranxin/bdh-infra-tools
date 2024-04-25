import sys

sys.path.append('/project')
from junit_xml import TestSuite, TestCase

def generate_xml_report(result):
    check_cases = []
    case = TestCase('CREATE_VORATOOLS_INSTANCE', "voratools_check")
    if int(result) != 0:
        case.add_failure_info('create voratools instance failed!')
    check_cases.append(case)
    suite = TestSuite("voratools_check", check_cases)
    with open('/infrabox/upload/testresult/voratools_check_result.xml', 'w') as f:
        TestSuite.to_file(f, [suite])

if __name__ == "__main__":
    generate_xml_report(sys.argv[1])
