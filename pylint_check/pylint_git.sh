#!/bin/bash

PASS=true

#work_dir=$(pwd |sed 's/.pylint_check//g')
echo "## working dir at ${work_dir}"
echo "## file list details for work dir \n*****\n$(ls -al ${work_dir})\n******\n"
if [ -f $1 ];then
  echo "## file changed list details are \n*****\n$(cat $1)\n*****\n"
else
  echo "## no lint files list" && exit 0
fi

echo "## Start pylint checking"
while read FILE; do
  if [[ $FILE =~ 'library'] ]] ||
     [[ $FILE =~ 'check_vflow_result.py' ]] ||
     [[ $FILE =~ 'check_vsystem_result.py' ]] ||
     [[ $FILE =~ 'app.py' ]] ||
     [[ $FILE =~ 'six.py' ]] ||
     [[ $FILE =~ 'es2csv.py' ]] ||
     [[ $FILE =~ 'odtem' ]] ||
     [[ $FILE =~ 'junit_xml' ]] ||
     [[ $FILE =~ 'registry_auto_clean' ]]; then
    echo "Ignore Pylint:" $FILE
  else
    echo "Start Pylint:" $FILE
    pylint --rcfile=pylint_check/.pylintrc $FILE

    if [[ "$?" == 0 ]]; then
      echo "Pylint Passed: $FILE"
    else
      echo "Pylint Failed: $FILE"
      PASS=false
    fi
  fi
done < $1

if ! $PASS; then
  echo "## Pylint checking FAILED!"
  exit 1
else
  echo "## Pylint checking SUCCEEDED"
  exit 0
fi


