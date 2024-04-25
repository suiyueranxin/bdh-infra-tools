# ODTEM User Manual

ODTEM -- which stands for On Demand Test Execution and Management, is a Rest API service, which is used for the management and execution of test jobs in SAP DataHub.

With this tool, users can create their own validation process with a specified DataHub version(milestone version or a specified code branch with a commit change ref) and test suites in different ways(running in different infrabox projects or just return the infrabox.json content only for the next step customized usage).

### Running validation with a milestone version against customized DH cluster.

This case is suitable for you to run test against an already set-up DH cluster.
You need to prepare the DH specifications.

- `VORA_VERSION` The DH version string. eg: *2.7.32-ms*  *2.6.86*
- `GERRIT_CHANGE_BRANCH` For the `VORA_VERSION` with suffix *-ms*, please set it to `master`, and set it to `stable` for other case.
- `VORA_TENANT` The tenant name which is **NOT** system tenant
- `VORA_USERNAME` The user name for the tenant
- `VORA_PASSWORD` The password for the tenant. 
- `VORA_SYSTEM_TENANT_PASSWORD` The password for `system` tenant. 
- `NAMESPACE` The namespace that hold DH on k8s cluster
- `VSYSTEM_ENDPOINT` The VSYSTEM logon URL
- `KUBECONFIG` The content of the k8s logon credential. **Only JSON format is allowed**
-  `NODE_HOST` Legacy option. Please set it as same as the `VSYSTEM_ENDPOINT` but without port number. eg: *https://max-zhang-20190613-095914375-gke.infra.datahub.sapcloud.io*
- `VSYSTEM_PORT` Legacy option. Please set it to `443`
- `PRODUCT_NAME` Legacy option. Please set it to `BDH`
- `PROJECT_NAME` Legacy option. Please set it to `hanalite-releasepack`
- `PROVISION_PLATFORM` Legacy option. Please set it to `GKE`. *This option was used to determin how to install the DH. Since the DH is already set-up as customized DH cluster, this option will be discard in later release*
- `test` This is a list of test cases. For each item of the list, the dic format would be like below:
```
        {
            "case_name": "test_case_name_string",
            "environment": {...}
        }
```
   > - `case_name` You could find all the test case names from [TestPlans](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/master/TestCycleConfiguration/TestPlans.json). The case_name is the value of `infrabox_job` with `_gke` as suffix. For instance, you could find the job name `voratools_test` in the TeatPlans.json, so the `case_name` should be `voratools_test_gke`
   > - `environment` It's a dic that save all running enviroment key/values for the validation job. You could find the default enviroments of the jobs from [Milestone InfraBox Json Dump](milestone.json). You could overwirte any value.
- `executor` The I/D number of exectuor.

**Note**: *The plain text password will be discard in later release, we plan to manage the password by the executor I/D number *

Here's an example of creating a single milestone validation job on GKE:

```
POST /api/v2/tasks/test/userenv HTTPS/1.1
Host: odtem-api.datahub.only.sap
Content-Type: application/json
{
    "environment": {
        "PRODUCT_NAME": "BDH",
        "PROJECT_NAME": "hanalite-releasepack",
        "VORA_VERSION": "2.7.32-ms",
        "VORA_TENANT": "default",
        "GERRIT_CHANGE_BRANCH": "master",
        "VORA_USERNAME": "system",
        "VORA_PASSWORD": "bDh33@FcGQU",
        "PROVISION_PLATFORM": "GKE",
        "NODE_HOST": "https://max-zhang-20190613-095914375-gke.infra.datahub.sapcloud.io",
        "VSYSTEM_PORT": "443",
        "NAMESPACE": "bdh-2-7-18-ms",
        "VSYSTEM_ENDPOINT": "https://max-zhang-20190613-095914375-gke.infra.datahub.sapcloud.io:443",
        "VORA_SYSTEM_TENANT_PASSWORD": "bDh71@stKgf",
        "KUBECONFIG": {
            "apiVersion": "v1",
            "clusters": [
                {
                    "cluster": {
                        "certificate-authority-data": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUN5RENDQWJDZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRFNE1USXhNVEExTkRNd01Gb1hEVEk0TVRJd09EQTFORE13TUZvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTkhnCk5TRHc1RTRpZ1lKK1hjT21xLzIxbzd2bjJQMTEzQTRvZVZuMmtIaURBbXY5WXJQL3RMb3p6QThMb3J4Rkk0ZUsKeXZ6a0F0ME9pQjY5VFNRVCt2R3Z1K3hXQXloMkZqUlBZbk5JYjlJRHRDZk8zbXRJNllEanRCSGFIOXlGUjBaQwoyZGJkVFRIRDd4YmovZm1PbS8vbndkTGlzREFvcURGVUVlVWEwdUdRSjdVdjl3ak1WbnBMWmZqQWlOdFRXZDJ0CmRtNW9LN1ZwZ2lNY25NK3FyTkZnUzB5NUpMTDBvY25DTWUwSG05T3NOK0dlK0NHM2dqalhjcEFZVlRhdEhJblQKTHdhSEdmeXI3QVp3ejFzajN5S09MdEJBd0FRN1JWUS9NNmhyNFNHckMxTVpFYlpsY1BFbTBHbEhlTWJHZ0lDcAovbmN3NWtqUW1jaXUrLzlsT2xjQ0F3RUFBYU1qTUNFd0RnWURWUjBQQVFIL0JBUURBZ0trTUE4R0ExVWRFd0VCCi93UUZNQU1CQWY4d0RRWUpLb1pJaHZjTkFRRUxCUUFEZ2dFQkFGaVhSNHEzV0ZUZnc0cWV4Z1FhaS9kRXhFeSsKOXI0USsydW5sSFhYR0Y4cDRrT3dvUmI1eVcwa201L3NQOHQrM285QkFSSEIxVS84ZnBKcHhnSzFpQXBmK1NKMAp3OU5SM0UrMjRhaThqeGRGMEVkRksvaWVidTlDMzJDV1g1UWVwUVVCenJEM1pEREd4ay82RHRBenRkNXdNNHI2CndSRU1rT1BiUVpVR2dtWFhBT29aOVN2VVJtTUtwblJ3UXduei9HTm5qYmlIc1Naend5RWE3U0prNWJUYitxSUIKVGxNaW9TQU5ZWnFoa25WQWxZNjJQSFJjaXI0WEFPbFB1N3k0bVBvSzlqc01CQkRId1hYT2V5QkowUTM5Q2o4UApOOVhmWnlMWG9MUkRDczk1V0pMQUYvSDBleUlHQk9pMnk0VDNVWEc1c0R2VlhLVjJVckdMaGovVFcxQT0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=",
                        "server": "https://10.48.185.10:6443"
                    },
                    "name": "kubernetes"
                }
            ],
            "contexts": [
                {
                    "context": {
                        "cluster": "kubernetes",
                        "user": "kubernetes-admin"
                    },
                    "name": "kubernetes-admin@kubernetes"
                }
            ],
            "current-context": "kubernetes-admin@kubernetes",
            "kind": "Config",
            "preferences": {},
            "users": [
                {
                    "name": "kubernetes-admin",
                    "user": {
                        "client-certificate-data": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUM4akNDQWRxZ0F3SUJBZ0lJSUlYVDQ3SEw5ZW93RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB4T0RFeU1URXdOVFF6TURCYUZ3MHhPVEV5TVRFd05UUXpNRFJhTURReApGekFWQmdOVkJBb1REbk41YzNSbGJUcHRZWE4wWlhKek1Sa3dGd1lEVlFRREV4QnJkV0psY201bGRHVnpMV0ZrCmJXbHVNSUlCSWpBTkJna3Foa2lHOXcwQkFRRUZBQU9DQVE4QU1JSUJDZ0tDQVFFQThySGwvL1dYRlc0eENFWkYKY1RkNFptaENJdFJWOGpWSGhmNFBFK1FIKzJYcmpxRU8vS3RLdlRpT0R3VTRrZDRwV0xOU3ROaEM5aDZvdE5MRApCN0hZZWZNb29HeEhFcDJ6VEpMaGlCZTVjU0xNckQ3QlU0d3lHNER6T1VsZzExRk5HOTl5TnM1bEdqbCsya1lTCi81T1c0M2hDd3dFTWVnRnVzcTN4M3NaS0o0UTJHSWEzc1RUSHlhZS9kR0VJaDVOdTRtQkNDcXhYTDZEMWJuWlAKVmRYTW9pNlBIa1RWVjFSdkNKazJob3ZPbUlobDRXQzFYKytvUithcXN1RGwyVU9wSHVXS3lzTitWQ1VVL3llTwpqL1hFMTlPYnBCYlNyTzM2YnlSWXd2aFhYbFo2bnE2VW01VFFHWFFVVDZ4b0NqMTd0ZjRhbmZsa3crQ3NOYUdxCkNIeUJQd0lEQVFBQm95Y3dKVEFPQmdOVkhROEJBZjhFQkFNQ0JhQXdFd1lEVlIwbEJBd3dDZ1lJS3dZQkJRVUgKQXdJd0RRWUpLb1pJaHZjTkFRRUxCUUFEZ2dFQkFMVlZUMTRSRFIzSlZPRzVSUW1vQUtUVnp4WTM5THAvZnJwbwpLeVc0OHQvMSt1WFRPR3h0ZERQUGxxVytRMXpnajQwQmNpNjNUY1prNng3YVNsM00yRCtqc1dUSkswelA1VmVWCktCQVc2UDN3dldmNmt5b2J6TG5XS3VIZ2twNnB5SFA4NW5JdU9KZHN3SVYreUVkOVR0Q09YdWxkK2VXaEk5ZmoKVXR1L3VGa3BXS1QzbS9NK0ZIK3FkL2R5bWNPK2tIZ2hPUzNMTXBuVHVwYTk3Z0x6UExyRWZ4dlhJVkZvU2tRdQpOTDEraStwcXVTenlnUnh0RC9ud3BtQlJXdmRjL2dqbHJlQmpmMFZINlQ4cDliTmxOYTkwRVRXRHdIYW8rZnZuCnd3RThYZjBPUDdxTVJUMGh1OG80ejlUL2s5aEtxNy8rNHRqYnhzRlIwdEZNRzV4dnluWT0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=",
                        "client-key-data": "LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFb3dJQkFBS0NBUUVBOHJIbC8vV1hGVzR4Q0VaRmNUZDRabWhDSXRSVjhqVkhoZjRQRStRSCsyWHJqcUVPCi9LdEt2VGlPRHdVNGtkNHBXTE5TdE5oQzloNm90TkxEQjdIWWVmTW9vR3hIRXAyelRKTGhpQmU1Y1NMTXJEN0IKVTR3eUc0RHpPVWxnMTFGTkc5OXlOczVsR2psKzJrWVMvNU9XNDNoQ3d3RU1lZ0Z1c3EzeDNzWktKNFEyR0lhMwpzVFRIeWFlL2RHRUloNU51NG1CQ0NxeFhMNkQxYm5aUFZkWE1vaTZQSGtUVlYxUnZDSmsyaG92T21JaGw0V0MxClgrK29SK2Fxc3VEbDJVT3BIdVdLeXNOK1ZDVVUveWVPai9YRTE5T2JwQmJTck8zNmJ5Ull3dmhYWGxaNm5xNlUKbTVUUUdYUVVUNnhvQ2oxN3RmNGFuZmxrdytDc05hR3FDSHlCUHdJREFRQUJBb0lCQUV1dmV3REZ3Q1lveFJYRgpoR1o0WEEzanVheE85N2FmTXZ6d2JCZFI1OE5ZMTRzVll5MGM1aVA0ZlNUbUJleEhrakZkU3crbTJjc1RhSjFyCmxQTFRYYVU2VlpNaDhWQTI2ZkdaWk1naVRleWdZNS9idWtLcDEvNkh5bEkxTmdRd0VKSCtyd20wZUFjam94SEQKQksyN2d6VFJEbER1Qk13UG9rd0t2d0V3YVhQRXhmY3h4RUh1TmZtWFR5TTQzUmxWS0NIamhPUnBMSjhsK3NMWQpsZjN2TXlZNlZjVGhmejVXVUt4RTVDOWljR2hza1RmcjdJdTE1UjI2S0dNU2NCZDYyNlpqUi9Jakd3NWhHZHUyCjNRMmduNHlRaFhaK3ZsQkFiWGhia1VSWDkwR3M4cVBZYmUycDd4UjE5a0VMcG5qb3JQcDBPVzJ1a21NVG5BcDgKVUdvdG5TRUNnWUVBOWh2c1g5Z0syVHVpWVFtajFzZkZFVERMMDZOaGJSOVFIK3c2L3RBNFIvNVFXRlZ5TjN1NgoreWhDUG5xT2ZrV0FTdytWWitFYzJOZmhlNTJpcmF3cmlXcnpBV1JKMHFVLzJ3OXRVNXdrLzh6MjQ2MWpxMTJkCkVZK29WZjBWaStmSHhoOVd0enZMOUVtK3hVd2VBOUZCWWFaaVNsWE5XNVdBQUJtUExpcndJa2tDZ1lFQS9ITFoKUjNHRk9HSTNEOFlteUNlOXRxbStPM01xaVBYbmNhc3NmNmwvdmxjeE5aRVh0TzZrM1FqZzJKUXZucGxkRzhwVwo3dWZ1KzVVMG9Ub0lmcVdON1NJMlB4U0U0UExvYmc3aDRJTERRSlM0RVc4NEtvM1Z3clc4WDEwdVI1SjJUUk5PCjdKcXVudHMrYmxERUNGUEFGSUt0K2pHdEJrZVVVSElMU0dkYkIwY0NnWUFuUXVjZmx5Q0w3VGFIVW5sZnJ6amgKK0MzY0VtbGRkaXhiRzEyQi93ZXJmSWVtditMYnRSSnNOTXowbUtxWXZFK3VLY3RFNmlXbTlqR1RmZDlRNDNHQwpsNXd5c2FRUlJhbDlNZVhYKzhYdlJPeHgvOXd4bjFxS1RhZW1LQnpDMS9RSHlFSVdNeVRqVU14dFB5cGVvNGhSCm9yQjFlV0NzWnBvbjZldnNpbzhLZVFLQmdCa1VrKytjSUo4a2F0SC9YclQ5OWNRakF3cEcrOC9WbG1QZG5MTW0KTk5IRk9kZFhqZUprM3k0eWhwd2R4TWxkOVRrZ2xoaHdKSGNNTU1sZnlaNURkbUU3eCtYbWRQa2dTT1UrUjBTVgoyUzRlV0ZjckZJcHR3dkh3T2tIRE1TamRMVEdsSEc4M1F1ZjNZakYxaHJSSkZja3ozbkwvNG0vQVJzVGpQNm0yCjB2MWJBb0dCQU9BYk1KVUd5ZHJrS1VIMnErTTRYSDNQd2xKbVo1WUtxazFNWUNpcXpKREpSMDl2R3A3cVo1WUYKY043Mm5oUzZnRUVQRE9pYnhwTm5GeXdxQXZGVzkrNTRwRjFmcFZRTDZ1QU5rNHFPWVh4ajUxVkprcHdwbEVLbApzN1p1RUlCQ0syOGJnZVRsRWg5eUZabFk4MXZ5NGJpb1JuY0UvR0NyMW5FaGJHSzNFMFg3Ci0tLS0tRU5EIFJTQSBQUklWQVRFIEtFWS0tLS0tCg=="
                    }
                }
            ]
        }
    },
    "test": [
        {
            "case_name": "vflow_test_gke",
            "environment": {
                "SCENARIO_LIST": "basic",
                "RETRY_TEST": "3"
            }
        }
    ],
    "executor": "i322966"
}
```

Then you will get the response:
```
{
    "message": "Start test task successfully",
    "status": "200",
    "task_name": "BDH-DEMAND_VALIDATION-20190619_095938796",
    "url": "https://infrabox.datahub.only.sap/dashboard/#/project/on_demand_test/build/176/1"
}
```
The `url` from json response will be the created validaiton job. If you open the link, you can see it will run the validation test jobs.

### Running validation with a milestone version and some test jobs

This case is suitable for some milestone cases. User needs to prepare the milestone version, and test job names on the coresponding cloud platforms(AWS-EKS,GKE,GARDENER-AWS).

Here's an example of creating a single milestone validation job on GKE:

```
POST /api/v2/tasks/test/defenv HTTPS/1.1
Host: odtem-api.datahub.only.sap
Content-Type: application/json
{
    "environment": {
        "PRODUCT_NAME": "BDH",
        "PROVISION_PLATFORM": "GKE",
        "GERRIT_CHANGE_BRANCH": "master",
        "VORA_VERSION": "2.6.46-ms"
    },
    "test": [
        { "case_name": "vsystem_api_test_gke" },
        { "case_name": "vflow_test_gke" },
        { "case_name": "deployment_operator_test_gke" },
        { "case_name": "vflow_authorization-scenario_test_gke" },
        { "case_name": "vflow_data_transform_scenario_test_gke" },
        { "case_name": "voratools_test_gke" }
    ]
}
```
And here's the cURL command:

```
curl -X POST \
  https://odtem-api.datahub.only.sap/api/v2/tasks/test/defenv \
  -H 'Content-Type: application/json' \
  -d '{
    "environment": {
        "PRODUCT_NAME": "BDH",
        "PROVISION_PLATFORM": "GKE",
        "GERRIT_CHANGE_BRANCH": "master",
        "VORA_VERSION": "2.6.46-ms"
    },
    "test": [
        { "case_name": "vsystem_api_test_gke" },
        { "case_name": "vflow_test_gke" },
        { "case_name": "deployment_operator_test_gke" },
        { "case_name": "vflow_authorization-scenario_test_gke" },
        { "case_name": "vflow_data_transform_scenario_test_gke" },
        { "case_name": "voratools_test_gke" }
    ]
}'
```

Then we will get the response:

```
{
  "infrabox_json": {
    "jobs": [
      {
        ...
      }
    ], 
    "version": 1
  }, 
  "message": "Start test task successfully", 
  "status": "200", 
  "task_name": "BDH-DEMAND_VALIDATION-20190517_084828948", 
  "url": "https://infrabox.datahub.only.sap/dashboard/#/project/on_demand_test/build/152/1", 
  "version_info": {
    "build_prod": false, 
    "prod_repository_name": "bdh_repository", 
    "prod_repository_url": "https://int.repositories.cloud.sap/artifactory/build-milestones/com/sap/datahub/SAPDataHub/", 
    "prod_version": "2.6.46-ms"
  }
}
```

The `url` from json response will be the created validaiton job. If you open the link, you can see it will run the validation with the coresponding DataHub version `2.6.46-ms` on cloud platform `GKE`.

Here are some explanation of the properties in request json:

- `PROVISION_PLATFORM`: cloud platform of running tests, possible values: `GKE`， `AWS-EKS`, `GARDENER-AWS`, `AZURE-AKS`
- `VORA_VERSION`: DataHub milestone version
- `GERRIT_CHANGE_BRANCH`: The test code(bdh-infra-tools) branch used in the test. Usually if your milestone version is ended by `-ms`, please specify `master`; else please specify `stable`

### Running validation with a hanalite-releasepack gerrit change and some test jobs

If you want to use a gerrit change from hanalite-releasepack project and make a validation, here's an example:

```
POST /api/v2/tasks/test/defenv HTTPS/1.1
Host: odtem-api.datahub.only.sap
Content-Type: application/json
{
    "environment": {
        "PRODUCT_NAME": "BDH",
        "PROVISION_PLATFORM": "GKE",
        "GERRIT_PATCHSET_REF": "refs/changes/95/4019295/2",
        "GERRIT_CHANGE_BRANCH": "master",
        "INCLUDE_BUILD_JOB": true
    },
    "test": [
        { "case_name": "vsystem_api_test_gke" },
        { "case_name": "vflow_test_gke" },
        { "case_name": "deployment_operator_test_gke" },
        { "case_name": "vflow_authorization-scenario_test_gke" },
        { "case_name": "vflow_data_transform_scenario_test_gke" },
        { "case_name": "voratools_test_gke" }
    ]
}
```

Add `INCLUDE_BUILD_JOB` and `GERRIT_PATCHSET_REF` in the json request.


### Test case management

If you want to create new test job on different cloud platform, please take a look at [Component test creation/integration guide](../TestIntegrationGuide/ComponentTestCreationGuide.md).
