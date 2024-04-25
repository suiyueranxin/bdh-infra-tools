import requests
import json
import os


def fetch_e2e_secrets():
    im_api_url = "https://im-api.datahub.only.sap/api/v1/data/connection/component/e2e"
    im_token = os.environ.get("IM_TOKEN", "")
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + im_token
    }
    e2e_secrets = requests.get(im_api_url, headers=headers, verify=False)
    f = open("/infrabox/output/e2e_secrets.env", "w")
    for connection in e2e_secrets.json()["connections"]:
        id = connection["connection_payload"]["id"]
        secret = json.dumps(connection["connection_payload"]["contentData"])
        f.write("export {}='{}'\n".format(id, secret))
    f.close()


if __name__ == "__main__":
    fetch_e2e_secrets()