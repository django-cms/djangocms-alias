This is the plan:


- use gh cli to any operations related to github
- use ast-grep when required


We need to update the test matrix for the CI.

Python 3.14 will be added and any version lower than 3.10 is removed.

The change needs to reflected on the classifiers as well.

Follow this PR and do what is done here.
create a properly named branch.

Proper exclude needs to be done for django 6 as django 6 only support 3.12 plus.

We would also need to run pyupgrade and update to python 3.10 plus.

After the python file is changed using pyupgrade, use ruff to lint and fix lint issues
