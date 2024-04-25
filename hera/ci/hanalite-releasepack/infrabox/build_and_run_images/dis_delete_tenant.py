from tools import SanityChecks
import os,sys

def dis_delete_tenant(kubeconfig, tenant_id):
    service_type = os.getenv("SERVICE_PLAN","")
    if service_type and service_type.endswith('HC'):
        plan_id = "f85e7835-25d5-4e07-9da5-4b951c05da1a"
    elif service_type and service_type.endswith('DWC_TRIAL'):
        plan_id = "e6fbf831-2b93-4c23-8931-7a25548ba772"
    elif service_type and service_type.endswith('CCM'):
        plan_id = "e543ff8c-bdd4-4a49-8e25-f47f6143e900"
    else:
        plan_id = "42afee0b-8703-439e-b78b-23fe045c04ff4"

    try:
        checks = SanityChecks(kubeconfig,plan_id,tenant_id)
        checks.delete_tenant()
        if checks.tenant_was_deleted():
            print("Tenant {} successfully deleted".format(checks.tenant_id))
        else:
            print("Tenant {} is not deleted".format(checks.tenant_id))

    except Exception as e:
        raise Exception("Fail to operation on DI:E. with exception {}".format(e))


if __name__ == "__main__":
    dis_delete_tenant(sys.argv[1], sys.argv[2])

