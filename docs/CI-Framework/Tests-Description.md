# Tests

## Hananlite-Releasepack-nightly-dev

[Test Plans](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/refs/heads/stable/TestCycleConfiguration/TestPlans.json)

The validation jobs are definited in plans named *hanalite_releasepack_night_dev_gke*, 
*hanalite_releasepack_night_dev_eks*, *hanalite_releasepack_night_dev_gardener_aws*,
*hanalite_releasepack_night_dev_aks*, *hanalite_releasepack_night_dev_dhaas_aws*.

the TestCycle name is *NIGHTLY_VALIDATION_debug*.

[Infrabox Project](https://infrabox.datahub.only.sap/dashboard/#/project/Hananlite-Releasepack-nightly-dev)

Details:
Triggered every night by a Cronjob using the *Stable* branch. (since 2018-11-13)

Runs from every Monday-Friday at 3:00 AM German time

Contains unstable tests

Runs on *Stable* branch. (since 2018-11-13)

## Hananlite-Releasepack-nightly-master-dev

[Test Plans](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/refs/heads/master/TestCycleConfiguration/TestPlans.json)

The validation jobs are definited in plans named *hanalite_releasepack_night_dev_gke*, *hanalite_releasepack_night_dev_eks*, 
*hanalite_releasepack_night_dev_gardener_aws*, *hanalite_releasepack_night_dev_aks*, *hanalite_releasepack_night_dev_dhaas_aws*.

the TestCycle name is *NIGHTLY_VALIDATION_debug*.

[Infrabox Project](https://infrabox.datahub.only.sap/dashboard/#/project/Hananlite-Releasepack-nightly-dev-master)

Details:
Triggered every night by a Cronjob using the *master* branch.

Runs from every Monday-Friday at 1:00 AM German time

Contains unstable tests.

Runs only on GKE platform.

Runs on *master* branch. 

## milestone-validation-master

[Test Plans](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/refs/heads/master/TestCycleConfiguration/TestPlans.json)

The validation jobs are definited in plans named  *milestone_test_plan_gke*, *milestone_test_plan_gardener_aws*,
*milestone_test_plan_eks*, *milestone_test_plan_aks*,
*milestone_test_plan_dhaas_aws*.

the TestCycle name is *MILESTONE_VALIDATION*.

For milestone validation:
[Infrabox project](https://infrabox.datahub.only.sap/dashboard/#/project/milestone_validation/)

## milestone-validation-stable

[Test Plans](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/refs/heads/stable/TestCycleConfiguration/TestPlans.json)

The validation jobs are definited in plans named *milestone_test_plan_gke*, *milestone_test_plan_gardener_aws*,
*milestone_test_plan_aws_eks*, *milestone_test_plan_aks*,
*milestone_test_plan_dhaas_aws*

the TestCycle name is *MILESTONE_VALIDATION*.

For milestone validation:
[Infrabox project](https://infrabox.datahub.only.sap/dashboard/#/project/milestone_validation/)

Details:

When a new version is released, the job will be triggered immediately.

The milestone drop with suffix "-ms" stands for it is build from master branch.
The one without this suffix stands for it is from stable branch.

Uses milestone from [here](https://int.repositories.cloud.sap/artifactory/build-milestones/com/sap/datahub/SAPDataHub)
Uses release from [here](https://int.repositories.cloud.sap/artifactory/deploy-milestones/com/sap/datahub/SAPDataHub)