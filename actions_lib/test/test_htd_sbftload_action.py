#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -u
"""
htd_stf_action unittests
"""
import os
from os.path import join, dirname
import unittest
import sys
import pwd
sys.path.append(join(dirname(sys.argv[0]), ".."))
sys.path.append(os.getenv('PACMAN_ROOT'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/htd_te/bin'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'htd_info'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'project/htd_global_content_lib/collaterals_ui'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/htd_hpl/bin'))

from htd_collaterals import *
from htd_sbftload_action import *
#from htd_basic_action import *
from htd_spf_stf_info import *
from htd_hpl_spf_interface import *
from htd_hpl_itpp_interface import *

from utils.files import TempDir, File
from utils.mock import patch, Mock, MagicMock, call
#from utils.ut import TestCase, unittest
#from htd_arguments_containter import *
import pdb
import shutil
import os
import glob
from utils.helperclass import CaptureStdoutLog
# from htd_basic_action import *
# from htd_utilities import *
# from htd_collaterals import *
# from htd_player_top import *
# from htd_basic_flow import *


class TestHtdSbftloadAction(unittest.TestCase):

    def setUp(self):
        pass

    def test_verify_arguments(self):
        a = SBFTLOAD('test_verify_arguments', 'test_source_file', 10, None, 'test_is_internal')

        # HTD_COLLECT_RTL_SIGNALS_MODE is 1
        os.environ['HTD_COLLECT_RTL_SIGNALS_MODE'] = '1'
        self.assertEqual(a.verify_arguments(), None)
        os.environ.pop('HTD_COLLECT_RTL_SIGNALS_MODE')

       # error: HTD_SBFT_CPL_LOCATION is None
        with self.assertRaises(SystemExit):
            with CaptureStdoutLog() as p:
                a.verify_arguments()
        self.assertIn("Missing obligatory unix environment ENV[HTD_SBFT_CPL_LOCATION] - must point to to HTD CPL path", p.getvalue())

        # error: HTD_SBFT_CPL_OUTPUT_FILE_NAME is None
        with self.assertRaises(SystemExit):
            with CaptureStdoutLog() as p:
                os.environ['HTD_SBFT_CPL_LOCATION'] = '1'
                a.verify_arguments()
        self.assertIn("Missing obligatory unix environment ENV[HTD_SBFT_CPL_OUTPUT_FILE_NAME] - cpl default name", p.getvalue())

        # set below env for below testing
        os.environ['HTD_SBFT_CPL_LOCATION'] = '1'
        os.environ['HTD_SBFT_CPL_OUTPUT_FILE_NAME'] = '1'

        # error: file_basename do not have obj extension
        # For coverage, use the newline as filename
        # TODO: This error can be remove from the code because the .obj extension was add in the code
        with self.assertRaises(SystemExit):
            with CaptureStdoutLog() as p:
                a.arguments.set_argument("input_file", 'aaa/bbb/\n')
                a.verify_arguments()
        self.assertIn("Expecting an OBJ file (e.g. None.obj) as input, not", p.getvalue())

        # error: input file not exists
        # TODO: enhance the erro message if cpl file not exists
        with self.assertRaises(SystemExit):
            with CaptureStdoutLog() as p:
                a.arguments.set_argument("input_file", 'aaa/bbb/ccc.obj')
                a.cpl_file_exists = 1
                a.verify_arguments()
        self.assertIn("input file ccc.obj does not exist", p.getvalue())

        # # error:
        # with TempDir(name=True, chdir=True) as temp_dir:
        #     # with self.assertRaises(SystemExit):
        #     #    with CaptureStdoutLog() as p:
        #     input_file = join(temp_dir, "ccc.obj")
        #     File(input_file).touch()
        #     a.arguments.set_argument("input_file", input_file)
        #     a.cpl_file_exists = 1
        #     a.verify_arguments()

    # def tearDown(self):
    #     username = pwd.getpwuid(os.geteuid()).pw_name
    #     for file in glob('/tmp/collateral_interface_socket*'):
    #         if username in file:
    #             os.remove(file)
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


if __name__ == '__main__':
    unittest.main()
