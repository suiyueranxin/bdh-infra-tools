# How To Contribete
## CI framework
- Code Contribution
    - Two branches (master & stable)
        - master : Aim to test the code from master branch of [hanalite-releasepack](https://git.wdf.sap.corp/#/admin/projects/hanalite-releasepack).
        - stable : Aim to test the code from stable branch of [hanalite-releasepack](https://git.wdf.sap.corp/#/admin/projects/hanalite-releasepack).

        You can merge your code to the branch according to your need.
    
    - How to merge
        - Fork your own copy of this project to your account.
        - Submit the code to your project.
        - Create a new pull request from the branch of your project to the branch you want to update of this project.
        - Add [Max Zhang](mailto:max.zhang@sap.com) (*I322966*), [Edward Wang](mailto:edward.wang@sap.com) (*I345803*) and [Jing Li](mailto:jing.li08@sap.com) (*I505740*) as reviewers, and send a slack message or an email to the people above.
        - Code will be merged after their approval.

- [Quick Start of CI Framework Code Test]()

## Quality Dashboard

- Code Contribution
    - Master branch: always be a stable branch
        - Master : https://github.wdf.sap.corp/bdh/dh-validation-dashboard/tree/master

    - Dev branch: contains all the features under development
        - Dev : https://github.wdf.sap.corp/bdh/dh-validation-dashboard/tree/dev
    
    - How to merge
        - Checkout dev branch      
            1. If you are a new contributor for project, checkout the dev branch code into local
                > git clone -b dev  https://github.wdf.sap.corp/bdh/dh-validation-dashboard/tree/dev
            2. If you want to update the latest code for dev branch, and merge into your private branch(bug-179337)
                > git checkout dev

                > git pull

                > git checkout bug-179337

                > git merge dev
        - Create a private branch for development usage
            > git branch bug-179337 dev

            > git checkout bug-179337
        - Merge code from private branch to dev branch
            > git add -p

            > git commit -m "[restapi] add daily job report"

            > git push origin bug-179337        
        - Create a new pull request from the private branch to the dev branch.
        - Add one or more people as reviewers.
        - Code will be merged after at leaset one reviewer' approval.

- Quick Start
    - UI part
        - Refer to [UI reademe](https://github.wdf.sap.corp/bdh/dh-validation-dashboard/blob/master/ui/README.md)

    - RestApi part
        - Refer to [Restapi readme](https://github.wdf.sap.corp/bdh/dh-validation-dashboard/blob/master/restapi/README.md)
