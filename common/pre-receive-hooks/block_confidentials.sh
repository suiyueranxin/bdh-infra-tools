#!/bin/bash

#
# ⚠ USE WITH CAUTION ⚠
#
# Pre-receive hook that will block any new commits that contain passwords,
# tokens, or other confidential information matched by regex
#
# More details on pre-receive hooks and how to apply them can be found on
# https://git.io/fNLf0
#
# refer to: https://github.tools.sap/github/pre-receive-hooks/edit/master/scripts/block_confidentials.sh
# ------------------------------------------------------------------------------
# Variables
# ------------------------------------------------------------------------------
# Exit Code
exitCode=0

# Define list of REGEX to be searched and blocked
regex_list=(
  # block any private key file
  '(\-){5}BEGIN\s?(RSA|OPENSSH|DSA|EC|PGP)?\s?PRIVATE KEY\s?(BLOCK)?(\-){5}.*'
  # block AWS API Keys
  'AKIA[0-9A-Z]{16}'
  # block AWS Secret Access Key (TODO: adjust to not find validd Git SHA1s; false positives)
  # '([^A-Za-z0-9/+=])?([A-Za-z0-9/+=]{40})([^A-Za-z0-9/+=])?'
  # block confidential content
  'CONFIDENTIAL'
  # Basic Auth URLS
  # '.*://.*:.*@'
)

# Concatenate regex_list
separator="|"
regex="$( printf "${separator}%s" "${regex_list[@]}" )"
# remove leading separator
regex="${regex:${#separator}}"

# Commit sha with all zeros
zero_commit='0000000000000000000000000000000000000000'

# ------------------------------------------------------------------------------
# Pre-receive hook
# ------------------------------------------------------------------------------
echo "[Block Confidential's] Scanning for sensitive content."

while read oldrev newrev refname; do
  # # Debug payload
  # echo -e "${oldrev} ${newrev} ${refname}\n"

  # ----------------------------------------------------------------------------
  # Get the list of all the commits
  # ----------------------------------------------------------------------------

  # Check if a zero sha
  if [ "${oldrev}" = "${zero_commit}" ]; then
    # The detection range is everything reachable from newrev but not any heads
    start=`git for-each-ref --format='%(refname)' refs/heads/*`
  else
    start=${oldrev}
  fi
  end=${newrev}
  # ----------------------------------------------------------------------------
  # Only detect the difference between before push and after push 
  # ----------------------------------------------------------------------------
  
  # Use extended regex to search for a match. Only *adding* line, which is beginning with "+" will be detected.
  match=`git diff-tree -r -p --no-color --no-commit-id --diff-filter=d ${start} ${end} | grep '^+.*' | grep -nE "(${regex})"`

  # Verify its not empty
  if [ "${match}" != "" ]; then   
    echo -e "[Block Confidential's] Matched \"${match}\""
    exitCode=1
  fi
done

if [ ${exitCode} -gt 0 ]; then
  echo "[Block Confidential(s)] SENSITIVE FILES FOUND, MAKE SURE YOUR REPOSITORY IS PRIVATE OR REMOVE THEM!"
  echo "[Block Confidential(s)] https://help.github.com/articles/removing-sensitive-data-from-a-repository/"
else
  echo "[Block Confidential's] No sensitive content found."
fi

if [ ${GITHUB_REPO_PUBLIC} == "true" ]; then
  exit $exitCode
fi

exit 0