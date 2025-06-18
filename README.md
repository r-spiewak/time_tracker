# Python Template

Template repo for Python projects.

## Installation

1. (If poetry is not already installed:) `curl -sSL https://install.python-poetry.org | python3 -`
2. `git clone https://github.com/r-spiewak/python_template.git`
3. `poetry install`

## Dev Installation

After completing the regular installation above, also do the following:
1. `poetry run pre-commit install`
2. It may also be necessary to `chmod +x checks.sh`.


## Usage in Other Derived Repos

Create a repo based on this template. See https://github.com/marketplace/actions/actions-template-sync to make an Action to make the new repo automatically (make a PR to) sync changes from the template (this) repo.

Alternatively, set this template as an upstream branch and merge in changes accordingly:
1. *Set upstream*: From the derived (downstream) repository, run `git remote add template git@github.com:r-spiewak/python_template`.
2. *Fetch changes*: Run `git fetch template`.
3. *Merge changes* (maybe do this on a branch other than main and make a PR into main): `git merge template/main -- allow-unrelated-histories` (for the main branch in the upstream template).
4. *Fix Merge Conflicts*: Fix the merge conflicts in your local branch.

However, both of these methods are messy, since the package name (`python_template`) changes, and (if the derived repo is created from the gitHub template) the merge will want to revert it back to `python_template` and put anything new into a `python_template` directory as well (since they don't have a shared history).

The possible way to avoid this is if the derived repo is created locally as a copy of this repo, since then they'll have a shared history (and then the flag `--allow-unrelated-histories` in step 3 can be omitted as well).
