bdh-infra-tools integration test runtime
====================

Wrap customized component test(based on Dockerfile(example: hanawire test) or docker image(example: vit based tests))

Build/push command
---------------

On the project root folder

```
docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/bit-runtime:${version} -f hera/ci/hanalite-releasepack/infrabox/build_and_run_images/Dockerfile .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/bit-runtime:${version}
```
PS: version is from ./version.txt

****************************************************************************
Update the new image version : di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/bit-runtime:${version}
in the following files:

bdh-infra-tools:
docs/CI-Framework/Component-E2E-validation.md   (1 example uses this image )
hera/di_backup_milestone_test_on_cloud.json   (3 jobs uses this image)
hera/di_backup_milestone_test_on_premise.json (16 jobs uses this image)
hera/ci/hanalite-releasepack/infrabox/build_and_run_images/version.txt

milestone-validation:
database/temp_details/validation_jobs.json  (52 jobs uses this image)
infrabox/generator/infrabox.json  (22 jobs uses this image)

test-image-validation:
template/infrabox.json  (1 job uses this image)

****************************************************************************

Misc
---------------

Once the new version of image is updated, to use it please update all related job template.
