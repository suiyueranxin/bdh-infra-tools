# DI Push Validation User Guide

![push-validation-process](https://github.wdf.sap.corp/i322966/bdh-infra-tools/blob/master/hera/docs/image/push-validation-process.svg)
Links to 
> [IM(Infrastructure Manager)](https://im.datahub.only.sap/)
> [Central Monitor](https://infra-monitoring.datahub.only.sap)
> [Create Bug](https://sapjira.wdf.sap.corp/projects/DM01/issues)

All jobs in push validation are list in the table below, click the link according to the failure job name and get advise from [Find issue classification via console logs](#Find-issue-classification-via-console-logs) and [Typical Failures](#typical-failures).

|Failure Test Job          |                 Troubleshoot             |
|------------------------------------------------|---------------------|
generator | Restart single job  |
generator/build-extended-product-bridge | [Troubleshoot build](#generatorbuild) |
generator/build-full-product-bridge | [Troubleshoot build](#generatorbuild)|
generator/build-product-bridge| [Troubleshoot build](#generatorbuild) |
generator/build-installer| [Troubleshoot build](#generatorbuild) |
generator/test| [Troubleshoot build-test](#generatortest) |
generator/test-install| [Troubleshoot build](#generatorbuild) |
generator/bdh-infra-tools/generator| [Troubleshoot generator](#bdh-infra-toolsgenerator) |
generator/bdh-infra-tools/generator/build | [Troubleshoot generator/build](#bdh-infra-toolsgeneratorbuild) |
generator/bdh-infra-tools/generator/build_copy_files | [Troubleshoot build_copy_files](#bdh-infra-toolsgeneratorbuild_copy_files) |
generator/bdh-infra-tools/generator/k8s_creation_di_on_prem-gke | [Troubleshoot k8s creation](#bdh-infra-toolsgeneratork8s_creation_di_on_prem-gke) |
generator/bdh-infra-tools/generator/install_di_on_prem-gke| [Troubleshoot install on-premise](#bdh-infra-toolsgeneratorinstall_di_on_prem-gke) |
generator/bdh-infra-tools/generator/import_export_test_di_on_prem-gke | [Troubleshoot test](#bdh-infra-toolsgeneratortest) |
generator/bdh-infra-tools/generator/vflow_flowagent_test_di_on_prem-gke| [Troubleshoot test](#bdh-infra-toolsgeneratortest) |
generator/bdh-infra-tools/generator/vflow_test_di_on_prem-gke| [Troubleshoot test](#bdh-infra-toolsgeneratortest) |
generator/bdh-infra-tools/generator/vora_dqp_test_di_on_prem-gke | [Troubleshoot test](#bdh-infra-toolsgeneratortest) |
generator/bdh-infra-tools/generator/vora_license_manager_test_di_on_prem-gke | [Troubleshoot test](#bdh-infra-toolsgeneratortest)|
generator/bdh-infra-tools/generator/vora_tools_ui_e2e_test_di_on_prem-gke | [Troubleshoot test](#bdh-infra-toolsgeneratortest)|
generator/bdh-infra-tools/generator/k8s_deletion_di_on_prem-gke | Restart single job |
generator/bdh-infra-tools/generator/job_report_gke | Restart single job |
generator/bdh-infra-tools/generator/mirror_docker_image | [Troubleshoot mirror](#bdh-infra-toolsgeneratormirror_docker_image) |
generator/bdh-infra-tools/generator/dhaas_creation_dhaas_aws| [Troubleshoot install on-cloud](#bdh-infra-toolsgeneratordhaas_creation_dhaas_aws) |
generator/bdh-infra-tools/generator/import_export_test_dhaas_aws | [Troubleshoot test](#bdh-infra-toolsgeneratortest) |
generator/bdh-infra-tools/generator/vflow_flowagent_test_dhaas_aws| [Troubleshoot test](#bdh-infra-toolsgeneratortest) |
generator/bdh-infra-tools/generator/vflow_test_dhaas_aws| [Troubleshoot test](#bdh-infra-toolsgeneratortest) |
generator/bdh-infra-tools/generator/vora_dqp_test_dhaas_aws | [Troubleshoot test](#bdh-infra-toolsgeneratortest) |
generator/bdh-infra-tools/generator/vora_license_manager_test_dhaas_aws | [Troubleshoot test](#bdh-infra-toolsgeneratortest)|
generator/bdh-infra-tools/generator/vora_tools_ui_e2e_test_dhaas_aws | [Troubleshoot test](#bdh-infra-toolsgeneratortest)|
generator/bdh-infra-tools/generator/k8s_deletion_dhaas_aws | Restart single job |
generator/bdh-infra-tools/generator/job_report_dhaas_aws | Restart single job |

## Failure jobs
### generator/build* 
These jobs are used to build and push product images. If any of these job failed, including `generator/test-install`, most possibility it's an infra issue and lead to docker build failed. The infrabox console may show error like ```Failed to build the image: Command failed``` on the top. Please check if your change related to the product image build process. If not, then restart the single failure job could resolve the issue in most cases. If the failure persist, please refer [Find issue classification via console logs](#Find-issue-classification-via-console-logs) and [Typical Failures](#typical-failures) to find corresponding `component name` in JIRA ticket and create [DI Infrastructure Bug](https://sapjira.wdf.sap.corp/projects/DM01/issues) accordingly.
### generator/test 
This job failure may caused by commit message doesn't meet th convention, please refer [Commit Convention and changelog generation using Elvis](https://jam4.sapjam.com/wiki/show/sl1R4wPA8yvtYD7oTZpToW) and update commit message accordingly.

### bdh-infra-tools/generator
This job is used to expand a full `infrabox.json` according to test plan. Due to the infrabox limitation, we can not restart the `generator` job itself. Please restart the entire infrabox build via `RESTART BUILD` button or rebase you commit to execute another infrabox build. If the same failure persist, refer [Find issue classification via console logs](#Find-issue-classification-via-console-logs) and [Typical Failures](#typical-failures) to find corresponding `component name` in JIRA ticket and create [DI Infrastructure Bug](https://sapjira.wdf.sap.corp/projects/DM01/issues) accordingly. 

### bdh-infra-tools/generator/build
The `generator/build` job only extract the image lists from the `full-product-image`. 
Mostly, restart the job could resolve the issue. If the same failure persist, refer [Find issue classification via console logs](#Find-issue-classification-via-console-logs) and [Typical Failures](#typical-failures) to find corresponding `component name` in JIRA ticket and create [DI Infrastructure Bug](https://sapjira.wdf.sap.corp/projects/DM01/issues) accordingly. 

### bdh-infra-tools/generator/build_copy_files
This job only copy enviroments from the `build` job. Restart the job could resolve the issue.

### bdh-infra-tools/generator/k8s_creation_di_on_prem-gke
For the scenarios below:
- Accordig to the job console, if the job failed before `Run container`, then the issue would be either in `Infrabox` or `gerrit` or `di-dev-cicd-docker.int.repositories.cloud.sap`. 
- If the job failed after `Run container`, and before `Finalize`, then the issue is in `IM` or `DI CI test infrastructure`. 
- If the job failed at `Finalize`, then the issue is in `Infrabox`.

Restart the single failure job could resolve the issue in most cases. If the failure persist, please refer [Find issue classification via console logs](#Find-issue-classification-via-console-logs) and [Typical Failures](#typical-failures) to find corresponding `component name` in JIRA ticket and create [DI Infrastructure Bug](https://sapjira.wdf.sap.corp/projects/DM01/issues) accordingly. 


### bdh-infra-tools/generator/install_di_on_prem-gke
For the scenarios below:
- Accordig to the job console, if the job failed before `Run container`, then the issue would be either in `Infrabox` or `gerrit` or `di-dev-cicd-docker.int.repositories.cloud.sap`.
- If the job failed after `Run container`:
  1. Click `CONSOLE OUTPUT` and search `Install vora successfully`. If you can find the the message, it indecates the installer completed, but something wrong at vflow instance creation or healthy check step.
  2. If `Install vora failed` show in the console log, it means the install job not completed. Please view the slcb.log in `Archive` for more details. 
  3. if the `DI DATALAKE CONNECTION creation failed!` show in the console log, it means something is wrong with the cloud resources that maintained by IM.

Restart the single failure job could resolve the issue in most cases. If the failure persist, please refer [Find issue classification via console logs](#Find-issue-classification-via-console-logs) and [Typical Failures](#typical-failures) to find corresponding `component name` in JIRA ticket and create [DI Infrastructure Bug](https://sapjira.wdf.sap.corp/projects/DM01/issues) accordingly. 


### bdh-infra-tools/generator/dhaas_creation_dhaas_aws
For the scenarios below:
- Accordig to the job console, if the job failed before `Run container`, then the issue would be either in `Infrabox` or `gerrit` or `di-dev-cicd-docker.int.repositories.cloud.sap`.
- If the job failed after `Run container`:
  1. Click `CONSOLE OUTPUT` and search `Kubernetes cluster is READY!`. If you can find the the message, it indecates the installer completed, but something wrong at vflow instance creation or healthy check step.
  2. If `Health Check is done!` show in the console log, it indecates the install job completed and ready to use. The `infraobx` issue may cause the job failed at the `Finalize` step.
  3. If `DataHub installation failed!` or `Stop waiting when met this type of status!` show in the console log, it indecates the install job not completed. Please view the `dhaas_creation_fail_log.json` in `Archive` for more details. If the error in `dhaas_creation_fail_log.json` is not related with your code change, and the issue could be reproduce after re-trigger, please create [DI Infrastructure Bug](https://sapjira.wdf.sap.corp/projects/DM01/issues) accordingly.

Restart the single failure job could resolve the issue in most cases. If the failure persist, please refer [Find issue classification via console logs](#Find-issue-classification-via-console-logs) and [Typical Failures](#typical-failures) to find corresponding `component name` in JIRA ticket and create [DI Infrastructure Bug](https://sapjira.wdf.sap.corp/projects/DM01/issues) accordingly. 

### bdh-infra-tools/generator/mirror_docker_image
This job mirror images from _public.int.repositories.cloud.sap_ to _docker://726853116465.dkr.ecr.eu-central-1.amazonaws.com/dev/_. If this job failed, most properly something wrong with the docker registry, just restart the single job. If the same failure persist, refer [Find issue classification via console logs](#Find-issue-classification-via-console-logs) and [Typical Failures](#typical-failures) to find corresponding `component name` in JIRA ticket and create [DI Infrastructure Bug](https://sapjira.wdf.sap.corp/projects/DM01/issues) accordingly. 

### bdh-infra-tools/generator/\*test\*
According to the job suffix, and restart the `dhaas_creation_dhaas_aws` or `k8s_creation_di_on_prem-gke` accordingly. If the failure persist, please refer [Find issue classification via console logs](#Find-issue-classification-via-console-logs) and [Typical Failures](#typical-failures) to find corresponding `component name` in JIRA ticket and create [DI Infrastructure Bug](https://sapjira.wdf.sap.corp/projects/DM01/issues) accordingly. 

# Appendix
## Find issue classification via console logs
1. The infrabox job console page would show summary logs by default
   - example for [build* ](https://github.wdf.sap.corp/i322966/bdh-infra-tools/blob/master/hera/docs/image/build-product-image.png) jobs:
   - example for [install on-premise](https://github.wdf.sap.corp/i322966/bdh-infra-tools/blob/master/hera/docs/image/install-on-premise.png) jobs:
   - example for [install on-cloud](https://github.wdf.sap.corp/i322966/bdh-infra-tools/blob/master/hera/docs/image/dhaas-creation.png) jobs:
   - example for \*test\* jobs:
   ![job-console](https://github.wdf.sap.corp/i322966/bdh-infra-tools/blob/master/hera/docs/image/job-console.png) 
  
   
2. If the failure occure in `Prepare Job` and  `Build image`, and there is error message for `git clone` from `git.wdf.sap.corp:29418/hanalite-releasepack` then the issue  goes to `Gerrit`, otherwise the issue goes to `Infrabox`.
3. If the failure occure after `Build image` and before `Run container`, then it indecates there are issues during **docker build** execution. If there is an error after command `docker pull` from `di-dev-cicd-docker.int.repositories.cloud.sap` or `docker.wdf.sap.corp` or `di-dev-cicd-docker.int.repositories.cloud.sap`. Then the issue goes to `di-dev-cicd-docker.int.repositories.cloud.sap` or `docker.wdf.sap.corp` or `di-dev-cicd-docker.int.repositories.cloud.sap`.
4. (For build\* jobs only) If the failure occur after `Build image` but before `Deploying` then the issue goes to `docker.wdf.sap.corp` or `v2-registry.datahub.only` or `Converged Cloud service`, depends on the error messages.
    > Typical failure on `Converged Cloud service`:
    ```
    Temporary failure in name resolution: Unknown host artifactory
    ```
5. (For \*test\* jobs only) If the `health check` failed, then click "TESTS" tab on the failure job to refer which item get failure status. [Re-trigger test](#Re-trigger-test) accordingly.
6. (For \*test\* jobs only) If the failure occur after `health check starts` and before `CI pre check is done.` then it indicate there is someting wrong with the DI instance. Please restart the `k8s_creation_di_on_prem-gke` or `dhaas_creation_dhaas_aws` (depends on the platform) to have another try with a new installation. If the failure persist, create [DI Infrastructure Bug](https://sapjira.wdf.sap.corp/projects/DM01/issues) accordingly.
7. If the failure occur after `CI pre check is done`, then there is something wrong during the test execution.
    + If the test is `vflow_flowagent_test`, which use cloud resource that maintained by IM. Please check the [Central Monitor]. (https://infra-monitoring.datahub.only.sap). If everything good, then restart the `k8s_creation_di_on_prem-gke` or `dhaas_creation_dhaas_aws` (depends on the platform) to have another try with a new installation. If the failure persist, create [DI Infrastructure Bug](https://sapjira.wdf.sap.corp/projects/DM01/issues) accordingly.
    + If the test job show failure test cases in job `TESTS` and it's related with yoru code change, please update your change accordingly.

8. If the failure occur in `Finalize` or `Finished` then the issue also goes to `Infrabox`, please raise issue in # infrabox.

## Re-trigger test
- If the failure infrabox job run after `k8s_creation` or `dhaas_creation` but before `k8s_deletion`, then restart the `k8s_creation` or `dhaas_creation` accordingly.
- If the failure infrabox job is `k8s_deletion` or `job_report`, then restart the single job itself.
- If the failure infrabox job is ``
- If the failure infrabox job run before k8s_creation/dhaas_creation, then restart the failure job itself


## Typical Failures
- Developer need to change the gerrit change
  > Typical failure for `generator/test` failure:
  ```
  AssertionError: subject does not meet commit message convention, please refer https://jam4.sapjam.com/wiki/show/sl1R4wPA8yvtYD7oTZpToW
  ```
- Bug for Component: `gerrit`
  > Typical failure:
  ```
  git clone --depth=10 ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack /data/repo
      Cloning into '/data/repo'...
      ssh: connect to host git.wdf.sap.corp port 29418: Connection refused
      fatal: Could not read from remote repository.
  ```
- Bug for Component: `Cloud service`
  > Typical failures on `Converged Cloud service`:
  ```
  Temporary failure in name resolution: Unknown host artifactory
  ```
  ```
  Could not validate integrity of download from https://int.repositories.cloud.sap/artifactory/build-releases-3rd-party/org/apache/maven/maven-artifact-manager/2.2.1/maven-artifact-manager-2.2.1.jar: Checksum validation failed, no checksums available
  ```
  ```
   --- artifactory ping statistics ---
      2 packets transmitted, 2 received, 0% packet loss, time 1001ms
      rtt min/avg/max/mdev = 1.011/1.113/1.215/0.102 ms
      keytool error: java.lang.Exception: No certificate from the SSL server
      keytool error: java.lang.Exception: Input not an X.509 certificate
  ```
  > Typical failures on `GCP Cloud service`:
  ```
  Error writing manifest: Error uploading manifest 1.15.3 to eu.gcr.io/sap-p-and-i-big-data-vora/infrabox/releasepack/test-install/17909/com.sap.dsp.linuxx86_64/ml-tf-serving-gpu: received unexpected HTTP status: 504 Gateway Timeout
  ```
  ```
  Error: could not reach target registry eu.gcr.io/sap-p-and-i-big-data-vora/validation-shared: Google Container Registry does not have read-write permisions. Permissions to the storage pool of the cluster can only be set at cluster creation time
  ```
- Bug for `Infrabox`
  > Typical failures at `Finalize` step
  ```
  IOError: [Errno 2] No such file or directory: u'/tmp/output/parts/output.tar.snappy-aa
  ```
- Bug for `DI private registry`
  > Typical failures for docker pull or skopeo mirror from(to) v2-registry.
  ```
  Get http://di-dev-cicd-docker.int.repositories.cloud.sap/v2/: net/http: request canceled while waiting for connection (Client.Timeout exceeded while awaiting headers)
  ```
  ```
  manifest for di-dev-cicd-docker.int.repositories.cloud.sap/infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/di-releasepack-installer:build_18024 not found
  ```
  ```
  image com.sap.dsp.linuxx86_64/jupyter:0.1.71 missing in source registry SAP (di-dev-cicd-docker.int.repositories.cloud.sap/infrabox/hanalite-releasepack)
  ```
  ```
  images [di-dev-cicd-docker.int.repositories.cloud.sap/infrabox/hanalite-releasepack/com.sap.bds.docker/storagegateway:2006.0.9] push fail! retry...
  ```
- Bug for `docker.wdf.sap.corp`
  > Typical failures for docker pull from `docker.wdf.sap.corp`
  ```
  "Error reading config blob sha256:36000a9c53241f0d3288ce09c10ccfb2282527d9421b9673a032dd27eef35b26: Invalid status code returned when fetching blob 500 (Internal Server Error)" 
  ```
  ```
  received unexpected HTTP status: 503 Service Unavailable
  ```
  ```
  docker: Error response from daemon: received unexpected HTTP status: 500 Internal Server Error.
  ```
  ```
  Error determining manifest MIME type for docker://public.int.repositories.cloud.sap/com.sap.datahub.linuxx86_64/XXX: Error reading manifest 2006.0.18 in public.int.repositories.cloud.sap/com.sap.datahub.linuxx86_64/XXX: manifest unknown: The named manifest is not known to the registry.
  ```
  ```
  docker: Error response from daemon: error parsing HTTP 400 response body: invalid character '<' looking for beginning of value: "<html>
  ```
- Bug for `IM(infrastructure Manager)`
  > Typical failure in `k8screation` or `dhaas_creation` job
  ```
  Request got exception for HTTPSConnectionPool(host='im-api.datahub.only.sap')
  ```
  > Typical failure in `install` or `dhaas_creation` job, `Data source systems` failure
  ```
  create_and_check_connection_with_retry - ERROR - 111 - check connection DI_DATA_LAKE is not ready, retry!
  create_and_check_connection_with_retry - ERROR - 114 - error when creating connection DI_DATA_LAKE, exit!
  ```

- Bug for `DI CI test infrastructure`
  > Typical failure, in  `k8screation` or `dhaas_creation` job console, IM return quota is full.
  ```
  status_code:500,
      content:{
          "error": "Exceed maximum number of clusters"
      }
  ```
- Bug for `DI Control center`
  > Typical failure, in `dhaas_creation` job console, IM return error or timeout status.
  ```status_code:200,
    content:{
    "cluster_status": "error", 
    "status": "200
  ```

## Components in CI JIRA projects
[Link to wiki](https://wiki.wdf.sap.corp/wiki/display/Odin/Create+infra+service+Issues)

