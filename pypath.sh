# Configure the Python module search path.
#
# This file should be 'run' with the 'source' command, so it is not executable.
# For example: 'source pypath.sh -c -a . -e '

main() {
    local OUTPUT
    local RETCODE
    local ECHO
    while read -r LINE; do 
        eval "${LINE}"; 
    done < ~/.pypath/codes
    OUTPUT="$(~/.pypath/pypath.py "${@}" 2>&1)"
    RETCODE="${?}"
    ECHO=false
    while test "${#}" -gt 0; do
        case "${1}" in
            '-e' | '--echo') ECHO=true ;;
        esac
        shift
    done
    #echo "OUTPUT: ${OUTPUT}"
    #echo "RETCODE: ${RETCODE}"
    #echo "ECHO: ${ECHO}"
    if test ${RETCODE} -eq "${HELP}"; then
        # Echo output to stdout as it contains help.
        echo "${OUTPUT}"
    elif test ${RETCODE} -ne "${SUCCESS}"; then
        # Echo output to stderr as it contains an error string.
        echo "${OUTPUT}" 1>&2
    else
        # Set PYTHONPATH.
        export PYTHONPATH="${OUTPUT}"
        # Echo PYTHONPATH if specified.
        "${ECHO}" && echo "${PYTHONPATH}"
    fi
    return "${RETCODE}"
}

main "${@}"
unset main
