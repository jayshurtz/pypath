#!/usr/bin/env python
"""
Test pypath.py script.
"""


import contextlib
import StringIO
import os
import shlex
import shutil
import subprocess
import sys
import unittest

import pypath


# Dirs & files used in testing.
DEFAULT_PATH_FILE = os.path.expanduser(pypath.DEFAULT_PATH)
PATH_FILE = os.path.join("test_pypath.pth")
TEST_DIRS = [
    "test pypath",
    os.path.join("test pypath", "nested 1"),
    os.path.join("test pypath", "nested 1", "nested 2"),
]
TEST_FILES = [
    os.path.join(TEST_DIRS[0], "foo"),
    os.path.join(TEST_DIRS[1], "bar"),
    os.path.join(TEST_DIRS[2], "qux"),
]

# pypath output.
TEST_DIRS_OUT = [os.path.abspath(path) for path in TEST_DIRS]
NOT_DIRS = [os.path.join(path, "not") for path in TEST_DIRS]
NOT_DIRS_OUT = [os.path.join(os.path.abspath(path), "not")
    for path in TEST_DIRS]


def backup():
    """
    Backup default PYTHONPATH file.
    """
    try:
        shutil.move(DEFAULT_PATH_FILE, DEFAULT_PATH_FILE + ".bak")
    except IOError as err:
        if err.errno == 2:  # No file to backup.
            pass


def restore():
    """
    Restore default PYTHONPATH file.
    """
    try:
        shutil.move(DEFAULT_PATH_FILE + ".bak", DEFAULT_PATH_FILE)
    except IOError as err:
        if err.errno == 2:  # No file to backup.
            pass


def write_file(filename, contents):
    """
    """
    with open(filename, 'w') as fh:
        fh.write(contents)


def mk_test_files():
    """
    Create dirs/files used in testing.
    """
    for path in TEST_DIRS:
        try:
            os.mkdir(path)
        except OSError as err:
            if err.errno == 17:     # Ignore error if dir already exists.
                pass
    for fn in TEST_FILES:
        with open(fn, 'w') as fh:
            fh.write("")
    # PATH_FILE is created as-needed.


def rm_test_files():
    """
    Remove dirs/files used in testing.
    """
    for path, dirs, files in os.walk(TEST_DIRS[0], topdown=False):
        for f in files:
            os.remove(os.path.join(path, f))
        for d in dirs:
            os.rmdir(os.path.join(path, d))
    try:
        os.rmdir(TEST_DIRS[0])
    except OSError as err:
        if err.errno == 2:     # Ignore error if dir already removed.
            pass
    try:
        os.remove(PATH_FILE)
    except OSError as err:
        if err.errno == 2:
            pass


@contextlib.contextmanager
def no_stderr():
    """
    Silence stderr messages.
    """
    saved = sys.stderr
    sys.stderr = StringIO.StringIO()
    yield
    sys.stderr = saved


def run(*args, **kwargs):
    """
    """
    proc = subprocess.Popen(*args, **kwargs)
    out, err = proc.communicate()
    return proc.returncode, out, err



class TestPyPath(unittest.TestCase):
    """
    """

    @classmethod
    def setUpClass(cls):
        rm_test_files()
        mk_test_files()
        backup()

    @classmethod
    def tearDownClass(cls):
        rm_test_files()
        restore()

    def test_join_paths(self):
        # Blanks & repeats ignored.
        self.assertEqual(['p1', 'p2'], pypath.join_paths(
            ['', 'p1', '', '', 'p2', 'p1', '', '', '']))

    def test_format_path(self):
        # Test blank.
        self.assertEqual("", pypath.format_path(""))
        # Test cwd.
        self.assertEqual(os.path.abspath('.'), pypath.format_path("."))
        # Test normalized.
        self.assertEqual(os.path.abspath('test pypath/nested'),
            pypath.format_path("test pypath/../test pypath/nested"))

    def test_get_path_details(self):
        # Test blank.
        self.assertEqual("", pypath.get_path_details("", "", None))
        # Test identical, no file.
        self.assertEqual("", pypath.get_path_details("p1", "p1", None))
        # Test identical, from file.
        self.assertTrue("in 'filename'" in pypath.get_path_details(
            "p1", "p1", "filename"))
        # Test not match without file.
        self.assertTrue("as 'original'" in pypath.get_path_details(
            "formatted", "original", None))
        # Test not match with file.
        msg = pypath.get_path_details("formatted", "original", "filename")
        self.assertTrue("as 'original'" in msg and "in 'filename'" in msg)

    def test_get_file_paths(self):
        # Test blanks, comments & paths.
        write_file(PATH_FILE,
            "# Comment 1\n\n\n  # C 2 \n\n.\n~\nfoo\nfoo/foo bar")
        self.assertEqual(['.', '~', 'foo', 'foo/foo bar'],
            pypath.get_file_paths(PATH_FILE))

    def test_check_path_add(self):
        # Test path not exist.
        p1 = os.path.join(TEST_DIRS[0], "p1")
        p2 = os.path.join(TEST_DIRS[0], "p2")
        with self.assertRaises(ValueError) as err:
            pypath.check_path_add(p1, p1, None)
            self.assertTrue("not found" in str(err))
        # Test path is file.
        p1 = TEST_FILES[0]
        p2 = TEST_FILES[1]
        with self.assertRaises(ValueError) as err:
            pypath.check_path_add(p1, p1, None)
            self.assertTrue("not found" in str(err))
        # Test path is dir (no errors raised).
        p1 = TEST_DIRS[0]
        p2 = TEST_DIRS[1]
        pypath.check_path_add(p1, p2, "filename")

    def test_check_path_remove(self):
        p1 = os.path.join(TEST_DIRS[0], "p1")
        p2 = os.path.join(TEST_DIRS[0], "p2")
        # Test in PYTHONPATH (no error raised).
        pypath.check_path_remove([p1, p2], p1, 'original', 'filename')
        with self.assertRaises(ValueError) as err:
            pypath.check_path_remove([p2], p1, p1, 'filename')
            self.assertTrue("Not on" in str(err))

    def test_set_permanently(self):
        pypath.set_permanently(TEST_DIRS)
        with open(DEFAULT_PATH_FILE, 'r') as fh:
            contents = fh.read()
        self.assertEqual(contents, "PYTHONPATH={}\nexport PYTHONPATH\n".format(
            "\nPYTHONPATH+=:".join(["'{}'".format(td) for td in TEST_DIRS])))

    def test_set_paths_from_file(self):
        # Test file with no paths.
        write_file(PATH_FILE, "# Coment\n\n")
        with self.assertRaises(ValueError) as err:
            pypath.set_paths(['p1'], ['p2'], [('-a', [PATH_FILE])], False)
            self.assertTrue(PATH_FILE in str(err))
        # Test that relative paths & absolute paths work as lines in a path
        # file, including absolute paths starting with '~'.
        write_file(PATH_FILE, "~\n.\n{}\n".format(TEST_DIRS_OUT[0]))
        self.assertEqual(
            [
                os.path.expanduser('~'),
                os.path.abspath('.'),
                TEST_DIRS_OUT[0],
                'p2',
            ],
            pypath.set_paths(['p1'], ['p2'], [('-a', [PATH_FILE])], True),
        )

    def test_set_paths_add(self):
        # Test add not exist (as group).
        with self.assertRaises(ValueError) as err:
            pypath.set_paths(['p1'], ['p2'], [('-a', NOT_DIRS)], False)
        # Test add not exist force.
        self.assertEqual(NOT_DIRS_OUT+['p2'],
            pypath.set_paths(['p1'], ['p2'], [('-a', NOT_DIRS)], True))
        # Test add as group.
        self.assertEqual(TEST_DIRS_OUT+['p2'],
            pypath.set_paths(['p1'], ['p2'], [('-a', TEST_DIRS)], False))
        # Test add sequential.
        self.assertEqual(TEST_DIRS_OUT+['p2'], pypath.set_paths(['p1'],
            ['p2'], [('-a', [p]) for p in TEST_DIRS[-1::-1]], False))

    def test_set_paths_add_from_file(self):
        # Test add from file not exist.
        write_file(PATH_FILE, "\n".join(NOT_DIRS))
        with self.assertRaises(ValueError) as err:
            pypath.set_paths(['p1'], ['p2'], [('-a', [PATH_FILE])], False)
        # Test add from file not exist force.
        write_file(PATH_FILE, "\n".join(NOT_DIRS))
        self.assertEqual(NOT_DIRS_OUT+['p2'],
            pypath.set_paths(['p1'], ['p2'], [('-a', [PATH_FILE])], True))
        # Test add from file as group.
        write_file(PATH_FILE, "\n".join(TEST_DIRS))
        self.assertEqual(
            TEST_DIRS_OUT+TEST_DIRS_OUT+['p2'],
            pypath.set_paths(['p1'], ['p2'],
                [('-a', [PATH_FILE, PATH_FILE])], False)
        )
        # Test add from file sequential.
        write_file(PATH_FILE, "\n".join(TEST_DIRS))
        self.assertEqual(
            TEST_DIRS_OUT+TEST_DIRS_OUT+['p2'],
            pypath.set_paths(['p1'], ['p2'],
                [('-a', [PATH_FILE]), ('-a', [PATH_FILE])], False)
        )

    def test_set_paths_remove(self):
        # Test remove not on PYTHONPATH (or path_list).
        with self.assertRaises(ValueError) as err:
            pypath.set_paths(['p1'], TEST_DIRS_OUT, [('-r', NOT_DIRS)], False)
        # Test remove not on PYTHONPATH (or path_list) force.
        self.assertEqual(TEST_DIRS_OUT,
            pypath.set_paths(['p1'], TEST_DIRS_OUT, [('-r', NOT_DIRS)], True))
        # Test remove as group.
        self.assertEqual(['p2'], pypath.set_paths(['p1'], NOT_DIRS_OUT+['p2'],
            [('-r', NOT_DIRS)], False))
        # Test remove sequential.
        self.assertEqual(['p2'], pypath.set_paths(['p1'], NOT_DIRS_OUT+['p2'],
            [('-r', [p]) for p in NOT_DIRS[-1::-1]], False))

    def test_set_paths_remove_from_file(self):
        # Test remove from file not on PYTHONPATH.
        write_file(PATH_FILE, "\n".join(NOT_DIRS))
        with self.assertRaises(ValueError) as err:
            pypath.set_paths(['p1'], TEST_DIRS_OUT, [('-r', [PATH_FILE])],
                False)
        # Test remove from file not on PYTHONPATH force.
        write_file(PATH_FILE, "\n".join(NOT_DIRS))
        self.assertEqual(TEST_DIRS_OUT,
            pypath.set_paths(['p1'], TEST_DIRS_OUT, [('-r', [PATH_FILE])],
                True))
        # Test remove from file as group.
        write_file(PATH_FILE, "\n".join(NOT_DIRS))
        self.assertEqual(['p2'], pypath.set_paths(['p1'], NOT_DIRS_OUT+['p2'],
            [('-r', [PATH_FILE, PATH_FILE])], False))
        # Test remove from file sequential.
        write_file(PATH_FILE, "\n".join(NOT_DIRS))
        self.assertEqual(['p2'], pypath.set_paths(['p1'], NOT_DIRS_OUT+['p2'],
            [('-r', [PATH_FILE]), ('-r', [PATH_FILE])], False))

    def test_set_paths(self):
        # Test add, then remove added (with extra remove).
        self.assertEqual([TEST_DIRS_OUT[1], 'p2'], pypath.set_paths(['p1'], ['p2'], [
            ('-a', [TEST_DIRS[0]]),
            ('-r', [TEST_DIRS[0]]), ('-r', [TEST_DIRS[0]]),
            ('-a', [TEST_DIRS[1]]),
        ], False))

    def test_parser(self):
        parser = pypath.get_parser()
        # Test flags.
        args = parser.parse_args(['-c', '-e', '-d', '-f'])
        self.assertTrue(args.clear)
        self.assertTrue(args.echo)
        self.assertTrue(args.permanent)
        self.assertTrue(args.force)
        # Test add, remove.
        with no_stderr():
            with self.assertRaises(SystemExit) as err:
                args = parser.parse_args(['-a'])    # Requires value.
            with self.assertRaises(SystemExit) as err:
                args = parser.parse_args(['-r'])    # Requires value.
        args = parser.parse_args(['-a', '1', '2', '-a', '3', '-r', '1', '2',
            '-r', '3'])
        self.assertEqual(args.actions, [
            ('-a', ['1', '2']),
            ('-a', ['3']),
            ('-r', ['1', '2']),
            ('-r', ['3']),
        ])

    def test_main(self):
        kwargs = dict(cwd='.', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Test no args.
        r, o, e = run('./pypath.py', **kwargs)
        self.assertEqual(pypath.HELP, r)
        self.assertEqual(0, len(e))
        self.assertTrue(pypath.USAGE in o)
        # Test help (return code 2).
        r, o, e = run(['./pypath.py', '-h'], **kwargs)
        self.assertEqual(pypath.HELP, r)
        self.assertEqual(0, len(e))
        self.assertTrue(pypath.USAGE in o)
        # Test success (return code 0).
        r, o, e = run(['./pypath.py', '-a'] + TEST_DIRS, **kwargs)
        self.assertEqual(pypath.SUCCESS, r)
        self.assertEqual(0, len(e))
        self.assertTrue(all([tdo in o for tdo in TEST_DIRS_OUT]))
        # Test error (return code 1).
        r, o, e = run(['./pypath.py', '-a'] + NOT_DIRS, **kwargs)
        self.assertEqual(pypath.ERROR, r)
        # Test force.
        r, o, e = run(['./pypath.py', '-f', '-a'] + NOT_DIRS, **kwargs)
        self.assertEqual(pypath.SUCCESS, r)
        self.assertEqual(0, len(e))
        self.assertTrue(all([tdo in o for tdo in TEST_DIRS_OUT]))
        # Test permanent.
        r, o, e = run(['./pypath.py', '-c', '-d', '-a'] + TEST_DIRS,
            **kwargs)
        self.assertEqual(pypath.SUCCESS, r)
        self.assertEqual(0, len(e))
        with open(DEFAULT_PATH_FILE, 'r') as fh:
            contents = fh.read()
        self.assertEqual(contents, "PYTHONPATH={}\nexport PYTHONPATH\n".format(
            "\nPYTHONPATH+=:".join(["'{}'".format(td) for td in TEST_DIRS_OUT])))


if __name__ == "__main__":
    unittest.main()

