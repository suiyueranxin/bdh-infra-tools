#!/bin/sh
echo "## copy /infrabox/context to /infrabox/output/context"
# we need to exclude .infrabox because this contains /infrabox/output
rm -rf /infrabox/output/context
mkdir /infrabox/output/context
cd /infrabox/context
tar cf - --exclude=.infrabox  . | tar xf - -C /infrabox/output/context/
