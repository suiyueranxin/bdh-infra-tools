from tools import SanityChecks
import os,sys

def dis_create_tenant(kubeconfig, tenant_id, env_file):

    service_type = os.getenv("SERVICE_PLAN","")
    if service_type and service_type.endswith('HC'):
        plan_id = "f85e7835-25d5-4e07-9da5-4b951c05da1a"
    elif service_type and service_type.endswith('DWC_TRIAL'):
        plan_id = "e6fbf831-2b93-4c23-8931-7a25548ba772"
    elif service_type and service_type.endswith('CCM'):
        plan_id = "e543ff8c-bdd4-4a49-8e25-f47f6143e900"
    else:
        plan_id = "42afee0b-8703-439e-b78b-23fe045c04ff4"

    print("PLAN_ID is {}".format(plan_id))
    try:
        checks = SanityChecks(kubeconfig,plan_id,tenant_id)
        checks.create_tenant()
        if checks.tenant_was_created():
           print("Tenant {} successfully created".format(checks.tenant_id))
        else:
           print("Tenant {} is not created".format(checks.tenant_id))
           exit(1)

        if not checks.login_and_get_user(env_file):
           print("Tenant {} can not be login".format(checks.tenant_id))
           exit(1)

    except Exception as e:
        raise Exception("Fail to operation on DI:E. with exception {}".format(e))
if __name__ == "__main__":
    dis_create_tenant(sys.argv[1], sys.argv[2], sys.argv[3])

