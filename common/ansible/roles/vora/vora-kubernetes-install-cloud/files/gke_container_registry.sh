gcloud auth activate-service-account --key-file=${1}
gcloud config set project ${2}
gcloud --quiet auth configure-docker
