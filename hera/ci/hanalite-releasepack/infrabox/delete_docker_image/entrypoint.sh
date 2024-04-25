#!/bin/bash
set -ex

if [[ ! -f /infrabox/inputs/mirror_docker_image/image_name_list ]]; then
    echo "image name list not found, exit!"
    exit 0
fi 

AWS_REGION="eu-central-1"
aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
aws configure set region $AWS_REGION
#eval $(aws ecr get-login --no-include-email | sed 's|https://||')
aws ecr get-login

for line in $(cat /infrabox/inputs/mirror_docker_image/image_name_list)
do
    image=`echo $line | cut -d \: -f 1`
    tag=`echo $line | cut -d \: -f 2`
    if [[ ${tag} == build_* ]]; then
        if ! aws ecr --region ${AWS_REGION} batch-delete-image \
            --repository-name dev/${image} \
            --image-ids imageTag=${tag}
        then
            echo "### [level=warning] image ${line} was not removed"
        fi
    fi
done

echo "## Docker images delete finished, exit!"
