#!/bin/bash

# Test pypath.sh script.

# Main function.
main() {
    # Test parameters.
    # test dirs, including absolute dir under '~' & dir with spaces in name.
    TEST_DIRS="${HOME}/test pypath/nested"
    TEST_PATH="::${HOME}:::$(dirname "${TEST_DIRS}"):${TEST_DIRS}:"
    CLEAN_PATH="${HOME}:${HOME}/test pypath:${HOME}/test pypath/nested"
    # Disable user aliases
    unalias -a
    # Make test dirs.
    rm -rf "$(dirname "${TEST_DIRS}")"
    mkdir -p "${TEST_DIRS}"
    trap 'cleanup' EXIT
    test_no_args
    test_help
    test_echo
    test_clear
    test_add
    test_remove
    test_error
    echo ''
    trap - EXIT
    cleanup
}

cleanup() {
    rm -rf "$(dirname "${TEST_DIRS}")"
    unset TEST_DIRS
    unset TEST_FILES
    unset CLEAN_PATH
}

# Test no args returns usage.
test_no_args() {
    local OUTPUT="$(. ./pypath.sh 2>&1 || true)"
    #echo "OUTPUT: ${OUTPUT}"
    if ! echo "${OUTPUT}" | grep -q "usage"; then
        printf "\nFail 'test_no_args', expected usage, got:\n${OUTPUT}"
        return 1
    fi
    printf '.'
}

# Test -h returns usage.
test_help() {
    local OUTPUT="$(. ./pypath.sh -h 2>&1 || true)"
    #echo "OUTPUT: ${OUTPUT}"
    if ! echo "${OUTPUT}" | grep -q "usage"; then
        printf "\nFail 'test_help', expected usage, got:\n${OUTPUT}"
        return 1
    fi
    printf '.'
}

# Test that -e echos PYTHONPATH with ':' cleaned up.
test_echo() {
    export PYTHONPATH="${TEST_PATH}"
    local OUTPUT="$(. ./pypath.sh -e 2>&1 || true)"
    #echo "OUTPUT: ${OUTPUT}"
    local EXPECTED="${CLEAN_PATH}"
    if [ "${OUTPUT}" != "${EXPECTED}" ]; then
        printf "\nFail 'test_echo', expected:\n${EXPECTED}\nGot:\n${OUTPUT}"
        return 1
    fi
    printf '.'
}

# Test that -c clears PYTHONPATH completely (before echo).
test_clear() {
    export PYTHONPATH="${TEST_PATH}"
    local OUTPUT="$(. ./pypath.sh -e -c 2>&1 || true)"
    #echo "OUTPUT: ${OUTPUT}"
    local EXPECTED=""
    if [ "${OUTPUT}" != "${EXPECTED}" ]; then
        printf "\nFail 'test_clear', PYTHONPATH not clear:\n${OUTPUT}"
        return 1
    fi
    printf '.'
}

# Test that -a sets PYTHONPATH.
# Dirs already on the PYTHONPATH are removed then prepended (in sequence).
test_add() {
    export PYTHONPATH="${HOME}"
    local OUTPUT="$(. ./pypath.sh -e -a "${TEST_DIRS}" -a "${HOME}" "$(dirname "${TEST_DIRS}")" 2>&1 || true)"
    #printf "OUTPUT: ${OUTPUT}"
    local EXPECTED="${CLEAN_PATH}"
    if [ "${OUTPUT}" != "${EXPECTED}" ]; then
        printf "\nFail 'test_add', expected:\n${EXPECTED}\nGot:\n${OUTPUT}"
        return 1
    fi
    printf '.'
}

# Test that -r sets PYTHONPATH.
# No error when removing valid entry twice.
test_remove() {
    export PYTHONPATH="${TEST_PATH}"
    local OUTPUT="$(. ./pypath.sh -e -r "${TEST_DIRS}" -r "${HOME}" "$(dirname "${TEST_DIRS}")" 2>&1 || true)"
    #printf "OUTPUT: ${OUTPUT}"
    local EXPECTED=""
    if [ "${OUTPUT}" != "${EXPECTED}" ]; then
        printf "\nFail 'test_remove', PYTHONPATH not clear:\n${OUTPUT}"
        return 1
    fi
    printf '.'
}

# Test error does not set PYTHONPATH.
test_error() {
    export PYTHONPATH=""
    local OUTPUT="$(. ./pypath.sh -e -a "${HOME}" "${TEST_DIRS}/invalid" -r "${HOME}" -a "${TEST_DIRS}" 2>&1 || true)"
    #printf "OUTPUT: ${OUTPUT}"
    if ! echo "${OUTPUT}" | grep -q "Path not found"; then
        printf "\nFail 'test_error', expected error, got:\n${OUTPUT}"
        return 1
    fi
    if [ 0 -ne ${#PYTHONPATH} ]; then
        printf "\nFail 'test_error', PYTHONPATH not clear:\n${OUTPUT}"
        return 1
    fi
    printf '.'
}

# Run tests.
main "${@}"
