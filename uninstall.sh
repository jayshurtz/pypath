#!/bin/sh

# Uninstall pypath for the current user.
#
# They are forever safe from unfinished or unpackaged Python code.

# Disable user aliases.
unalias -a

# Dirs and commands.
PYC='~/.pypath'
PYD="${HOME}/.pypath"
SITE="${PYD}/site"
ALIAS="alias pypath='source ${PYC}/pypath.sh'"
DFLT="[ -r ${PYC}/default.pth ] && source ${PYC}/default.pth"

# Remove alias & source commands from shell rc files.
cat "${SITE}" | while read -r RCF; do
    grep -v "^${ALIAS}" "${RCF}" > "${RCF}.tmp" && mv "${RCF}.tmp" "${RCF}"
    grep -xFv "${DFLT}" "${RCF}" > "${RCF}.tmp" && mv "${RCF}.tmp" "${RCF}"
done

# Remove pypath directory.
rm -rf "${PYD}"
