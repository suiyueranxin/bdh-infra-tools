#!/bin/bash

function die()
{
  >&2 echo "ERROR: $*"
  exit 1
}

function until_timeout()
{
  grep -q "^[0-9]\+$" <<< "$1" || die "missing/invalid timeout value"
  to=$(($(date +%s)+$1))
  check_cmd="$2"
  if test -z "$check_cmd"; then
    check_cmd="$(cat)"
  fi

  while (( $(date +%s) <= $to )); do
    if bash -ec "$check_cmd"; then
      echo
      return 0
    fi
    echo -n '.'
    sleep 1
  done
  echo
  die "timeout"
}

# test if files exist
function test_files_exist()
{
  if ls "$1" 1> /dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

# Upgrade the kernel
function upgrade_kernel()
{
  sudo apt-get install linux-image-extra-4.4.0-53-generic --force-yes -y -q
  sudo apt-get install linux-headers-4.4.0-53-generic --force-yes -y -q
}


#### Install docker
function install_docker()
{
  sudo apt-get update
  sudo apt-get install apt-transport-https ca-certificates -q
  sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
  sudo mkdir -p  /etc/apt/sources.list.d

  if grep -q "16.04 LTS (Xenial Xerus)" "/etc/os-release"; then
    OS="UB1604"
    echo "deb https://apt.dockerproject.org/repo ubuntu-xenial main"  > /tmp/docker.ubuntu1604.list
    sudo cp /tmp/docker.ubuntu1604.list /etc/apt/sources.list.d
  else
    OS="UB1404"
    echo "deb https://apt.dockerproject.org/repo ubuntu-trusty main"  > /tmp/docker.ubuntu1404.list
    sudo cp /tmp/docker.ubuntu1404.list /etc/apt/sources.list.d
  fi

  sudo apt-get update
  sudo apt-cache policy docker-engine

  case $OS in
  UB1604)
     sudo apt-get install -y docker-engine=1.12.1-0~xenial -q
     ;;
  UB1404)
     sudo apt-get install -y docker-engine=1.12.1-0~trusty -q
     ;;
  esac

  sudo usermod -aG docker $USER
  sudo service docker stop

  sudo cat > /tmp/docker.default  << END_OF_FILE
# Docker Upstart and SysVinit configuration file
# Customize location of Docker binary (especially for development testing).
#DOCKER="/usr/local/bin/docker"
# Use DOCKER_OPTS to modify the daemon startup options.
# One of the dns addresess (10.58.32.32) is set to SAP internal dns
# DOCKER_OPTS="--dns 10.58.32.32 --dns 8.8.8.8"
# If you need Docker to use an HTTP proxy, it can also be specified here.
  export http_proxy="http://proxy.wdf.sap.corp:8080/"
  export no_proxy=".sap.corp, localhost"
# This is also a handy place to tweak where Docker's temporary files go.
#export TMPDIR="/mnt/bigdrive/docker-tmp"
DOCKER_OPTS="$DOCKER_OPTS --storage-driver=aufs --insecure-registry=ansible-docker-hub.mo.sap.corp:5000"
END_OF_FILE


  sudo mv /tmp/docker.default /etc/default/docker

  if [ "${OS}" == "UB1604" ]; then

     cat >/tmp/docker.service <<EOF
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network.target docker.socket
Requires=docker.socket

[Service]
Type=notify
EnvironmentFile=/etc/default/docker
ExecStart=/usr/bin/docker daemon  --storage-driver=aufs --insecure-registry=ansible-docker-hub.mo.sap.corp:5000 --insecure-registry=docker.mo.sap.corp -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock
MountFlags=slave
LimitNOFILE=1048576
LimitNPROC=1048576
LimitCORE=infinity
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

     cat >/tmp/docker.proxy <<EOF
[Service]
Environment="HTTP_PROXY=http://proxy.wdf.sap.corp:8080/" "NO_PROXY=localhost,127.0.0.1,sap.com,sap.corp"
EOF

     sudo mkdir -p /lib/systemd/system/docker.service.d
     sudo cp /tmp/docker.service  /lib/systemd/system/docker.service.d/docker.service
     sudo mv /tmp/docker.service  /lib/systemd/system/docker.service
     sudo mv /tmp/docker.proxy    /lib/systemd/system/docker.service.d/proxy.conf
     sudo systemctl daemon-reload
  fi

  sudo service docker status
}

function validate_JDK()
{
  # Test if JDK file is valid
  gunzip -c "$1" | tar t > /dev/null
  return $?
}

function install_python_packages()
{
  sudo apt-get update
  sudo apt-get -y install python-dev python-pip libssl-dev -q
  sudo -E pip install -U boto -q
}

function install_ansible_dockerpy()
{
  sudo -E pip install ansible==2.1 markupsafe docker-py==1.9 --force-reinstall -q
}

function install_xmake()
{
  if [ -d $1 ]; then
    pushd "$1"
    wget -q -O xmake.tar.gz "$2"
    tar zxvf ./xmake.tar.gz
    popd
  fi
}

function install_java()
{
  sudo apt-get update
  sudo apt-get install default-jdk --force-yes -y -q
}

function install_maven()
{
  sudo apt-get install maven -q --force-yes -y
  sudo cat > /tmp/mvn_settings.default  << END_OF_FILE
  <settings>
  <proxies>
   <proxy>
      <active>true</active>
      <protocol>http</protocol>
      <host>dewdfwdf03proxy.wdf.sap.corp</host>
      <port>8080</port>
      <nonProxyHosts>*.sap.corp</nonProxyHosts>
    </proxy>
  </proxies>
  <profiles>
    <profile>
      <id>sap</id>
      <activation>
        <activeByDefault>true</activeByDefault>
      </activation>
      <repositories>
        <repository>
          <id>sap-xmake</id>
          <url>https://int.repositories.cloud.sap/artifactory/deploy-milestones-xmake/</url>
          <layout>default</layout>
          <releases>
            <enabled>true</enabled>
          </releases>
        </repository>
        <repository>
          <id>sap-milestones</id>
          <url>https://int.repositories.cloud.sap/artifactory/deploy-milestones/</url>
          <layout>default</layout>
          <releases>
            <enabled>true</enabled>
          </releases>
        </repository>
        <repository>
          <id>sap-snapshots</id>
          <url>https://int.repositories.cloud.sap/artifactory/deploy-snapshots/</url>
          <layout>default</layout>
          <releases>
            <enabled>false</enabled>
          </releases>
          <snapshots>
            <enabled>true</enabled>
          </snapshots>
        </repository>
        <repository>
          <id>deploy-releases</id>
          <url>https://int.repositories.cloud.sap/artifactory/deploy-releases/</url>
          <releases>
            <enabled>true</enabled>
          </releases>
        </repository>
      </repositories>
    </profile>
  </profiles>
</settings>
END_OF_FILE
mkdir -p $HOME/.m2/
sudo mv /tmp/mvn_settings.default $HOME/.m2/settings.xml
}

function remove_docker_containers()
{
  # stop all the running containers
  echo "Stop running containers..."
  if [ -n "$(sudo docker ps -q)" ]; then
    sudo docker stop $(sudo docker ps -q)
  fi
  # remove all the existing containers
  echo "Remove all existing containers..."
  if [ -n "$(sudo docker ps -aq)" ]; then
    sudo docker rm $(sudo docker ps -aq)
  fi
}
export -f remove_docker_containers

function remove_docker_containers_timeout()
{
  until_timeout 20 "remove_docker_containers"
}

function remove_docker_images()
{
  if [ -n "$(sudo docker images -aq)" ]; then
    sudo docker rmi $(sudo docker images -aq)
  fi
}
export -f remove_docker_images

function remove_docker_images_timeout()
{
  until_timeout 20 "remove_docker_images"
}

function remove_docker_network()
{
  if [ -n "$1" ] && [ -n "$(docker network ls -f name=$1 -q)" ]; then
    docker network rm "$1"
  fi
}
export -f remove_docker_network

function remove_docker_network_timeout()
{
  if [ -n "$1" ]; then
    until_timeout 20 "remove_docker_network $1"
  fi
}

function start_docker_containers()
{
  if [ -n "$(sudo docker ps -aq)" ]; then
    sudo docker start $(sudo docker ps -aq)
  fi
}
export -f start_docker_containers

function start_docker_containers_timeout()
{
  until_timeout 60 "start_docker_containers"
}

# check whether available space is less than a given threshold
## $1 is the given threshold
## return 0 if it the available space is less than the threshold; otherwise return 123
function is_avail_space_less_than()
{
  [ -z $1 ] && die "please provide a threshold to check the available space"
  threshold=$1
  avail_space=$(df --total --output=avail | tail -n1)

  if [ $avail_space -lt $threshold ]; then
    return 0
  else
    return 123
  fi
}

# check whether the current docker storage driver is aufs
## return 0 if it is using aufs; otherwise return 123
function is_docker_storage_driver_aufs()
{
  [ ! -f "/etc/default/docker" ] && die "docker config file /etc/default/docker does not exist"
  if ( grep -q "aufs" /etc/default/docker ); then
    return 0
  else
    return 123
  fi
}

# check whether docker containers exist
## return 0 if there is containers otherwise return 123
function is_docker_container_exist()
{
  if [ -n "$(sudo docker ps -aq)" ]; then
    return 0
  else
    return 123
  fi
}
