#!/bin/bash
# $1 host $2 user $3 passwd $4 namespace $5 abs folder to save the download file
set -x
ftp -v -n $1<<EOF
user $2 $3
binary
cd $4
lcd $5
prompt
quote pasv
passive
mget *.zip
bye
EOF
