#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python

import os
from os.path import join, dirname
import unittest
import sys
import pwd
import glob
import shutil
sys.path.append(join(dirname(sys.argv[0]), ".."))
sys.path.append(os.getenv('PACMAN_ROOT'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/htd_te/bin'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'htd_info'))

from htd_basic_flow import *
from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
from htd_arguments_container import *
from htd_edram_fsm_action import *

from utils.files import TempDir
from utils.mock import patch, Mock, MagicMock
#from utils.ut import TestCase, unittest
from utils.helperclass import CaptureStdoutLog


class TestHtdEdramFsmAction(unittest.TestCase):

    def setUp(self):
        base_flow = htd_base_flow('', 1)
        self.EFSM = EFSM('action_name', 'source_file', 1, base_flow, 'is_internal')

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

    def test_init(self):
        self.EFSM.arguments.arg_l = {}
        self.EFSM.__init__('action_name', 'source_file', 1, 'currentFlow', 'is_internal')
        self.assertEqual(self.EFSM.arguments.arg_l['FSM_STATE']['default'], 'none')
        self.assertEqual(self.EFSM.arguments.arg_l['waitcycles']['default'], 0)
        self.assertEqual(self.EFSM.arguments.arg_l['run_pin']['default'], 'yyinitrun')
        self.assertEqual(self.EFSM.arguments.arg_l['ack_pin']['default'], 'yyINITACK')
        self.assertEqual(self.EFSM.arguments.arg_l['tb_hack_hook']['default'], '')

    @patch('htd_basic_action.htd_base_action.verify_obligatory_arguments')
    @patch('htd_logger.Logger.error')
    def test_verify_arguments(self, mock_logger_error, mock_verify_obligatory_arguments):
        self.EFSM.verify_arguments()
        mock_logger_error.assert_called_with("Invalid FSM State none")
        '''
        check error waitcycles
        '''
        self.EFSM.arguments.set_argument('waitcycles', -1)
        self.EFSM.verify_arguments()
        mock_logger_error.assert_called_with('Param waitcylcles must be positive')

    def test_get_action_not_declared_argument_names(self):
        self.EFSM.get_action_not_declared_argument_names()  # run through not doing any checking


if __name__ == '__main__':
    unittest.main()
