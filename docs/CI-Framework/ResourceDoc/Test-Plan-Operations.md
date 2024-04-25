
## Add Test Job
### Add an existing Test Job into a Sub Test Plan
Suppose you need to add a Test Job _dummy_test_ that is already running in a `developing nightly validation` Sub Test Plan named _hanalite_releasepack_night_dev_gke_ into another `milestone validation` Sub Test Plan named _milestone_test_plan_gke_. 
1. Clone the [hanalite-releasepack](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/) project.
2. Checkout the branch that you want to run your Test Job against.
3. Edit [TestPlans.json](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/master/TestCycleConfiguration/TestPlans.json), and copy your Test Job block from _hanalite_releasepack_night_dev_gke_ to _milestone_test_plan_gke_
```
    {
        "infrabox_job": "dummy_test",
        "environment": {}
    }
```
4. Push changes and request [Gordon](gordon.gaumnitz@sap.com) or [Tugba](tugba.bodrumlu@sap.com) to review and merge.  

### Register a new Test Job

1. Email to [**DL BDH-CI-TEST-MANAGEMENT**](mailto:DL_5D312A41FFBDC902798EEC25@global.corp.sap) with the following content:
     - Requested changes are for branch(es):
       - [ ] master
       - [ ] stable
       - [ ] both
    - Requested changes are for jobs configured in platform(s):
      - [ ]  GKE
      - [ ]  AZURE-AKS
      - [ ]  AWS-EKS
      - [ ]  GARDENER-AWS
      - [ ]  DHAAS-AWS
    - Test job name: must end with suffix "_\_test_"
    - Test job run time enviroment: _e.g: "SKIP_TEST": "DUMMY_TEST1"_ .(**Optional**)
    - Component Name: must be chosen from the **Component** drop-down list in Bugzilla-Product:Data Hub 
    -	Job Timeout: defaults to 1 hour
    -  Dockerfile : https://github.wdf.sap.corp/velocity/data-tools-ui/blob/stable/Dockerfile (**Optional** If you have already built and pushed the Dockerfile, continue reading)
    -  Docker images pushed to registory: (**Optional** If you set the Dockerfile). _e.g.: docker.wdf.sap.corp:51022/com.sap.datahub.linuxx86_64/vsolution-integratio:<vsolution_version>_
    - [Test cycle](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/master/TestCycleConfiguration/TestCycle.json) that you want to add to: _e.g.: PUSH_VALIDATION_
2. **Xi'an team**([DL BDH-CI-TEST-MANAGEMENT](mailto:DL_5D312A41FFBDC902798EEC25@global.corp.sap)) will register the madatory information in back-end DB tables. 
   _e.g.: 
   - Insert test case name, platform information, branch information, dependency order infomation into DB tables.
   - **Xi'an team**([DL BDH-CI-TEST-MANAGEMENT](mailto:DL_5D312A41FFBDC902798EEC25@global.corp.sap)) will add configuration into GKE test template table as the following:
   ```
           {
            "security_context": {
                "privileged": true
            },
            "name": "dummy_test_gke",
            "docker_file": "hera/ci/hanalite-releasepack/infrabox/build_and_run/Dockerfile",
            "depends_on": [
                {
                    "on": [
                        "finished"
                    ],
                    "job": "k8s_creation_gke"
                },
                {
                    "on": [
                        "finished"
                    ],
                    "job": "install_gke"
                }
            ],
            "build_only": false,
            "environment": {
                "CONTINUES_INTEGRATION": "TRUE",
                "PARENT_INSTALL_JOB": "install_gke"
            },
            "timeout": 3600,
            "deployments": [
                {
                    "always_push": "true",
                    "host": "di-dev-cicd-docker.int.repositories.cloud.sap",
                    "type": "docker-registry",
                    "repository": "bdh-infra-tools/troubleshooting/dummy_test_gke"
                }
            ],
            "type": "docker",
            "resources": {
                "limits": {
                    "cpu": 2,
                    "memory": 2048
                }
            }
        }
   ```
3. **Xi'an team**([DL BDH-CI-TEST-MANAGEMENT](mailto:DL_5D312A41FFBDC902798EEC25@global.corp.sap)) will edit the [TestPlans.json](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/master/TestCycleConfiguration/TestPlans.json) and add the new Test Job accordingly.
4. **Xi'an team**([DL BDH-CI-TEST-MANAGEMENT](mailto:DL_5D312A41FFBDC902798EEC25@global.corp.sap)) will push changes and request [Gordon](gordon.gaumnitz@sap.com) or [Tugba](tugba.bodrumlu@sap.com) to review and merge.   

## Update Test Job
- Developer could change the Test Job logic by either of the two ways.
    - [ ] [**Preferred**] Push the change to [TestPlans.json](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/master/TestCycleConfiguration/TestPlans.json) to change the job run time enviroment.
    - [ ] Change test code in it's own repository.


## Remove Test Job

### Remove a Test Job from a Sub Test Plan

1. Clone the [hanalite-releasepack](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/) project.
2. Checkout the branch that you want to run your Test Job against.
3. Edit [TestPlans.json](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/master/TestCycleConfiguration/TestPlans.json), and remove your Test Job dic from a _test_plan_ dic.
4. Push changes and request [Gordon](gordon.gaumnitz@sap.com) or [Tugba](tugba.bodrumlu@sap.com) to review and merge.  

### Remove a Sub Test Plan from a Test Cycle
1. Clone the [hanalite-releasepack](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/) project.
2. Checkout the branch that you want to run your Test Job against.
3. Edit [TestCycle.json](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/master/TestCycleConfiguration/TestCycle.json), and remove a _test_plan_name_ from a _test_cycle_name_ dic.
4. Push changes and request [Gordon](gordon.gaumnitz@sap.com) or [Tugba](tugba.bodrumlu@sap.com) to review and merge.


## Appendix
  - For how to manipulate `TestPlans.json` and `TestCycle.json`, please check out [Test Cycle Management](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/master/TestCycleConfiguration/ReadMe.md).
  
  -  Terminology
        - **milestone validation**: Validation for each milestone release. It download the DH installer from artifactory.
        > [Infrabox Project](https://infrabox.datahub.only.sap/dashboard/#/project/milestone_validation)
      - **developing nightly validation**: Validation for all unstable or developing test jobs.
        > [Infrabox Project(master branch)](https://infrabox.datahub.only.sap/dashboard/#/project/Hananlite-Releasepack-nightly-dev-master/) 

        > [Infrabox Project(stable branch)](https://infrabox.datahub.only.sap/dashboard/#/project/Hananlite-Releasepack-nightly-dev)
      - **push validation**: Validation for all git commit against **hanalite-releasepack** project.
        > [Infrabox Project](https://infrabox.datahub.only.sap/dashboard/#/project/hanalite-releasepack/)
