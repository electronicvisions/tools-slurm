#!/bin/bash
set -euo pipefail
shopt -s expand_aliases

# Use perl for shebang-aware execution of the (not yet executable) script prior to installation
alias listLicences="perl ${WAF_TOPLEVEL}/tools-slurm/src/shell/listLicences"

# test ordinary way
listLicences

# test help
listLicences --help

# test skipping a user
listLicences --skip jgoeltz

# test with a special setup in regex
listLicences --colour W67
