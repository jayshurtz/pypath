#!/bin/sh

# Install the pypath tool (to '~/.pypath').
#
# To install pypath for the current user, run './install.sh'.
# To install for a specifc shell, run something like './install.sh ~/.bashrc'.
# The default install target is "~/.*shrc".

# Disable user aliases.
unalias -a

# Dirs and commands.
PYC='~/.pypath'
PYD="${HOME}/.pypath"
SITE="${PYD}/site"
ALIAS="alias pypath='source ${PYC}/pypath.sh'"
DFLT="[ -r ${PYC}/default.pth ] && source ${PYC}/default.pth"

# Get shell rc files to add pypath 'alias' & 'source' commands to.
# At a minimum, create "~/.bashrc" if it doesn't exist.
[ -e "${HOME}/.bashrc" ] || touch "${HOME}/.bashrc"
RCFS=${1:-"$(ls -1 "${HOME}"/.*shrc)"}

# Create pypath directory.
[ -f "${PYD}" ] && mv "${PYD}" "${PYD}.bak"
mkdir -p "${PYD}"

# Install files.
echo "${RCFS}" >> "${SITE}"
cp "uninstall.sh" "pypath.sh" "pypath.py" "${PYD}"
chmod 755 "${PYD}/uninstall.sh" "${PYD}/pypath.py"
chmod 644 "${SITE}" "${PYD}/pypath.sh"

# Add alias & source commands to shell rc files.
cat "${SITE}" | while read -r RCF; do
    chmod u+rw "${RCF}"
    grep -q "^${ALIAS}" "${RCF}" || echo "${ALIAS}" >> "${RCF}"
    grep -qxF "${DFLT}" "${RCF}" || echo "${DFLT}" >> "${RCF}"
done
