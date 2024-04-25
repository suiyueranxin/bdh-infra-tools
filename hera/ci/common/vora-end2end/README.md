Vora's End2End build
====================

Utilizes `hanalite-vora <https://git.wdf.sap.corp/#/admin/projects/hanalite-vora>`_ to
execute an end2end build for artifactory artifacts.

input parameter
---------------

* build arg **CODELINE** can be ``master`` or ``stable``
* environment variable **CURRENT_COMPONENT** as the submodule name of the validated component
  within hanalite-vora. Used to overwrite vora's submodule content with infrabox context.
* environment variable **ELVIS_ARG_COMPONENTS** a list of components to include,
  each component prefixed with ``-c ``
  A complete list can be found using ``elvis --component list``. See also
  https://velocity.wdf.sap.corp/documentation/projects/vora/general_usage.html
  To get a Foundation package, this list must contain hanalite-releasepack.

example job config
------------------

```
   {
        "name": "vora-end2end",
        "type": "docker",
        "docker_file": "bdh-infra-tools/hera/ci/common/vora-end2end/Dockerfile",
        "build_only": false,
        "build_arguments": { "CODELINE": "master" },
        "environment": {
            "CURRENT_COMPONENT" : "hanalite-lib",
            "ELVIS_ARG_COMPONENTS" : "-c lib -c jdbc -c spark-datasources -c releasepack"
        },
        "resources": { "limits": { "cpu": 6, "memory": 24567 } },
        "repository": { "submodules": true },
        "timeout": 15000
    }
```
