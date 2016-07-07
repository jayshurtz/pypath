#!/bin/bash

# Test install.sh script.

# Main function.
main() {
    PTH="${HOME}/.pypath/pypath.pth"
    mv "${PTH}" "${PTH}.bak" 2>/dev/null || true
    trap 'cleanup' EXIT
    test_alias
    test_default
    echo ''
    trap - EXIT
    cleanup
}

cleanup() {
    mv "${PTH}.bak" "${PTH}" 2>/dev/null || true
    unset PTH
    unset main
    unset cleanup
    unset test_alias
    unset test_default
}

# Test that 'pypath' alias works (in current shell).
test_alias() {
    OUTPUT="$(bash -ic 'pypath -c -a "${HOME}" -d')"
    #echo "OUTPUT: ${OUTPUT}"
    if [ "z${OUTPUT}" != "z" ]; then
        printf "\nFail '${FUNCNAME[0]}', expected empty output, got:\n${OUTPUT}"
        return 1
    fi
    printf '.'
}

# Test that new shells source 'pypath.pth'.
test_default() {
    OUTPUT="$(bash -ic 'pypath -e')"
    #echo "OUTPUT: ${OUTPUT}"
    if [ "${OUTPUT}" != "${HOME}" ]; then
        printf "\nFail '${FUNCNAME[0]}', expected:\n${HOME}\ngot:\n${OUTPUT}"
        return 1
    fi
    printf '.'
}

# Run tests.
main "${@}"
