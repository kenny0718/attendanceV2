#!/bin/bash
# Git pull with password authentication
export GIT_SSH_COMMAND="ssh -p 2288 -o PreferredAuthentications=password -o PubkeyAuthentication=no"
cd /opt/attendance-system
git pull "$@"
