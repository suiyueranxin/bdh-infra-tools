OPTIONS=$1
if [[ -z "${OPTIONS}" ]]; then
  eval "$(./install.sh -l | cut -d'/' -f2-3 | awk '{print "aws ecr create-repository --repository-name="$1}')"
else
  eval "$(./install.sh -l | cut -d'/' -f2-3 | awk '{print "aws ecr create-repository --repository-name=${OPTIONS}/"$1}')"
fi
