#!/usr/bin/env python
"""
Configure the Python module search path.

This file should be run via a shell script that can actually set the
PYTHONPATH environment variable.
"""


import argparse
import os
import sys


DEFAULT_PATH = "~/.pypath/default.pth"

# Enumerate return codes.
execfile(os.path.expanduser("~/.pypath/codes"))

DESCRIPTION = __doc__.strip().split('\n')[0]
USAGE = \
    "pypath [-h] [-e] [-c] [-d] [-f] [-a path [path ...]] [-r path [path ...]]"
EPILOG = """
Specifying multiple options and path values is allowed.
Path files should list one directory per line, in order of decreasing priority.

If 'echo' is specificed, the PYTHONPATH value is echoed once at the end.
If 'clear' is specified, the PYTHONPATH is cleared once at the start.
The 'permanent' option sets the default PYTHONPATH value once at the end.

Examples:
  pypath -a .            # Add current dir to PYTHONPATH.
  pypath -r .. .         # Remove parent & current dirs from PYTHONPATH.
  pypath -a foo.pth      # Add the contents of './foo.pth' to PYTHONPATH.
  pypath -r *.pth        # Remove contents of all '.pth' files from PYTHONPATH.
  pypath -c -a .         # Clear and set PYTHONPATH to the current directory.
  pypath -c -a .. . -e   # Clear, set, and echo the PYTHONPATH.

Any number of paths can be specified after an 'add' or 'remove' flag. These are
prepended to the PYTHONPATH as a group, so earlier additions have a higher
priority:
  $ pypath -c -a bin tmp usr -e
  /bin:/tmp:/usr

Any number of 'add' or 'remove' actions can be specified. These are performed
sequentially. The PYTHONPATH is prepended by each action, so later additions
have a higher priority:
  $ pypath -c -a bin -a tmp -a usr -e
  /usr:/tmp:/bin
"""


def main():
    """
    Parse command line & perform actions on PYTHONPATH.
    """
    #print sys.argv
    try:
        if len(sys.argv) < 2:
            sys.argv.append("-h")   # Show help if run with no arguments.
        args = get_parser().parse_args()
    except SystemExit as exc:
        if '-h' in sys.argv or '--help' in sys.argv:
            sys.exit(HELP)
        else:
            sys.exit(ERROR)
    #print args
    try:
        pythonpath = os.getenv("PYTHONPATH", None).split(':')
    except AttributeError:  # pythonpath is None.
        pythonpath = []
    if args.clear:
        path_list = []
    else:
        path_list = pythonpath
    try:
        path_list = set_paths(pythonpath, path_list, args.actions, args.force)
        path_list = join_paths(path_list)
        if args.permanent:
            set_permanently(path_list)
        print ":".join(path_list)   # Always echo.
    except Exception as exc:
        print str(exc)  # Do not indimidate user with a traceback.
        sys.exit(ERROR)


def get_parser():
    """
    Get command line parser.
    """
    doc = __doc__.strip().split("\n")
    parser = Parser(
        usage=USAGE,
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    # Help is provided for free.
    # Echo is always true.
    parser.add_argument('-e', dest='echo', action='store_true', default=True,
        help='Echo the PYTHONPATH environment variable.')
    parser.add_argument('-c', dest='clear', action='store_true', default=False,
        help='Clear the PYTHONPATH environment variable completely.')
    parser.add_argument('-a', dest='actions', action=AppendWithArg, nargs='+',
        metavar='pth', default=[], help=('If path is a directory, add it to the'
        ' PYTHONPATH.\nIf path is a file, add contents to the PYTHONPATH.'))
    parser.add_argument('-r', dest='actions', action=AppendWithArg, nargs='+',
        metavar='pth', default=[], help=('If path is a directory, remove it'
        ' from the PYTHONPATH.\nIf path is a file, remove contents from the'
        ' PYTHONPATH.'))
    parser.add_argument('-d', dest='permanent', action='store_true',
        default=False, help=('Permanently save the current PYTHONPATH value as'
        ' the default.'))
    parser.add_argument('-f', dest='force', action='store_true', default=False,
        help='Force execution without checking user input.')
    return parser


class Parser(argparse.ArgumentParser):
    """
    Do not print 'self.prog' if error.
    """
    def exit(self, status=0, message=None):
        try:
            message = message.replace("{}: ".format(self.prog), "")
        except AttributeError:
            pass
        super(Parser, self).exit(status, message)


class AppendWithArg(argparse._AppendAction):
    """
    Include option string when appending values.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        #values = [value for value in values if len(value) > 0]  # Remove blank.
        values = (option_string, values)
        super(AppendWithArg, self).__call__(parser, namespace, values,
            option_string)


def set_paths(all_paths, path_list, actions, force):
    """
    Add or remove paths.

    Paths are specified by descending priority with: -a 1 2 3
    Paths are specified by ascending priority with: -a 3 -a 2 -a 1
    The 'path_list' parameter is used to track the working PYTHONPATH.
    The 'all_paths' parameter is used to track paths that were present
    at *any time* during or before execution.  This allows the user to
    specify extra valid removes (like -a p1 -r p1 -r p1) without an
    error.
    """
    all_paths = set(all_paths)
    for action, paths in actions:
        all_paths |= set(path_list)
        altered = []  # Action is either adding or removing.
        for path in paths:

            if os.path.isfile(path):
                lines = get_file_paths(path)
                if not force and len(lines) == 0:
                    raise ValueError("No paths in file: '{}'".format(path))
                file_dir = os.path.dirname(format_path(path))
                for line in lines:
                    # Convert file-relative paths to absolute paths.
                    converted = os.path.expandvars(os.path.expanduser(line))
                    if not os.path.isabs(converted):
                        converted = os.path.join(file_dir, converted)

                    formatted = format_path(converted)
                    if not force:
                        if action in ['-a', '--add']:
                            check_path_add(formatted, line, path)
                        if action in ['-r', '--remove']:
                            check_path_remove(all_paths, formatted, line, path)
                    altered.append(formatted)

            else:
                formatted = format_path(path)
                if not force:
                    if action in ['-a', '--add']:
                        check_path_add(formatted, path)
                    if action in ['-r', '--remove']:
                        check_path_remove(all_paths, formatted, path)
                altered.append(formatted)

        if action in ['-a', '--add']:
            path_list = altered + path_list
        else:
            path_list = [p for p in path_list if p not in altered]
    return path_list


def check_path_add(formatted, original, file=None):
    """
    Check that path exists, and is a directory.
    """
    if not os.path.exists(formatted):
        raise ValueError("Path not found: '{}'{}".format(formatted,
            get_path_details(formatted, original, file)))
    if not os.path.isdir(formatted):
        raise ValueError("Not a directory: '{}'{}".format(formatted,
            get_path_details(formatted, original, file)))


def check_path_remove(pythonpath, formatted, original, file=None):
    """
    Check that path is (or was) in the PYTHONPATH.

    The path doesn't actually need to exist, and may even have been
    removed from the system.
    """
    if formatted not in pythonpath:
        raise ValueError("Not on PYTHONPATH: '{}'{}".format(formatted,
            get_path_details(formatted, original, file)))


def get_path_details(formatted, original, file=None):
    """
    Return original path information in a consistent format.
    """
    if formatted == original:
        if file is None:
            message = ""
        else:
            message = " (in '{}')".format(file)
    else:
        if file is None:
            message = " (specified as '{}')".format(original)
        else:
            message = " (specified as '{}' in '{}')".format(original, file)
    return message


# TODO catch unreadable file error?
def get_file_paths(filename):
    """
    Get paths from file.

    File should contain one path per line.
    Paths may be absolute or relative to the file's directory.
    Blank lines & comments are ignored.
    """
    lines = []
    with open(filename) as fh:
        for line in fh.readlines():
            line = line.strip()
            if len(line) == 0 or line.startswith('#'):
                continue
            lines.append(line)
    return lines


# TODO Use realpath instead of abspath?
def format_path(path):
    """
    Format path consistently.

    Changes to a path file should not break the remove function (same
    path specified differently, etc).
    """
    if len(path) == 0:
        return path     # 'os.path.abspath' converts empty path to cwd.
    else:
        return os.path.normpath(os.path.abspath(path))


def join_paths(path_list):
    """
    Clean up extra ':' characters & duplicates in PYTHONPATH.
    """
    found = []
    for path in path_list:
        if len(path) > 0 and path not in found:
            found.append(path)
    return found


def set_permanently(path_list):
    """
    Permanently set the PYTHONPATH environment variable.

    Alters the contents of '~/.pypath', which should be sourced by the
    shell on startup.
    """
    path_strings = ["'{}'".format(pth) for pth in path_list]
    path_string = "\nPYTHONPATH+=:".join(path_strings)
    contents = "PYTHONPATH={0}\nexport PYTHONPATH\n".format(path_string)
    with open(os.path.expanduser(DEFAULT_PATH), 'w') as fh:
        fh.write(contents)


if __name__ == "__main__":
    main()


