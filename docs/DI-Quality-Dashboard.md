# DI Quality Dashboard

## 1. Architecture

1.1 System contains three layers
- UI Cockpit implemented by SAPUI5
- Backend restApi implemented by Python Flask
- Backend management database implemented by PostgreSQL
1.2 Each component can be deployed to k8s pods

## 2. Entrypoint

2.1 System Web Site - https://dashboard.datahub.only.sap \
2.2 Rest API Manual - https://api.dashboard.datahub.only.sap:30711/apidocs/

## 3. How to contribute

### 3.1 Feature release

The code of Validation Dashboard is located at [dh-validation-dashboard](https://github.wdf.sap.corp/bdh/dh-validation-dashboard).

There are 2 branches: Master and Dev. Please follow the below standards.
1. Ensure master branch always be a stable branch
2. Dev branch is for feature development
3. Each feature or bug fix should have a [Jira](https://sapjira.wdf.sap.corp/secure/RapidBoard.jspa?rapidView=15529&projectKey=BDHQIT&view=planning&selectedIssue=BDHQIT-692&epics=visible) task tracking
   - Refer to [Standards of JIRA Tasks Management](https://jam4.sapjam.com/blogs/show/i2KoQ7wDWQPVwvt7wUJPRv)
4. After feature finished developing and testing locally, commit and create PR on dev branch for review, a sign-off meeting is optional
   - Pull Request
     - Add clear commit message for each commit in the PR.
     - Only can be merged after at least one reviewer approved.
     - Only the PR Merge Owner could merge PR, if the PR Merge Owner is OOO, the backup owner could help to merge.
     - PR Merge Owner need delete the unused branch after PR is merged.    
5. Before feature released to production env, deploy it to dev env for integration testing
6. After feature tested under dev env, ask Lianjie to deploy it to production env
7. Every sprint only has one release version, containing all the features in this sprint.
8. If there is an emergency bug fix, create a hot-fix branch based on master.
9.  Add pytest for api change.

### 3.2 Database update

1. Test the sqls under dev db,
2. All the sqls for features in one sprint should be included in one file(filename suffix with timestamp),
   - [example](https://github.wdf.sap.corp/bdh/dh-validation-dashboard/pull/25)
3. Send out the PR including sqls change for review,
4. After fully test, ask Lianjie to help deploying the change to production database.

## 4. Contact

[DL DataHub QIT Xian](mailto:DL_5D3FED1D25A752027AC1DCD8@global.corp.sap)
