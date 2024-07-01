#!/bin/bash

CHECK_EXTENSIONS=(".py")

# git stash -u -m untracked_files -- $(git status --porcelain | grep '^??' | cut -c4- | sed -n 'H;1h;${g;s/\n/ /g;p}') $(git status --porcelain | grep '^MM' | cut -c4- | sed -n 'H;1h;${g;s/\n/ /g;p}')
# echo "Starting script."
UNTRACKED="$(git status --porcelain | grep '^??' | cut -c4- | sed -n 'H;1h;${g;s/\n/ /g;p}')"
UNTRACKED_STASH_NAME="untracked_files"
UNSTAGED_STASH_NAME="unstaged_stash"
# The $(git status --porcelain) returns 'M ' for staged files, ' M' for modified but not staged files, and
# 'MM' for files that were modified, staged, and modified again without those new modifications being staged.
# The latter option will be checked, but a warning will be emitted.
UNSTAGED="$(git status --porcelain | grep '^ M' | cut -c4- | sed -n 'H;1h;${g;s/\n/ /g;p}')"
STAGED_THEN_MODIFIED="$(git status --porcelain | grep '^MM' | cut -c4- | sed -n 'H;1h;${g;s/\n/ /g;p}')"
STASH_ATTEMPT="no"
UNSTAGED_STASH_ATTEMPT="no"
NO_STASH_TEXT="No local changes to save."
SASHED="$NO_STASH_TEXT"
UNSTAGED_STASH="$NO_STASH_TEXT"

# This is set down here because some of the git commands above may return no input, and then an exit code of 1.
set -o errexit -o errtrace

trap 'on_error $STASH_ATTEMPT $UNTRACKED_STASH_NAME $UNSTAGED_STASH_ATTEMPT $UNSTAGED_STASH_NAME $DEBUG $LINENO ${?} $BASH_COMMAND $BASH_LINENO $(caller)' ERR EXIT

unstash()
{
    UNSTASH_NAME="$1"
    DEBUG_FLAG="$2"
    STASH_NAME=$(git stash list --pretty='%gd %s'|grep "$UNSTASH_NAME"|head -1|awk '{print $1}')
    if [[ -n $STASH_NAME ]]
    then
        if [[ $DEBUG_FLAG == "yes" ]]; then echo "Unstashing $UNSTASH_NAME:"; fi
        git stash pop $STASH_NAME
    else
        if [[ $DEBUG == "yes" ]]; then echo "Stash $UNSTASH_NAME not found. Skipping."; fi
    fi
}

on_error()
{
    DEBUG_FLAG="$5"
    LINE_NO="$6"
    ERR_CODE="$7"
    LAST_CMD="$8"
    LINENO_BASH="$9"
    if [[ $DEBUG_FLAG == "yes" ]]; then echo "Trapped error: line $LINE_NO, code $ERR_CODE, command $LAST_CMD, bash lineno: $LINENO_BASH."; fi
    STASH_ATTEMPT_INPUT="$1"
    STASH_NAME_INPUT="$2"
    UNSTAGED_ATTEMPT_INPUT="$3"
    UNSTAGED_NAME_INPUT="$4"
    if [[ $DEBUG_FLAG == "yes" ]]; then echo "Stash attempted: $STASH_ATTEMPT_INPUT"; fi
    if [[ $STASH_ATTEMPT_INPUT == "yes" ]]
    then
        unstash "$STASH_NAME_INPUT" $DEBUG_FLAG
    fi
    if [[ $DEBUG_FLAG == "yes" ]]; then echo "Unstaged stash attempted: $UNSTAGED_ATTEMPT_INPUT"; fi
    if [[ $UNSTAGED_ATTEMPT_INPUT == "yes" ]]
    then
        unstash "$UNSTAGED_NAME_INPUT" $DEBUG_FLAG
    fi
    exit $ERR_CODE
}

help()
{
    echo "
    Usage: $(basename $0) [OPTS]

    -t  Run tests, as well as checks.
    -s  Don't stash unstaged changes prior to running checks.
    -u  Don't stash untracked files prior to running checks.
    -d  Add extra echo statements for debugging.
    -h  Display this help message and exit.
    "
}

run_scripts()
{
    DO_TESTS="$1"
    DEBUG_FLAG="$2"
    #THE_DIR="$(dirname $0)"
    THE_DIR="$(git rev-parse --show-toplevel)"
    if [[ $DEBUG_FLAG == "yes" ]]; then echo "Current working dir: $THE_DIR"; fi
    if [[ $DEBUG_FLAG == "yes" ]]; then echo "All args to script: ${@:3}"; fi
    # Filter args to only keep python files:
    FILES=()
    for filename in ${@:3}
    do
        if [[ $DEBUG_FLAG == "yes" ]]; then echo "filename: $filename"; fi
        if [[ $(echo ${CHECK_EXTENSIONS[@]} | fgrep -w ".${filename##*.}") ]]
        then
            FILES+=($filename)
        fi
    done
    if [[ $DEBUG_FLAG == "yes" ]]; then echo "FILES: ${FILES[@]}"; fi
    #"$THE_DIR"/checks.sh checks $FILES
    if (( ${#FILES[@]} ))
    then
        # "$THE_DIR"/checks.sh autoflake ${FILES[@]}
        # "$THE_DIR"/checks.sh black ${FILES[@]}
        # "$THE_DIR"/checks.sh isort ${FILES[@]}
        # "$THE_DIR"/checks.sh mypy #${FILES[@]}
        # "$THE_DIR"/checks.sh pylint #${FILES[@]}
        # if [[ $DO_TESTS == "yes" ]]
        # then
        #     "$THE_DIR"/checks.sh test
        # fi
        "$THE_DIR"/checks.sh commit -t ${FILES[@]}
    fi
}

TESTS="no"
STASH_UNTRACKED="yes"
STASH_UNSTAGED="yes"
DEBUG="no"
# echo "Reading options..."
while getopts ":tsudh" opt
do
    case $opt in
        t)
            TESTS="yes"
            ;;
        s)
            STASH_UNSTAGED="no"
            ;;
        u)
            STASH_UNTRACKED="no"
            ;;
        d)
            DEBUG="yes"
            ;;
        h)
            help
            exit 0
            ;;
    esac
done
if [[ $DEBUG == "yes" ]]; then echo "All remaining args: ${@:2}"; fi

if [[ -n $STAGED_THEN_MODIFIED ]]
then
    echo "WARNING: Some staged files have been subsequently modified, and those modifications were not staged."
    echo "         These files will be checked anyway."
    if [[ $DEBUG == "yes" ]]; then echo "         These files are: $STAGED_THEN_MODIFIED"; fi
    echo ""
fi

if [[ $STASH_UNSTAGED == "no" && $STASH_UNTRACKED == "no" ]]
then
    run_scripts $TESTS $DEBUG ${@:2}
    if [[ $DEBUG == "yes" ]]; then echo "Finished sequence: stash neither unstaged nor untracked."; fi
elif [[ $STASH_UNSTAGED == "yes" && $STASH_UNTRACKED == "yes" ]]
then
    if [[ -n $UNTRACKED || -n $UNSTAGED ]]
    then
        if [[ $DEBUG == "yes" ]]; then echo "Stashing unstaged changes and untracked files:"; fi
        STASHED="$(git stash -u -m $UNTRACKED_STASH_NAME -- $UNTRACKED $UNSTAGED)"
        if [[ $STASHED != *$NO_STASH_TEXT* ]]
        then
            if [[ $DEBUG == "yes" ]]; then echo "Stashed changes to $UNTRACKED_STASH_NAME."; fi
            STASH_ATTEMPT="yes"
        else
            if [[ $DEBUG == "yes" ]]; then echo "No unstaged changes or untracked files able to be stashed."; fi
        fi
    else
        if [[ $DEBUG == "yes" ]]; then echo "No unstaged changes or untracked files to stash."; fi
    fi
    run_scripts $TESTS $DEBUG ${@:2}
    if [[ $STASHED != *$NO_STASH_TEXT* ]]
    then
        if [[ $DEBUG == "yes" ]]; then echo "$STASHED"; fi
        unstash $UNTRACKED_STASH_NAME $DEBUG
        STASH_ATTEMPT="no"
    fi
    if [[ $DEBUG == "yes" ]]; then echo "Finished sequence: stash unstaged and untracked."; fi
elif [[ $STASH_UNSTAGED == "yes" && $STASH_UNTRACKED == "no" ]]
then
    if [[ -n $UNSTAGED ]]
    then
        if [[ $DEBUG == "yes" ]]; then echo "Stashing unstaged changes:"; fi
        STASHED="$(git stash --keep-index -m $UNTRACKED_STASH_NAME)"
        if [[ $STASHED != *$NO_STASH_TEXT* ]]
        then
            if [[ $DEBUG == "yes" ]]; then echo "Stashed changes to $UNTRACKED_STASH_NAME."; fi
            STASH_ATTEMPT="yes"
        else
            if [[ $DEBUG == "yes" ]]; then echo "No unstaged changes able to be stashed."; fi
        fi
    else
        if [[ $DEBUG == "yes" ]]; then echo "No unstaged changes to stash."; fi
    fi
    run_scripts $TESTS $DEBUG ${@:2}
    if [[ $STASHED != *$NO_STASH_TEXT* ]]
    then
        unstash $UNTRACKED_STASH_NAME $DEBUG
        STASH_ATTEMPT="no"
    fi
    if [[ $DEBUG == "yes" ]]; then echo "Finished sequence: stash unstaged but not untracked."; fi
elif [[ $STASH_UNSTAGED == "no" && $STASH_UNTRACKED == "yes" ]]
then
    if [[ -n $UNTRACKED ]]
    then
        if [[ -n $UNSTAGED ]]
        then
            if [[ $DEBUG == "yes" ]]; then echo "Temporarily stashing unstaged files:"; fi
            UNSTAGED_STASH="$(git stash --keep-index -m $UNSTAGED_STASH_NAME)"
            if [[ $UNSTAGED_STASH != *$NO_STASH_TEXT* ]]
            then
                if [[ $DEBUG == "yes" ]]; then echo "Temporarily stashed unstaged changes to $UNSTAGED_STASH_NAME."; fi
                UNSTAGED_STASH_ATTEMPT="yes"
            else
                if [[ $DEBUG == "yes" ]]; then echo "Could not temporarily stash unstaged changes."; fi
            fi
        else
            if [[ $DEBUG == "yes" ]]; then echo "No unstaged files. No temporary stashing necessary."; fi
        fi
        if [[ $DEBUG == "yes" ]]; then echo "Untracked files found. Stashing them to $UNTRACKED_STASH_NAME."; fi
        STASHED="$(git stash --keep-index -u -m $UNTRACKED_STASH_NAME)"
        if [[ $STASHED != *$NO_STASH_TEXT* ]]
        then
            if [[ $DEBUG == "yes" ]]; then echo "Stashed changes to $UNTRACKED_STASH_NAME."; fi
            STASH_ATTEMPT="yes"
        else
            if [[ $DEBUG == "yes" ]]; then echo "No untracked files able to be stashed (though some were detected????)."; fi
        fi

        if [[ $UNSTAGED_STASH != *$NO_STASH_TEXT* ]]
        then
            unstash $UNSTAGED_STASH_NAME $DEBUG
            UNSTAGED_STASH_ATTEMPT="no"
        fi
    else
        if [[ $DEBUG == "yes" ]]; then echo "No untracked files to stash."; fi
    fi
    run_scripts $TESTS $DEBUG ${@:2}
    if [[ $STASHED != *$NO_STASH_TEXT* ]]
    then
        unstash $UNTRACKED_STASH_NAME $DEBUG
        STASH_ATTEMPT="no"
    fi
    if [[ $DEBUG == "yes" ]]; then echo "Finished sequence: stash untracked but not unstaged."; fi
fi

if [[ $DEBUG == "yes" ]]; then echo "Last line of file."; fi

exit 0
