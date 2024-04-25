import re

regex_escape = re.compile(r"({{.*?}})")
# pylint: disable=W0102
def regex_replace_with_count(s, regex, repl, count=0, flags=0, repl_dict={"{#": "{{", "#}": "}}"}):
    for key, val in repl_dict.iteritems():
        s = s.replace(key, val)
    s = re.sub(regex, repl, s, count, flags)
    return escape(s)

def escape(s):
    return re.sub(regex_escape, r"{{'\1'}}", s)

def dropline_with_substr(s, substr):
    lines_ret = []
    lines = s.split("\n")
    for line in lines:
        if line.find(substr) < 0:
            lines_ret.append(line)
    return "\n".join(lines_ret)

def kops_get_ingress_address(strInput, strAddress):
    lines = strInput.split("\n")
    for line in lines:
        if line.find(strAddress) >= 0:
            return line.split(":")[-1].strip()
    return ""

class FilterModule(object):
    def filters(self):
        return {
            "regex_replace_with_count": regex_replace_with_count,
            "dropline_with_substr": dropline_with_substr,
            "kops_get_ingress_address": kops_get_ingress_address
        }
