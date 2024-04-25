#!/bin/bash
set -x
# $1 host $2 user $3 passwd $4 namespace $5 upload file local path
ftp -v -n $1<<EOF
user $2 $3 
binary
mkdir $4
cd $4 
lcd $5
prompt
passive mode
mput *.zip
bye
EOF
