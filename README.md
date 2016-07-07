# pypath

A tool for managing the Python module search path.


# About

`pypath` is a tool that makes it easy to import Python code from anywhere on a system.

This is useful when working with **unfinished** code (in a version control repository),
or **unpackaged** code (that cannot be installed).

Requires Python 2.7 or higher (or the argparse module).


# Installation

To install `pypath` for the current user, run `./install.sh`, then open a **new terminal**.

To install `pypath`, but **only** for a specific shell, run something like `./install.sh ~/.bashrc`.
(The default target is `~/.*shrc`).


# Usage

To add the current directory to the PYTHONPATH environment variable:
```shell
$ pypath -a .
```

To remove it:
```shell
$ pypath -r .
```

To clear the PYTHONPATH, add multiple directories, and echo the result:
```shell
$ pypath -c -a /Users /Users/jay -e
/Users:/Users/jay
```

To add project directories (listed in a file) to the PYTHONPATH:
```shell
$ pypath -a project.pth
```

To save the current PYTHONPATH value as the default:
```shell
$ pypath -d
```

Run `pypath -h` for more examples.


# How it works

The `pypath` command is actually an **alias** for `source ~/.pypath/pypath.sh`.
`pypath.sh` reads user input and sets the `PYTHONPATH` environment variable accordingly.
Most of the work is done by running `~/.pypath/pypath.py`, allowing the tool to be easily ported.
Any default `PYTHONPATH` values are stored in `~/.pypath/default.pth`.


# References

- [The Python module search path](https://docs.python.org/3.5/tutorial/modules.html#the-module-search-path)
- [The PYTHONPATH environment variable](https://docs.python.org/3.5/using/cmdline.html#envvar-PYTHONPATH)

