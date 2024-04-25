#!/bin/sh -e

echo "## cloning repository"
chmod a-rw /root/.ssh/*
chmod u+rw /root/.ssh/*

mv /root/.ssh/infrabox_key /root/.ssh/id_rsa
mv /root/.ssh/infrabox_key.pub /root/.ssh/id_rsa.pub

git config --global http.sslverify false
git config --global submodule.fetchJobs 5 # supported in git >= 2.9
git clone --recurse-submodules \
  ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-vora \
  /vora
