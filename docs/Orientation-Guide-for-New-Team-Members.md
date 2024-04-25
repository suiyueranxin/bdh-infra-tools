# Orientation Guide for New Team Members

Welcome! This is a very short guide to help you to prepare your working environment and get familiar with our products.

- [Prepare](#Prepare)
    - [Setup Work Place and Prepare Your Laptop](#Setup-Work-Place-and-Prepare-Your-Laptop)
    - [Say Hello to Team Members](#Say-Hello-to-Team-Members)
    - [Gerrit](#Gerrit)
    - [Slack](#Slack)
    - [JAM](#JAM)
    - [Jira](#Jira)
        - [Standards of Jira Task Management](#Standards-of-Jira-Task-Management)
- [Training Topics](#Training-Topics)
    - [Git & Github](#Git-amp-Github)
        - [Useful Resources](#Useful-Resources)
        - [Practice](#Practice)
    - [Docker](#Docker)
        - [Concept](#Concept)
        - [Practice](#Practice-1)
    - [Ansible](#Ansible)
    - [Kubernetes](#Kubernetes)
        - [Concept](#Concept-1)
        - [Practice](#Practice-2)
    - [Infrabox](#Infrabox)
    - [CI Framework](#CI-Framework)
    - [Validation Dashboard](#Validation-Dashboard)
- [Advanced Training Topics](#Advanced-Training-Topics)
    - [Python](#Python)
-[Appendix](#Appendix)
    - [Useful Links](#Useful-Links)
    - [Tools](#Tools)

## Prepare

### Setup Work Place and Prepare Your Laptop

Please
1. sign in Windows OS with your I-number
2. make sure outlook (the e-mail client) works well
3. sign in Skype for Business and send a testing message to other colleagues (you can find user, say "Max Zhang", in the search area)
4. install Chrome and SwitchyOmega plugin then ask your teammates for a proxy setting.
  - Proxy servers

    `http:proxy.wdf.sap.corp:8080`

    `https:proxy.wdf.sap.corp:8080`
  - Rule List Config

    `AutoProxy - https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt`
5. install Slack, see [Slack](#Slack).
6. install Microsoft Teams for team cooperation.
6. install development tools.

    For CI validation
    - git client
    - vscode + pylint plugin
    - postman
    - docker client
    - pgAdmin
    
    For Validation Dashboard:
    - git client
    - install VSCode, and config the linting plugin: 
      - backend restAPI: refer to [Pre-requisite](https://github.wdf.sap.corp/bdh/dh-validation-dashboard/tree/master/restapi#pre-requisite)
      - frontend UI: refer to [VSCode setting](https://github.wdf.sap.corp/bdh/dh-validation-dashboard/tree/master/ui#vscode-setting)
    - postman
    - pgAdmin


### Say Hello to Team Members

Please prepare an email and say hello to [all the Xi'an Big Data Team members](mailto:DL_5C32B9CE2FB45902868B2F3F@global.corp.sap).


### Github Enterprise for SAP

SAP has an internal github service at https://github.wdf.sap.corp/ which serves all the internal DHaaS and other projects repository.

Please
1. Activate your account with the Github Self-Service(there is a link for creating a new account under the sign in page).
2. Change your password by clicking the "Forgot password" link.
3. Send an email about your account(your employee number) and the organization(BigDataDevOps) that you would join to [jing-tao.li@sap.com](mailto:jing-tao.li@sap.com).
4. Try to clone the git repository from:

    Repository          |                Description                      |
    ------------------------------------------------|---------------------|
    https://github.wdf.sap.corp/bdh/bdh-infra-tools | CI framework  |
    https://github.wdf.sap.corp/bdh/milestone-validation| milestone validation |
    https://github.wdf.sap.corp/velocity-infra/trigger-milestone-validation| upggradeing & backup-restore validation|
    https://github.wdf.sap.corp/bdh/dh-validation-dashboard | validation Dashboard |

### Gerrit

Get familiar with Gerrit Code Review system

Here's some useful links
- [Git explained: Git Concepts and Workflows](https://docs.google.com/presentation/d/1IQCRPHEIX-qKo7QFxsD3V62yhyGA9_5YsYXFOiBpgkk/edit?usp%3Dsharing)
- [Gerrit explained: Gerrit Concepts and Workflows](https://docs.google.com/presentation/d/1C73UgQdzZDw0gzpaEqIC6SPujZJhqamyqO1XOHjH-uk/edit?usp%3Dsharing)
- Add your ssh public key into our gerrit project: https://git.wdf.sap.corp/#/dashboard/self -> top-right -> settings -> SSH Public Keys -> Add Key
- Try to clone hanalite-releasepack: ```git clone ssh://your-i-number@git.wdf.sap.corp:29418/hanalite-releasepack```

### Slack

Slack is the most used application to communicate with other colleagues.

Please
1. open "Software Center" application
2. search for "Slack" and install it
3. register slack account with your SAP email
4. ask your teammates to invite you to the channels.
    -   dh-quality-infrastructure-team
    -   dh-push-validation
    -   dh-ci-status

### JAM

SAP JAM serves the project and team homepages.  

Please visit https://jam4.sapjam.com/home and ask your teammates to
invite you to our groups.

### Jira

Jira is used as QIT agile project management and bug tracker.

Please visit the [BDHQIT]](https://sapjira.wdf.sap.corp/projects/BDHQIT/issues/BDHQIT-1114?filter=allopenissues) in JIRA. Ask your teammates for help if you have any problem.

#### Standards of Jira Task Management 
Who creates his task needs to define the AC (acceptance criteria) and write it down in the task details. Who is assigned to the task needs to check the AC before sets its status as done.

2 types of tasks we use in Jira
 - Features:
1. Every feature needs an eipc story to trace.
2. Epic stories has at least 1 user story. The user story may have several tasks.
3. Measure the planned tasks by T-SHIRT SIZE, XXS(1), XS(2), S(4). If the size is bigger than M, it needs to be split or it could not be added to the plan. (Start from next sprint)

 - Bugs:
1. We use two special epic stories to manage the bugs. 
2. There're 3 types of tasks included in these tow epic stories: Planned Bug Fix; Emergency Bug Fix; Improvements. And we use different methods to mark them as the following graph shows.
![JIRA-Bugs](https://github.wdf.sap.corp/bdh/bdh-infra-tools/blob/master/hera/docs/images/JIRA-Bugs.svg)     

## Training Topics

### Git & Github

#### Useful Resources

- [Hello World - Github Guides](https://guides.github.com/activities/hello-world/)
- [https://guides.github.com/introduction/flow/](https://help.github.com/en/articles/about-pull-requests)
- [Understanding the GitHub flow](https://nvie.com/posts/a-successful-git-branching-model/)


#### Practice

1. prepare your git client
2. learn the basic usage of git
   + create a repo
   + clone a repo
   + make change to it
   + commit and amend the commit message
   + create branch
   + merge branches
   + rebase a branch
   + fetch a remote branch
   + cherry-pick commit from one branch to another
   + review history and changes
3. get familiar with GitHub Pull Request workflow
   + create a new PR
   + comments on PR
4. get familiar with Git branching model

### Docker

#### Concept

Try to answer the following questions
- What is Docker?
- Where to find docker image?
- How to build a docker image?
- How to write a Dockerfile?
- Explain the Docker Architecture
- List the basic usage of docker subcommands

#### Practice

1. install Docker CE in your monsoon host or laptop
2. write a simple http server in your favorate program language
3. write a Dockerfile and pack this http server program into a docker image
4. tag the docker image with version =v0.0.1=
5. run the docker image
6. visit the service
7. access the container log
8. stop the container and remove the image

### Ansible

***Try to***
1. know what's the playbook, role.
2. know how to set the condition check
3. know how to set and use local and global variables
4. useful link [ansible guide](https://www.tutorialspoint.com/ansible/index.htm)

### Kubernetes

#### Concept

Try to answer the following questions
- What is Kubernetes?
- What is Pod?
- What is Service?
- What is label selector?
- What's the difference between /Pod/ and /Container/?
- What's the difference between /StatefulSet/ and /Deployment/?
- How to configure /kubectl/?
- What's the difference between `kubectl apply` and `kubectl create`
- What is PV? and what is PVC?

#### Practice

1. create a k8s cluster in IM
2. write a yaml file for Redis Deployment
3. apply the Deployment
4. create a service
5. access the service
6. delete the resources you have created

### Infrabox

Search for resources about [Infrabox](https://github.com/SAP/InfraBox) 

1. Create an infrabox project in your own [infrabox dashboard](https://infrabox.datahub.only.sap/)
2. Install a infrabox client and try to push an infrabox build.
3. Try to explain how to transfer files between jobs.
4. Try to explain the difference for the job types below:
    - docker
    - docker-image
    - docker-compose
    - git
    - workflow
5. Try to explain the infrabox workflow of this project
https://github.wdf.sap.corp/bdh/bdh-infra-tools/blob/master/hera/infrabox_hanalite-releasepack_generator.json

### CI Framework

Follow the [CI Framework Introduction](CIFramework.md) and try to explain the questions below:
1. how does the push validaiton in releasepack been triggered ?
2. how does the milestone validation been triggered ?
3. how does the upgrading and backup/restore validation been triggered ?
4. how to tell if a job failure is caused by CI framework or not ?
5. how to manage the test plans ?
6. how to add a new validation job into CI frarmework ?
7. how to check the report via Quality Dashboard ?

### Validation Dashboard

[Project Overview](https://github.wdf.sap.corp/bdh/dh-validation-dashboard/blob/master/README.md)

[Validation Dashboard Introduction](DI-Quality-Dashboard/Q-Dashboard-Introduction.md)

Environment setup: [UI](https://github.wdf.sap.corp/bdh/dh-validation-dashboard/blob/master/ui/README.md) and [restApi](https://github.wdf.sap.corp/bdh/dh-validation-dashboard/blob/master/restapi/README.md)

[Database Introduction](DI-Quality-Dashboard/Q-Dashboard-Database-Introduction.md)

[How to contribute](How-To-Contribute.md#quality-dashboard)

After reading these documents, you should be able to finish the below tasks:
1. know what's the usage of the validation dashboard
2. set up the local environment for UI and restApi

   Access the below url to verify:
    - UI: http://localhost:10000/index.html#home
    - restApi: http://0.0.0.0/api/v1
3. debug the restapi code through VSCode
4. debug the UI code through chrome
5. logon the test database with pgAdmin
6. run pytest
7. commit your code change into dev branch
8. build and run a docker image for restAPI and UI

## Advanced Training Topics

### Python

- Learn the basic language: data type, OOP, list comprehensive, decorator, module, package, functional programming
- Learn python's standard library
- Build your python local development environment
- Learn the python module/package management policy

## Appendix

### Useful Links

Page                         | Description                                                                               |
------------------------------|-------------------------------------------------------------------------------------------|
 [Portal Page](https://portal.wdf.sap.corp/)                  | if you are not sure where to find resources, this may be the first page you want to visit |
 [SAP JAM](https://jam4.sapjam.com)                      | JAM serves homepages for projects and teams                                               |
 [Devops Wikipage](https://wiki.wdf.sap.corp/wiki/display/bddevops/)             | Big Data Services DevOps wikipage                                                         |
 https://github.wdf.sap.corp  | SAP internal Github                                                                       |
 https://git.wdf.sap.corp     | SAP internal Gerrit server                                                                |
 https://im.datahub.only.sap/ | Infrastructure Management (IM) homepage                                                      |
 https://sri.wdf.sap.corp/    | The installable software catalog                                                          |
[Data Intelligence Help Portal](https://help.sap.com/viewer/product/SAP_DATA_INTELLIGENCE/Cloud/en-US)  |  Know about DI product

### Tools

Check if the third-party software is legal in the [ SAP Software Rating Information](https://sri.wdf.sap.corp/) website before you install it.

 Tool               | Description                                |
--------------------|--------------------------------------------|
 onedriver          | cloud file system                          |
 onenote            | Note application in Microsoft Office Suite |
 BIG-IP Edge Client | VPN client                                 |
 Putty              | Terminal Emulator                          |
 vscode             | Microsoft Lite Code Editor/IDE             |
 pyCharm            | Intellij Python IDE                        |
 MobaXterm          | Another Terminal Emulator                  |
