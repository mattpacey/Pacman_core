#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -B
import unittest
import os
from os.path import join, dirname
import sys
import subprocess
import pwd
import glob
import shutil
sys.path.append(join(dirname(sys.argv[0]), ".."))
sys.path.append(os.getenv('PACMAN_ROOT'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/htd_te/bin'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'htd_info'))


from htd_fivr_fuse_action import FIVR_FUSE
import htd_basic_action
import htd_collaterals_parser
import htd_arguments_container
import htd_logger

from utils.files import TempDir, File
from utils.mock import patch, Mock, MagicMock
#from utils.ut import TestCase, unittest
from utils.helperclass import CaptureStdoutLog


class Test_FIVR_FUSE(unittest.TestCase):

    def setUp(self):
        self.fivr_fuse = FIVR_FUSE('action_name', 'source_file', 100, 'currentFlow', 'is_internal')

    def tearDown(self):
        idsid = pwd.getpwuid(os.getuid()).pw_name
        tmp = '/tmp/*' + idsid + '*'
        tmp_dir = glob.glob(tmp)

        for items in tmp_dir:
            if ('run_all_tests') in items:
                pass

            else:
                if os.path.isdir(items):
                    shutil.rmtree(items)
                elif os.path.exists(items):
                    os.remove(items)

    @patch('htd_basic_action.htd_base_action.__init__')
    @patch('htd_arguments_container.htd_argument_containter.declare_arg')
    def test_init(self, mock_declare, mock_action):
        self.fivr_fuse.__init__('action_name', 'source_file', 100, 'currentFlow', 'is_internal')
        mock_action.assertIn('FIVR_FUSE', 'action_name', 'source_file', 100, 'currentFlow', 'is_internal')
        mock_declare.assert_called_once_with("cfg_file", "The path to file define a test sequence in SPF format", "string", "none", 1)

    def test_verify_arguments(self):
        self.fivr_fuse.verify_arguments()

    def test_get_action_not_declared_argument_names(self):
        self.fivr_fuse.get_action_not_declared_argument_names()

#    def test_run(self):

# class Test_FIVR_FUSE_10NMSRVR(unittest.TestCase):


if __name__ == '__main__':
    unittest.main()
