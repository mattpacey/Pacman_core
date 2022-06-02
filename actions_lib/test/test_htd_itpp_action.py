#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -u

import os
from os.path import join, dirname
import unittest
import sys
import pwd
import shutil
import glob

sys.path.append(join(dirname(sys.argv[0]), ".."))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/htd_te/bin'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/htd_hpl/bin'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'htd_info'))

#from utils.ut import TestCase, unittest
from utils.mock import patch
from htd_itpp_action import ITPP
from htd_basic_action import *
from htd_basic_flow import *
from utils.files import TempDir
import htd_utilities
from htd_player_top import *


class ITPP_Test(unittest.TestCase):

    def setUp(self):
        self.tmpdir_obj = TempDir(name=True)
        self.tmpdir = self.tmpdir_obj.name()
        fo = open(self.tmpdir + "/lkfb_pmc_xreg.itpp", "w")
        fo.write('''label: SET_RSVD_ASW_7_2_1__0X20_I;''')
        fo.close()
        self.itpp_path = self.tmpdir + "/lkfb_pmc_xreg.itpp"
        self.itpp_obj = ITPP("a", self.itpp_path, 0, "b", "c")

    def tearDown(self):
        os.remove(self.tmpdir + "/lkfb_pmc_xreg.itpp")
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

    def test_init(self):
        self.assertEquals(self.itpp_obj.arguments.arg_l["itpp_file"]["description"], "The path to file define a test sequence in ITPP format")

    def test_get_action_not_declared_argument_names(self):
        self.itpp_obj.get_action_not_declared_argument_names()

    def test_verify_arguments(self):
        self.itpp_obj.verify_arguments()

    @patch("htd_player_top.htdPlayer.hpl_to_dut_interface.write_itpp_cmd")
    def test_run_with_itpp_defined(self, mock_write_itpp_cmd):
        # base_flow = htd_base_flow("", 1)
        # base_flow.exec_action_obj("", 1, {"actionName":"ITPP_TEST", "actionType":"ITPP", "itpp_file":self.itpp_path})
        self.itpp_obj.arguments.set_argument("itpp_file", self.itpp_path)
        self.itpp_obj.run()
        mock_write_itpp_cmd.assert_any_call("label: SET_RSVD_ASW_7_2_1__0X20_I;")

    @patch('htd_utilities.htdte_logger.error')
    def test_run_without_itpp_defined(self, mock_htdte_logger):
        # with patch.object(htd_utilities.htdte_logger, 'error') as mock:
        self.itpp_obj.run()
        mock_htdte_logger.assert_called_with("Can't open file none")


if __name__ == '__main__':         # pragma: no cover
    unittest.main()
