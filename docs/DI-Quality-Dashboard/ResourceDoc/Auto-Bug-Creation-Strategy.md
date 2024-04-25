# Auto Bug Creation Strategy

## Trigger Time

Along with daily job report.

## Supported validations

Milestone validation, Upgrade validation

## Skip job list

These jobs are skipped in auto bug creation due to limitations.

`e2e_scenario_test, e2e_smoke_test`

## Code logic

If a job fails in a validation build, we will analyze whether there is a new bug through below steps:

This image is a flow chart of the bug auto-creation logic.

![logic](https://github.wdf.sap.corp/bdh/bdh-infra-tools/blob/cidoc/hera/docs/images/logic.jpg)

1. Check if the health check and service check passed for current job;

    > <font color=#A52A2A size=4 >**Purpose:**</font> If the job failed due to infrastructure issue, for example, git repository or docker registry couldn't be reached, then no bugs will be created. [This](https://github.wdf.sap.corp/bdh/bdh-infra-tools/blob/cidoc/hera/docs/CI_PRE_CHECK/Ci_Pre_Check.md) is a detailed document for health check and service check.

    1. If there has infrastructure error, do not create new bug, and add message to current job failure comment, return.

    2. If the service or health check passed, go to step 2;

2. Check if the current job has failure comment?

    > <font color=#A52A2A size=4 >**Purpose:**</font> If the job failed due to non-production issue, and Infrastructure team added the failure comment to this job, then we will not create any bug.

    1. If yes, do not create new bug, return.

    2. If no, go to step 3;

3. Check if the current job has bug number?

    1. If yes, do not create new bug, return. 
  
    2. If no, go to step 4;

4. Check if the job has a bug number in the latest validation build?

    > <font color=#A52A2A size=4 >**Purpose:**</font> If a job fails constantly, we will copy the previous bug instead of creating new bugs.

    **Requirements:**> > > > > 
    
    - **The same validation type and same branch;**

    - **Check backward until reaching a job failed with a bug number or passed in a previous validation build.**

    1. If yes, copy this bug number to current job failure reason, return.

    2. If no, go to step 5;

5. Check if the job has a bug number in the other latest validation build?(**DISCARDED**: No nightly validation now.)

    > <font color=#A52A2A size=4 >**Purpose:**</font> If the same job failed both on nightly and milestone validation, we will only create one bug.

    **Requirements:**

    - **Different validation type(milestone<->nightly) but same branch;**

    - **Validation builds of the same day;**

    1. If yes, copy this bug number to the current job failure reason, return.

    2. If no, go to step 6;

6. Check if the current job is included in skipped job list?

    **NOTE:**

    - **For the skipped jobs, we will copy the previous bug instead of creating a new bug.**

    1. If yes, do not create new bug, return;

    2. If no, create a new bug;

        - If the job component is certificated by Bugzilla, bug creation succeeds, return.

        - If the job component is not certificated by Bugzilla, bug creation fails, return.

7. For the bug number copied from previous validation, check the bug status;

    > <font color=#A52A2A size=4 >**Purpose:**</font> If the bug is copied from a previous validation, we will check the bug status, and take different actions accordingly.

    1. If the bug status is `Resolve Fixed`, go to step 6;

    2. If the bug status is `Resolve Duplicate`, check the source bug status,

        - If the source bug status is `Resolve X`, create a new bug, return.

        - Otherwise, update the source bug symptom and attachment. 

    3. If the bug status is `Merge Pending`, do not update bug symptom.

    4. If the bug is of other status, update the bug symptom with `Job still failed in build xxx.xx`, and attach the `KUBECONFIG` file.

8. If the same job failed on all platforms in one validation, only create one bug.

![All Platform Example](https://github.wdf.sap.corp/bdh/bdh-infra-tools/blob/cidoc/hera/docs/images/all_platform_example.jpg)

9. If all vflow_* jobs failed on one platform, and all the tests are skipped, only create one bug.

![All Vflow Example](https://github.wdf.sap.corp/bdh/bdh-infra-tools/blob/cidoc/hera/docs/images/all_vflow_example.jpg)

## New logic in plan

1. Create bug for e2e test case level.

2. Do not create bug when there is a network issue or non-production issue

## Bug pattern created by framework

Refer to [Bug 220159](https://hdbits.wdf.sap.corp/bugzilla/show_bug.cgi?id=220159)

1. Reporter: SAP BDH Infrastructure

2. Assignee: firstly use job owner, if no job owner, use component owner

3. QA Contact: component qa contactor

    **NOTE:**

    If you want to change the `job owner/component owner/QA contact` of a certain job, please contact [Lianjie Qin](mailto:lianjie.qin@sap.com) or [Alan Wang](mailto:alan.wang02@sap.com) for help.     

4. Additional tags: BDH_VAL_TEST,PRODUCT_ISSUE,MILESTONE_VALIDATION/NIGHTLY_VALIDATION/UPGRADE

5. Bug Title:

    [nightly/milestone/upgrade build/version][platform] "<job_name>" failed

6. Attachment: `KUBECONFIG` file

7. Symptom:

    Contains failed job url, job console outputs, component versions, DataHub launch-pad endpoint, dashboard Debugging link, dashboard Log path, failed test count, test error message.

