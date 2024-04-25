import requests
import sys
import pdb

MONSOON_BASE_URL = "https://monsoon.mo.sap.corp/api/"
MONSOON_BASE_HEADER = {"Accept": "application/vnd.monsoon.v1+json", "content-type":"application/json", \
                       "Authorization":""}
MONSOON_PROXIES = {"http": None,"https": None,}

def add_org_team_member(org, team, number, token):
    url = MONSOON_BASE_URL + "organizations/" + org + "/teams/" + team + "/members/" + number
    MONSOON_BASE_HEADER ["Authorization"] = "Basic " + token
    try:
        return requests.post(url,proxies=MONSOON_PROXIES,verify=False, headers=MONSOON_BASE_HEADER)
    except Exception as e:
        exception = "Try to add user: %s into team %s failed with exception: %s" %(number, team, str(e))
        raise Exception(exception)

if __name__ == "__main__":
    USAGE = "USAGE: python %s $Monsoon_organization $monsoon_team $number $monsoon_auth_token " % sys.argv[0]
    if len(sys.argv) < 4:
        print USAGE
        sys.exit(1)
    pdb.set_trace()
    add_org_team_member(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
