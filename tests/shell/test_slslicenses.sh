#!/bin/bash
set -euo pipefail
shopt -s expand_aliases

# Use perl for shebang-aware execution of the (not yet executable) script prior to installation
alias slslicenses="perl ${WAF_TOPLEVEL}/tools-slurm/src/shell/slslicenses"

slslicenses
