# Contributing

There a few ways in which you could contribute towards MTRESS, namely by:
- Providing feedback
- Documenting
- Testing
- Enhancing

Please read this document to familiarise yourself with these processes.

## Providing feeback

Feedback helps us to keep MTRESS working well and to improve it. If you think
you found a bug, had an idea about how MTRESS could be improve, consider
raising an issue on [our gitlab page](https://gitlab.dlr.de/mtress-ecosystem/mtress/-/issues).

We prepared issue templates to prevent contributors from raising the same issue
 multiple times and other inconveniences. These will also guide you through the
 process and each includes a list of aspects to consider before submission.

## Documenting

We strive to have accurate and up to date documentation but this is a work in
progress. If something is incorrect or lacking, consider submitting corrections
or expanding existing documentation. This includes the docstrings as well as
tutorials. For the former, we rely on the reStructuredText (reST) style.

## Testing

We divide our tests into two phases:
- linting (using ruff)
- testing (using tox and pytest)

The CI pipeline will check the code for compliance but some checks can also be 
performed locally. 

Linting checks can be performed locally using:

```bash 
python -m black -l 79 --preview --enable-unstable-feature=string_processing .
``` 

The code can also be tested locally with:

```bash 
tox
```

## Enhancing

Enhancing the code is arguably the most demanding type of contribution. For
reasons of economy, please consider the following steps before spending time on
 a contribution:

- Check if the enhancement has not been proposed already [here](https://gitlab.dlr.de/mtress-ecosystem/mtress/-/issues) 
- If it has not, raise an issue and wait for feedback
- If and when you receive positive feedback, propose your solution and use git
- Test your solution as comprehensively as possible, namely by making sure that
code coverage includes all your contributions (i.e., new lines of code)
- Document your proposal, possibly by writing a tutorial as well
- File a merge request [here](https://gitlab.dlr.de/mtress-ecosystem/mtress/-/merge_requests) 
