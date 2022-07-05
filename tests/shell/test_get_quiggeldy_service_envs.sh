#!/bin/bash
set -euo pipefail
shopt -s expand_aliases

source $MODULESHOME/init/bash
module load slurm-singularity/current

# Use perl for shebang-aware execution of the (not yet executable) script prior to installation
alias quiggeldy_envs="perl ${WAF_TOPLEVEL}/tools-slurm/src/shell/quiggeldy_envs"

quiggeldy_envs
