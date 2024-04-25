# Upgrade in Other Validations

## Upgrade in Push Validation

In some cases, developers need to validate their submitted code with Upgrade Tests. 

[Infrabox Project](https://infrabox.datahub.only.sap/dashboard/#/project/hanalite-releasepack)

You can add some comments in your commit message which can choose the test plans that you need or use .

Comments | Example | Function
---------|---------|------------
test_cycle | "infrabox: test_cycle=PUSH_VALIDATION_upgrade" | Give the test cycle that you want to run in your validation.
test_cycle_include | "infrabox: test_cycle_include=hanalite_releasepack_update_validation" | Run the test cycle including this test plan.
test_cycle_exclude | "infrabox: test_cycle_exclude=hanalite_releasepack_update_validation" | Run the test cycle excluding this test plan.
test_cycle_platform | "infrabox: test_cycle_platform=GKE,EKS" | Run the test cycle on the platforms you want.
upgrade_test | "infrabox: upgrade_test" | Run push validation with upgrade test.

## Add Upgrade Validation to Your Own Tests


#### Add a Test Plan to [TestPlan.json](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/refs/heads/master/TestCycleConfiguration/TestPlans.json).

```
{
    "name": "hanalite_releasepack_update_validation",
    "platforms": [
        "GKE"
    ],
    "test_plan_type": "upgrade",
    "tests": [
        ... # Jobs that you want to run after upgrade.
    ]
}
```

#### Add Test Cycle with the Test Plan to [TestCycle.json](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/refs/heads/master/TestCycleConfiguration/TestCycle.json).

The type of test cycle need to be end with "_upgrade".

```
{
    "type": "VSYSTEM_VALIDATION_upgrade",
    "plans": [
        "vsystem_validation_gke_plan",
        "hanalite_releasepack_update_validation"
    ]
}
```
