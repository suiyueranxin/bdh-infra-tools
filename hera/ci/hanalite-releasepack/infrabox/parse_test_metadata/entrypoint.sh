set -x

source /project/common.sh
if [ -d "/project/hanalite-releasepack/" ]; then
    rm -rf /project/hanalite-releasepack
fi
pushd /project
    clone_hanalite_releasepack
popd

if [ -z "$GERRIT_CHANGE_BRANCH" ]; then
    if [ -n "$CODELINE" ]; then
        export GERRIT_CHANGE_BRANCH=$CODELINE
        if [ "$CODELINE" = "master" ]; then
            export MILESTONE_VALIDATION_BRANCH="main"
        else
            export MILESTONE_VALIDATION_BRANCH=$CODELINE
        fi
    else
        echo "Codeline is not specified, exit"
        exit 1
    fi
else
    if [ "$GERRIT_CHANGE_BRANCH" = "master" ]; then
        export MILESTONE_VALIDATION_BRANCH="main"
    else
        export MILESTONE_VALIDATION_BRANCH=$GERRIT_CHANGE_BRANCH
    fi
fi

if [ -z "$VORA_VERSION" ]; then
    if [ -n "$RELEASEPACK_VERSION" ];then
        export VORA_VERSION=$RELEASEPACK_VERSION
    fi
fi    
pushd /project/hanalite-releasepack
    if [ -n "$VORA_VERSION" ]; then
        branch=(git tag | grep /$VORA_VERSION | grep "rel")
        if [ "$branch" = "main" ]; then
            branch="master"
        git checkout $branch
    else
        git checkout $GERRIT_CHANGE_BRANCH
    fi
    get_component_version_from_pom
popd

if ! [ -f /infrabox/output/env.sh ]; then
    echo "get component pom failed"
    exit 1
fi
pushd /project
    if [ -d "/project/milestone-validation/" ]; then
    rm -rf /project/milestone-validation
    fi
    clone_repo "git@github.wdf.sap.corp:bdh/milestone-validation.git" $MILESTONE_VALIDATION_BRANCH
    template_file=/project/milestone-validation/database/temp_details/validation_jobs.json
    pushd /project/milestone-validation
        git checkout $MILESTONE_VALIDATION_BRANCH
        if ! [ -f "${template_file}" ]; then
            echo "get validation job templates failed"
            exit 1
        fi
        cp ${template_file} /project/validation_jobs.json
    popd
popd

python3 /project/entrypoint.py
