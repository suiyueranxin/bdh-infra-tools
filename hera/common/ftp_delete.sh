#!/bin/bash
# $1 host $2 user $3 passwd $4 namespace
set -x
ftp -v -n $1<<EOF
user $2 $3
binary
cd $4
prompt
quote pasv
passive
mdelete *
cd ..
rmdir $4
bye
EOF
