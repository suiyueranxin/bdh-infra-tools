Add the following table to the PR that you add new test code in component repository. Fulfil it according to the criteria to be verified at the code review.

| Criteria                      | Value                                                        |
| :---------------------------- | :----------------------------------------------------------- |
| Test image                    | [i.e: v2.registry.datahub.xxx]                               |
| Branches                      | [master OR other release branches] <br />*Note: for rel-20xx branches, only on-cloud validation be triggered. for rel-3.x branches, only on-prem validation be triggered.* |
| Metadata Provided             | [Yes OR No]                                                  |
| Platform                      | [on-premise(AKS/EKS/GKE) OR on-cloud(DHAAS-AWS) OR Both]     |
| Level                         | [i.e: L3(*system integration*) OR L4(*e2e*) ]                |
| Test Framework                | [i.e: junit, jasmine, pyunit]                                |
| Duration                      | Test execution duration                                      |
| Test job Owner                | email address or DL with 4 colleagues at most                |
| Validation Reports            | Attach the validation reports and resource consumption defined in |
| Resource Consumption          | CPU: [Low OR Medium OR High] Memory: [Low OR Medium OR High] |
| Require Extra Tenant          | [Yes OR No] *If the test require extra tenants besides "default" and "system", set it to "YES"* |
| Interference with other tests | [Yes OR No] <br />*consider if test can run in parallel with others. consider if the tests remove default drivers or connections or disable global feature flags* |

- Resource Consumption:  

  Consider the consumption base on current nodes types in milestone validation:

  *EKS: m4.2xlarge(8U32G), 3 nodes*
  *AKS: Standard_D4_v2(8U28G) , 3 nodes*
  *GKE: n1-standard-8(8U30G), 3 nodes*
  *DHAAS-AWS: m5.2xlarge(8U32G), 6 nodes*

   *CPU:* 

  ​    *"Low" < 1 CPU*

  ​    *"Medium" 1 CPU - 2 CPU.*

  ​    *"High"  > 2 CPU*

  *Memory:*

  ​    *"Low" < 2 G*

  ​    *"Medium" 2G - 6 G*

  ​    *"High"  > 6 G*

- Duration:

  *"Short" < 1h*

  *"Medium" 1h - 2h*

  *"Long" > 2h*

- A sample PR can be verified here: https://github.wdf.sap.corp/bdh/bdh-infra-tools/pull/4481