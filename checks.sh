#!/bin/bash

# This should have options to run each check individually,
# as well as all the checks together (and it can have 
# an option as well to run the linters without tests and
# coverage).
# Each thing should make sure, first and foremost, it's running
# in the poetry env (and if there is no poetry env, it should 
# install it and the dependencies), and then that the check
# package is actually installed. Then it should run the check.
# Each check should print output that it's starting the check,
# as well as any output that the check puts out. 
# Probably a function for each check, as well as a function (that
# each check will call) to check for (and install, if necessary)
# poetry, and then a switch statement at the end to run the
# specific check(s) given as input args (with a default to print
# a help message, probably from a help function).
# Also, at the beginning of the script, untracked files/dirs
# should be stashed, and at the end of the script (even upon
# exiting with errors) they should be restored.

install_poetry(){
    which poetry > /dev/null
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then
        echo "Installing poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
        exit_code=$?
        if [[ $exit_code > 0 ]]
        then
            echo "Failed to install poetry!"
            exit $exit_code
        fi
        echo "Done."
    fi
}

install_package(){
    echo "Installing package..."
    install_poetry
    poetry install -v
    exit_code=$?
    if [[ $exit_code > 0 ]]
    then
        echo "Failed to install package!"
        exit $exit_code
    fi
    echo "Done."
}

autoflake_check(){
    echo "Running autoflake..."
    poetry run which autoflake > /dev/null
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then 
        install_package
    fi
    poetry run autoflake $* --remove-unused-variables --recursive
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then
        echo "Autoflake failed!"
        exit $exit_code 
    fi
    echo "Done."
}

black_check(){
    echo "Running black formatter..."
    poetry run which black > /dev/null
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then 
        install_package
    fi
    poetry run black $* .
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then
        echo "Black formatter failed!"
        exit $exit_code 
    fi
    echo "Done."
}

isort_check(){
    echo "Running isort..."
    poetry run which isort > /dev/null
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then 
        install_package
    fi
    poetry run isort $* .
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then
        echo "Isort failed!"
        exit $exit_code 
    fi
    echo "Done."
}

mypy_check(){
    echo "Running mypy..."
    poetry run which mypy > /dev/null
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then 
        install_package
    fi
    poetry run mypy src tests --ignore-missing-imports --warn-unused-ignores 
    # verbose option?
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then
        echo "Mypy failed!"
        exit $exit_code 
    fi
    echo "Done."
}

pylint_check(){
    echo "Running pylint..."
    poetry run which pylint > /dev/null
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then 
        install_package
    fi
    poetry run pylint src tests --enable-useless-suppression # --ignore-paths <paths/to/ignore>
    # verbose option?
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then
        echo "Pylint failed!"
        exit $exit_code 
    fi
    echo "Done."
}

pytest_check(){
    DEBUG_FLAG="$1"
    echo "Running pytest and coverage..."
    poetry run which pytest > /dev/null
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then 
        install_package
    fi
    poetry run which coverage > /dev/null
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then 
        install_package
    fi
    if [[ $DEBUG_FLAG == "yes" ]]
    then
        poetry run coverage run -m pytest --testdox tests --pdb # --ignore=<paths/to/ignore>
    else
        poetry run coverage run -m pytest --testdox tests # --ignore=<paths/to/ignore>
    # verbose option?
    fi
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then
        echo "Pytest failed!"
        exit $exit_code 
    fi
    poetry run coverage report --fail-under=60 --skip-empty --skip-covered --show-missing
    # verbose option?
    exit_code=$?
    if [[ $exit_code != 0 ]]
    then
        echo "Coverage failed!"
        exit $exit_code 
    fi
    echo "Done."
}

pre_commit(){
    DEBUG_FLAG="$1"
    TESTS_FLAG="$2"
    shift 2
    autoflake_check --in-place $*
    black_check $*
    isort_check $*
    mypy_check
    pylint_check
    if [[ $TESTS_FLAG == "yes" ]]
    then
        pytest_check $DEBUG_FLAG
    fi
}

pre_merge(){
    autoflake_check --check $* .
    black_check --check $*
    isort_check --check-only $*
    mypy_check
    pylint_check
    pytest_check
}

help(){
    echo "
    Usage: $(basename $0) COMMAND [OPTIONS]

    COMMAND:
        install|setup   Install package.
        autoflake       Perform autoflake check.
        black           Perform black formatter check.
        isort           Perform isort import check.
        mypy            Peform mypy checks.
        *lint           Perform pylint checks.
        *test           Perform pytests and coverage.
        *commit         Perform pre-commit options (in-place,
                        where applicable): autoflake, black
                        formatter, isort import check, mypy,
                        and (optionally) pytests and coverage.
        *merge          Perform pre-merge options (not
                        in-place): autoflake, black formatter,
                        isort import check, mypy, and pytests
                        and coverage.
        help            Print this help message.

    OPTIONS:
        t       Also perform tests/coverage during *commit 
                command.
        d       Include "--pdb" flag in pytest (and also 
                perform test/coverage).
        h       Print help message and exit.
    "
}

DEBUG="no"
TESTS="no"
CMD="$1"; shift
while getopts dth opt; do
    case $opt in
        d)
            DEBUG="yes"
            TESTS="yes"
            shift
            ;;
        t)
            TESTS="yes"
            shift
            ;;
        h)
            help
            exit 0
            ;;
        ?)
            echo "Invalid option $OPTARG."
            help
            exit 1
            ;;
    esac
done
case $CMD in
    install | setup)
        install_package
        exit 0
        ;;
    autoflake)
        autoflake_check --in-place $*
        exit 0
        ;;
    black)
        black_check $*
        exit 0
        ;;
    isort)
        isort_check $*
        exit 0
        ;;
    mypy)
        mypy_check
        exit 0
        ;;
    *lint)
        pylint_check
        exit 0
        ;;
    *test)
        pytest_check $DEBUG
        exit 0
        ;;
    *commit)
        pre_commit $DEBUG $TESTS $*
        exit 0
        ;;
    *merge)
        pre_merge $*
        exit 0
        ;;
    help)
        help
        exit 0
        ;;
    *)
        echo "Invalid command: $CMD."
        help
        exit 1
esac