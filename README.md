# Time Tracker

Time tracker for tasks.

## Installation

1. (If poetry is not already installed:) `curl -sSL https://install.python-poetry.org | python3 -`
2. `git clone https://github.com/r-spiewak/time_tracker.git`
3. `poetry install`
4. (optional) Initialize a client config file, me config file, invoice state file, and invoice template with `poetry run time-tracker -a initialize`

## Dev Installation

After completing the regular installation above, also do the following:
1. `poetry run pre-commit install`
2. It may also be necessary to `chmod +x checks.sh`.


## Usage

`time-tracker [OPTIONS]`
   
Options:
```
 --action              -a      TEXT     What to do with the tracker. Valid actions: track, status, report, invoice, initialize. [default: track]
 --task                -t      TEXT     Task name or description.
 --filename            -f      TEXT     CSV filename. [default: None]
 --directory           -d      TEXT     Directory to store the file.
 --start-date          -s      TEXT     Start date filter (YYYY-MM-DD).
 --end-date            -e      TEXT     End date filter (YYYY-MM-DD).
 --client              -c      TEXT     Internal client reference string (e.g., client name). [default: None]
 --client-config               TEXT     File containing information regarding clients. [default: None]
 --me                  -m      TEXT     File containing information regarding 'me', the user of this tracker. [default: None]
 --invoice-state               TEXT     File containing information regarding persistent invoice state. [default: None]
 --invoice-filename    -i      TEXT     Name for the generated invoice file. [default: None]
 --invoice-template            TEXT     File to be used as a template for the generated invoices. [default: None]
 --verbosity           -v      INTEGER  [default: 0]
 --install-completion                   Install completion for the current shell.
 --show-completion                      Show completion for the current shell, to copy it or customize the installation.
 --help                                 Show this message and exit.
 ```
