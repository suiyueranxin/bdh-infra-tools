username=$1
password=$2
registry_name=$3
docker login --username ${username} --password "${password}" ${registry_name}.azurecr.io
