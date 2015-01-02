"""develop tests
"""
import os
import shutil
import tempfile
import types

import pytest

import pkg_resources
import setuptools.sandbox
from setuptools.sandbox import DirectorySandbox, SandboxViolation


class TestSandbox:

    def setup_method(self, method):
        self.dir = tempfile.mkdtemp()

    def teardown_method(self, method):
        shutil.rmtree(self.dir)

    def test_devnull(self):
        sandbox = DirectorySandbox(self.dir)
        sandbox.run(self._file_writer(os.devnull))

    @staticmethod
    def _file_writer(path):
        def do_write():
            with open(path, 'w') as f:
                f.write('xxx')
        return do_write

    def test_win32com(self):
        """
        win32com should not be prevented from caching COM interfaces
        in gen_py.
        """
        win32com = pytest.importorskip('win32com')
        gen_py = win32com.__gen_path__
        target = os.path.join(gen_py, 'test_write')
        sandbox = DirectorySandbox(self.dir)
        try:
            try:
                sandbox.run(self._file_writer(target))
            except SandboxViolation:
                self.fail("Could not create gen_py file due to SandboxViolation")
        finally:
            if os.path.exists(target):
                os.remove(target)

    def test_setup_py_with_BOM(self):
        """
        It should be possible to execute a setup.py with a Byte Order Mark
        """
        target = pkg_resources.resource_filename(__name__,
            'script-with-bom.py')
        namespace = types.ModuleType('namespace')
        setuptools.sandbox._execfile(target, vars(namespace))
        assert namespace.result == 'passed'

    def test_setup_py_with_CRLF(self):
        setup_py = os.path.join(self.dir, 'setup.py')
        with open(setup_py, 'wb') as stream:
            stream.write(b'"degenerate script"\r\n')
        setuptools.sandbox._execfile(setup_py, globals())
