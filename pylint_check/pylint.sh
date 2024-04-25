#!/bin/bash

function validate_python_code() {
    FILES=$(find ../ | xargs ls -ld | grep "\.py\{0,1\}$" | awk -F '[ ]' '{ print $NF }')
    if [[ "$FILES" = "" ]]; then
        return 0
    fi
    echo "Validating python code:"
    for FILE in $FILES ; do
        # flie with libary/app/six/junit_xml/registry_auto_clean are imported from the 3 libs, please ignore
        # file with odtem/check_vflow_result.py/check_vsystem_result.py are deprecated, please ignore
        if [[ $FILE =~ 'library' ]] ||
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
            pylint $FILE
            if [[ "$?" == 0 ]]; then
                echo "Pylint Passed: $FILE"
            else
                echo "Pylint Failed: $FILE"
                PASS=false
            fi
        fi
    done
    echo "Python code validation completed!"
    return 1
}

PASS=true

validate_python_code

if ! $PASS; then
    echo "Please fix the ESLint and Pylint errors and try again."
    exit 1
else
    echo "COMMIT SUCCEEDED"
fi
