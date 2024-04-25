import sys
import ldap

def getEmail(iNumber):
    l = ldap.initialize('ldap://ds2wdf0007.global.corp.sap:389')
    bind_user = 'ngnix_project@global.corp.sap'
    password = 'b3i{g(^@i(A1*sDY^uK@'
    try:
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(bind_user, password)
        if iNumber.upper().startswith("D"):
            search_cn = 'cn=%s,ou=D,ou=Identities,dc=global,dc=corp,dc=sap' %iNumber
        else:
            search_cn = 'cn=%s,ou=I,ou=Identities,dc=global,dc=corp,dc=sap' %iNumber
        filter_cn = '(cn=%s)' %iNumber
        filter_field = ['cn','mail']
        ret = l.search_s(search_cn, ldap.SCOPE_SUBTREE, filter_cn, filter_field)
        if ret[0][1]['mail'][0]:
            return ret[0][1]['mail'][0]
        else:
            print "Can't found email by I number , see detail info as: %s" %str(ret)
            return None
    except Exception as error:
        print error


if __name__ == "__main__":
    USAGE = "USAGE: python %s $iNumber " % sys.argv[0]
    if len(sys.argv) < 2:
        print USAGE
        sys.exit(1)
    print getEmail(sys.argv[1])
