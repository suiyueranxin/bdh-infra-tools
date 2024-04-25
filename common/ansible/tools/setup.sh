#!/bin/bash

MY_PATH="${BASH_SOURCE[0]}"
export ROOT="$(dirname "$(readlink -f "$MY_PATH")")"

source "$ROOT/utils.sh"

function usage {
  >&2 cat << EOF
Usage:
-y,  --yes             assume yes to all queries and do not prompt
-sd, --skip-docker     skip installing docker
-sx, --skip-xmake      skip installing xmake
EOF
  exit 1;
}

function write_log()
{
  echo -n "$1" >> "$ROOT/setup.log"
  echo "" >> "$ROOT/setup.log"
}

function clean_log()
{
  echo -n "" > "$ROOT/setup.log"
}

function validate_JDK()
{
  # Test if JDK file is correctly installed
  gunzip -c "$1" | tar t > /dev/null
  return $?
}
# Include config if it exists, which can be overriden
[ -f "$ROOT/config.sh" ] && source "$ROOT/config.sh"
for i in "$@"
do
  case $i in
    -h|--help)
      usage
      shift
      ;;
    -y|--yes)
      FORCE_INSTALL="true"
      shift
      ;;
    -sd|--skip-docker)
      INSTALL_DOCKER="false"
      shift
      ;;
    -sx|--skip-xmake)
      INSTALL_XMAKE="false"
      shift
      ;;
    *)
      echo "$i unknown option"
      ;;
  esac
done

##### Set the default values if parameters are not set
if [ -z "$FORCE_INSTALL" ]; then
  FORCE_INSTALL="false"
fi
if [ -z "$INSTALL_DOCKER" ]; then
  INSTALL_DOCKER="true"
fi
if [ -z "$XMAKE_PACKAGE_SOURCE" ]; then
  XMAKE_PACKAGE_SOURCE="https://int.repositories.cloud.sap/artifactory/build-milestones-xmake/com/sap/prd/xmake/xmake/0.9.3-6/xmake-0.9.3-6.tar.gz"
fi
if [ -z "$XMAKE_OUTPUT_PATH" ]; then
  XMAKE_OUTPUT_PATH="$ROOT/xmake"
fi
if [ -z "$INSTALL_XMAKE" ]; then
  INSTALL_XMAKE="true"
fi

if ! test_files_exist $ROOT/../fetch-external-deps.sh; then
  die " Cannot find valid ansible project"
fi

clean_log

####### Install Java if it is not installed
if ! java -version 2>&1 >/dev/null | grep -q "java version" ; then
  echo "JAVA is not installed, installing the latest JDK..."
  install_java
  [ $? == 0  ] && write_log "Java installed"
fi
####### Install xmake
if [ "$INSTALL_XMAKE" == "true" ]; then
  echo "Installing xmake ... "
  mkdir -p "$XMAKE_OUTPUT_PATH"
  install_xmake "$XMAKE_OUTPUT_PATH" "$XMAKE_PACKAGE_SOURCE"
  [ $? == 0  ] && write_log "Xmake installed"
fi

echo "Installing necessary python packages..."
install_python_packages
[ $? == 0  ] && write_log "Python packages installed"

echo "Installing ansible and docker-py..."
install_ansible_dockerpy
[ $? == 0  ] && write_log "ansible and docker-py installed"

echo "Installing external roles and dependencies..."
# go to the ansible project directory
pushd $ROOT/../
  ./fetch-external-deps.sh
  [ $? == 0  ] && write_log "External dependencies installed"
popd
# back to the current directory

if [ -z "$(which mvn)" ]; then
  echo "Installing maven and writing the default settings.xml"
  install_maven
  [ $? == 0  ] && write_log "Maven installed"
fi

# Upgrade the kernel because docker is more stable with this version
if [ "$FORCE_INSTALL" == "false" ] && [ "$( dnsdomainname )" != "mo.sap.corp" ]; then
  while [ "$choice" != "Y" ] && [ "$choice" != "y" ] &&[ "$choice" != "N" ] && [ "$choice" != "n" ]
  do
    read -p "Do you want to upgrade the kernel to 4.4.0-53 (docker is more stable with this version, but upgrading it on your local machine may cause problems) (y/n)?" choice
    case "$choice" in
      y|Y)
        echo "Upgrading the kernal to 4.4.0-53..."
        upgrade_kernel
        [ $? == 0  ] && write_log "Kernal upgraded"
        ;;
      n|N)
        echo "Skip upgrading the kernel.";;
      *)   echo "Invalid input! Please type y or n";;
    esac
  done
else
  echo "Upgrading the kernal to 4.4.0-53..."
  upgrade_kernel
  [ $? == 0  ] && write_log "Kernal upgraded"
fi

# Install Docker
if [ -z "$(which docker)" ] && [ "$INSTALL_DOCKER" == "true" ]; then
  echo "Installing docker... "
  install_docker
  [ $? == 0  ] && write_log "Docker installed"

  write_log "Setup succeed!"
  if [ "$FORCE_INSTALL" == "false" ]; then
    echo -e "
    #####################################################################

    It is required to reboot the system in order to make docker function!

    #####################################################################"
    choice=""
    while [ "$choice" != "Y" ] && [ "$choice" != "y" ] &&[ "$choice" != "N" ] && [ "$choice" != "n" ]
    do
      read -p "Do you want to restart now (y/n)?" choice
      case "$choice" in
        y|Y)
          echo " System is going to reboot soon..."
          sudo reboot ;;
        n|N)
          echo " Please reboot the system manually";;
        *)   echo "Invalid input! Please type y or n";;
      esac
    done
  else
    sudo reboot
  fi
else
  write_log "Setup succeed!"
fi

