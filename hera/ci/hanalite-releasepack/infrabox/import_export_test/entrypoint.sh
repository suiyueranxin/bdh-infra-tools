#!/usr/bin/env bash
set -x
if [ -n "${PARENT_INSTALL_JOB}" ]; then
  if [ ! -f /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh ]; then
    echo "/infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh does not exist. Skip the current job"
    exit 0
  else
    source /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh
  fi
else
  echo "## Skip sourcing env.sh, Using external env information..."
fi

source /project/common.sh

TOOLS="/infrabox/inputs/${PARENT_INSTALL_JOB}/tools.tgz"
if [ ! -f "${TOOLS}" ]; then
  # use the import.sh export.sh from hanalite-releasepack
  mkdir -p /tools
  cp /infrabox/inputs/${PARENT_INSTALL_JOB}/*.sh /tools
  chmod +x /tools/*.sh
else 
  tar -zxvf ${TOOLS} -C /
fi

echo "##start import export testing..."
PROVIDE_SQL="provided_sql.sql"
EXPORTED_SQL="exported_sql.sql"
CHECK_STRING="IMPORT_SH_TEST_T1"
# untar the install package
pushd /
  echo "CREATE TABLE IMPORT_SH_TEST_T1(C INTEGER) TYPE DATASOURCE;" > ${PROVIDE_SQL}
  ./tools/import.sh -n=${NAMESPACE} ${PROVIDE_SQL}
  IMPORT_RESULT=$?

  rm -f ${EXPORTED_SQL}
  ./tools/export.sh -n=${NAMESPACE} ${EXPORTED_SQL}
  EXPORT_RESULT1=$?

  grep ${CHECK_STRING} ${EXPORTED_SQL}
  EXPORT_RESULT2=$?

  if [[ $EXPORT_RESULT1 != 0 || $EXPORT_RESULT2 != 0 ]] ; then
    EXPORT_RESULT=1
  else
    EXPORT_RESULT=0
  fi
popd

python /project/check_import-export_status.py $IMPORT_RESULT $EXPORT_RESULT

if [[ $IMPORT_RESULT != 0 ]];then
  echo "import test failed!"
  exit 0
fi

if [[ $EXPORT_RESULT1 != 0 ]];then
  cat ${EXPORTED_SQL}
  echo "export test failed!"
  exit 0
fi

if [[ $EXPORT_RESULT2 != 0 ]];then
  cat ${EXPORTED_SQL}
  echo "the ${EXPORTED_SQL} doesn't contain string ${CHECK_STRING}"
  exit 0
fi

rm -rf /tools
echo "import export testing done"