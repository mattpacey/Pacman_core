#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -B
"""
Unittest for htd_tap_action.py
"""

import unittest
import sys
import os
import filecmp
from os.path import join, dirname
import pwd
import glob
import shutil

sys.path.append(join(dirname(sys.argv[0]), ".."))
sys.path.append(os.getenv('PACMAN_ROOT'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/htd_te/bin'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/htd_hpl/bin'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'htd_info'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/utils'))

#from htd_hpl_itpp_interface import hpl_itpp_interface
#from htd_player_top import htdPlayer
from tools.htd_te.bin.htd_arguments_container import htd_action_argument_entry
from utils.mock import patch, Mock, MagicMock
from utils.files import TempDir
from utils.helperclass import CaptureStdoutLog
#from tools.utils.mock import MagicMock, patch, Mock
from actions_lib.htd_tap_action import TAP_activity_logger, TAP
from htd_basic_flow import *


class TestTAPActivityLogger(unittest.TestCase):

    def setUp(self):
        self.action = "abc"
        self.agent = "tap"
        self.pattern_label = {1: 'tap1_aa', 2: 'tap2_bb'}
        self.stimulus_value = '11'
        self.expected_value = ['dummy', 'dummy2', 'dummy3']

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

    def test_write_data(self):
        """test write_data when CFG is defined """
        with TempDir(chdir=True, delete=True, name=True) as tdir:
            log = TAP_activity_logger()
            log.write_data(self.action, self.agent, self.pattern_label, self.stimulus_value, self.expected_value)

            f = open(join(tdir, "file.csv"), "w+")
            f.write("action,agent,pattern label,stimulus length,stimulus value,expected length,expected_value\n"
                    "abc,tap,tap1_aa@1;tap2_bb@2,2,0b11,3,['dummy', 'dummy2', 'dummy3']\n",
                    )
            f.close()

            self.assertTrue(os.path.exists(join(tdir, 'TapLogger.csv')))
#            self.assertTrue(filecmp.cmp(join(tdir,"file.csv"), join(tdir,'TapLogger.csv'), shallow=False))

        # with user defined logger_filename
        with TempDir(chdir=True, delete=True, name=True) as tdir:
            with patch.dict('htd_collaterals_parser.CFG', {"TapActivityLogger": {"enabled": 1, "logger_filename": join(tdir, "tap.csv")}}):
                log = TAP_activity_logger()
                log.write_data(self.action, self.agent, self.pattern_label, self.stimulus_value, self.expected_value)

                f = open(join(tdir, "file.csv"), "w+")
                f.write("action,agent,pattern label,stimulus length,stimulus value,expected length,expected_value\n"
                        "abc,tap,tap1_aa@1;tap2_bb@2,2,0b11,3,['dummy', 'dummy2', 'dummy3']\n",
                        )
                f.close()
                self.assertFalse(os.path.exists(join(tdir, 'TapLogger.csv')))
                self.assertTrue(os.path.exists(join(tdir, 'tap.csv')))
#                self.assertTrue(filecmp.cmp(join(tdir,"file.csv"), join(tdir,'tap.csv'), shallow=False))

        # without looger_filename
        with TempDir(chdir=True, delete=True, name=True) as tdir:
            with patch.dict('htd_collaterals_parser.CFG', {"TapActivityLogger": {"enabled": 1}}):
                log = TAP_activity_logger()
                log.write_data(self.action, self.agent, self.pattern_label, self.stimulus_value, self.expected_value)
                self.assertTrue(os.path.exists(join(tdir, 'TapLogger.csv')))

    def test_no_write_data(self):
        with TempDir(chdir=True, delete=True, name=True) as tdir:
            with patch.dict('htd_collaterals_parser.CFG', {"TapActivityLogger": {"enabled": 0}}):
                log = TAP_activity_logger()
                log.write_data(self.action, self.agent, self.pattern_label, self.stimulus_value, self.expected_value)
                self.assertFalse(os.path.exists(join(tdir, 'TapLogger.csv')))


class TestTap(unittest.TestCase):

    def setUp(self):
        self.actionname = "test_action"
        self.sourcefile = "test_file"
        self.sourcelineno = 0
        self.currentflow = "test_flow"
        self.is_internal = False
        self.arguments = {'ir': 'TAPSTATUS',
                          'agent': 'EDRAM',
                          'actionName': 'ReadEDRAMTapStatus',
                          'actionType': 'TAP'
                          }

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

    @patch("dts_spf_tap_info.dts_spf_tap_info.get_ir_fields")
    def test_get_action_not_declared_argument_names(self, mock_ir):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.irname = "ir1"
            tapaction.agent = "agent1"
            tapaction.get_action_not_declared_argument_names()
            mock_ir.assert_called_once_with("ir1", "agent1")

    def test_verify_arguments(self):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)

            tapaction.arguments.arg_l = Mock()
            tapaction.arguments.arg_l = {'ir': {'assigned': 0, 'declared': 1, 'description': '', 'default': 1, 'obligatory': 0, 'type': 'int'},
                                         'dri': {'assigned': 0, 'declared': 1, 'description': '', 'default': 1, 'obligatory': 1, 'type': 'int'}
                                         }

            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    tapaction.verify_arguments()
            self.assertIn("Missing obligatory argument \"dri\" in accessing Action:test_action", log.getvalue())
            self.assertEqual(cm.exception.code, 257)

    @patch('htd_arguments_container.htd_argument_containter.get_not_declared_arguments')
    def test_verify_arguments_check_args(self, mock_xarg):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.arguments.arg_l = Mock()
            # check ir
            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': True, 'default': '', 'type': ''},
                                         }
            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    tapaction.verify_arguments()
            self.assertIn("illegal argument -\"ir\" type - \"<class 'bool'>\".Expected int or str.", log.getvalue())

            # check dri
            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string_or_int'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': 10855845, 'default': -1, 'type': 'int', 'msb': -1}, }
            xargs = {'field1': {'assigned': 1, 'declared': 0}}
            mock_xarg.return_value = xargs
            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    tapaction.verify_arguments()
            self.assertIn("illegal arguments combination: \"dri\"=10855845 argument", log.getvalue())

            # check mask_dro
            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string_or_int'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': -1, 'default': -1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'int', 'msb': -1},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'int'}, }

            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    tapaction.verify_arguments()
            self.assertIn("illegal arguments combination: \"mask_dro\"=1 argument", log.getvalue())

            # check dro with not declared args
            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string_or_int'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': -1, 'default': -1, 'type': 'int', 'msb': -1},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                         'dro': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'int'}, }

            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    tapaction.verify_arguments()
            self.assertIn("illegal arguments combination: \"dro\"=1 argument could not be used with per field assignment", log.getvalue())

            # check dro with read_type
            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string_or_int'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': -1, 'default': -1, 'type': 'int', 'msb': -1},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'type': 'int'},
                                         'dro': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'int'},
                                         'read_type': {'assigned': 0, 'declared': 1, 'default': 0, 'obligatory': 0, 'type': 'bool'}, }
            xargs = {}
            mock_xarg.return_value = xargs
            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    tapaction.verify_arguments()
            self.assertIn("illegal arguments combination: \"dro\"=1 argument should be used in couple with \"read_type\"=1 only.", log.getvalue())

    @patch('htd_arguments_container.htd_argument_containter.get_not_declared_arguments')
    def test_verify_arguments_check_args_1(self, mock_xarg):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': '', 'default': '', 'type': 'string'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': -1, 'default': -1, 'type': 'int', 'msb': -1},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'type': 'int'},
                                         'dro': {'assigned': 0, 'declared': 1, 'default': 1, 'type': 'int'},
                                         'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'type': 'bool'}, }
            xargs = {}
            mock_xarg.return_value = xargs
            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    tapaction.verify_arguments()
            self.assertIn("no irname and no ircode has been assigned", log.getvalue())

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            # check irname not empty, ircode is 0
            with patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_opcode_int', return_value=0):
                tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string'},
                                             'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': -1, 'default': -1, 'type': 'int', 'msb': -1},
                                             'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                             'dro': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'int'},
                                             'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                             'agent': {'assigned': 1, 'declared': 1, 'val': 'LGCIO_PCH_DFX_TAP', 'default': '', 'type': 'string'}, }
                self.assertEqual(tapaction.verify_arguments(), None)

            # check ircode>0 , irname=""
            with patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_name', return_value=""):
                tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 50, 'default': '', 'type': 'int'},
                                             'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': -1, 'default': -1, 'type': 'int', 'msb': -1},
                                             'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'type': 'int'},
                                             'dro': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'int'},
                                             'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                             'agent': {'assigned': 1, 'declared': 1, 'val': 'LGCIO_PCH_DFX_TAP', 'default': '', 'type': 'string'}, }
                self.assertEqual(tapaction.verify_arguments(), None)

    @patch('htd_arguments_container.htd_argument_containter.get_not_declared_arguments')
    def test_verify_arguments_check_args_2(self, mock_xarg):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink",
                                                               "excluded_parallel_agents": "tapA,tapB,tapC,tapD",
                                                               "switch_par2ser_pscand_dis": 1}}):
            # dri > 0 amd msb > 0
            with patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_opcode_int', return_value=11):
                tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'obligatory': 1, 'type': 'string'},
                                             'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': 60, 'default': -1, 'type': 'int', 'msb': 50},
                                             'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                             'dro': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'int'},
                                             'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                             'agent': {'assigned': 1, 'declared': 1, 'val': 'tapA', 'default': '', 'type': 'string'},
                                             'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                             'drsize': {'assigned': 0, 'declared': 1, 'default': 45, 'obligatory': 0, 'type': 'int'}
                                             }
                with self.assertRaises(SystemExit) as cm:
                    with CaptureStdoutLog() as log:
                        tapaction.verify_arguments()
                self.assertIn("Agent tapA can't run in parallel, setting it to run in serial", log.getvalue())
                self.assertIn("Trying to assign tap raw data (\"dri\[lsb:50]\") out of register size -45", log.getvalue())

                # check dro > 0,
                tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'obligatory': 1, 'type': 'string'},
                                             'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': -1, 'default': -1, 'type': 'int', 'msb': 40},
                                             'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                             'dro': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'int', 'msb': 50, 'lsb': 1},
                                             'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                             'agent': {'assigned': 1, 'declared': 1, 'val': 'tapB', 'default': '', 'type': 'string'},
                                             'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                             'drsize': {'assigned': 0, 'declared': 1, 'default': 45, 'obligatory': 0, 'type': 'int'}
                                             }
                with self.assertRaises(SystemExit) as cm:
                    with CaptureStdoutLog() as log:
                        tapaction.verify_arguments()
                self.assertIn("Trying to assign tap output raw data (\"dro[50:1]\") out of register size (\"drsize\"):45", log.getvalue())

                # check dro > 0, msb < drsize,
                tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'obligatory': 1, 'type': 'string'},
                                             'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': -1, 'default': -1, 'type': 'int', 'msb': 40},
                                             'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                             'dro': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'int', 'msb': 40, 'lsb': 1},
                                             'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                             'agent': {'assigned': 1, 'declared': 1, 'val': 'tapB', 'default': '', 'obligatory': 1, 'ever_accessed': 0, 'type': 'string'},
                                             'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                             'drsize': {'assigned': 0, 'declared': 1, 'default': 45, 'obligatory': 0, 'type': 'int'}
                                             }
                with self.assertRaises(SystemExit) as cm:
                    with CaptureStdoutLog() as log:
                        tapaction.verify_arguments()
                self.assertNotIn("Trying to assign tap output raw data (\"dro[50:1]\") out of register size (\"drsize\"):45", log.getvalue())

                # dri and dro msb < drsize
                tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'obligatory': 1, 'type': 'string'},
                                             'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': 60, 'default': 0, 'type': 'int', 'msb': 40},
                                             'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                             'dro': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'int', 'msb': 40},
                                             'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                             'agent': {'assigned': 1, 'declared': 1, 'val': 'tapA', 'default': '', 'type': 'string'},
                                             'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                             'drsize': {'assigned': 0, 'declared': 1, 'default': 45, 'obligatory': 0, 'type': 'int'}
                                             }
                with self.assertRaises(SystemExit) as cm:
                    with CaptureStdoutLog() as log:
                        tapaction.verify_arguments()
                self.assertNotIn("Trying to assign tap raw data", log.getvalue())

            # check auto switching action
            with patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_opcode_int', return_value=11):
                with patch('htd_tap_action.TAP.noa_offset_mode_needed', return_value=0):
                    tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                    tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'obligatory': 1, 'type': 'string'},
                                                 'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': -1, 'default': -1, 'type': 'int', 'msb': -1},
                                                 'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                                 'dro': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'int'},
                                                 'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                                 'agent': {'assigned': 1, 'declared': 1, 'val': 'tapE', 'default': '', 'type': 'string'},
                                                 'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'}, }
                    with self.assertRaises(SystemExit) as cm:
                        with CaptureStdoutLog() as log:
                            tapaction.verify_arguments()
                    self.assertIn("Auto switching action to serial mode as this is a read and pscand is not enabled!", log.getvalue())

            # check auto switching action
            with patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_opcode_int', return_value=11):
                with patch('htd_tap_action.TAP.noa_offset_mode_needed', return_value=1):
                    tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                    tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'obligatory': 1, 'type': 'string'},
                                                 'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'val': -1, 'default': -1, 'type': 'int', 'msb': -1},
                                                 'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                                 'dro': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'int'},
                                                 'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                                 'agent': {'assigned': 1, 'declared': 1, 'val': 'tapE', 'default': '', 'type': 'string'},
                                                 'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'}, }
                    with self.assertRaises(SystemExit) as cm:
                        with CaptureStdoutLog() as log:
                            tapaction.verify_arguments()
                    self.assertNotIn("Auto switching action to serial mode as this is a read and pscand is not enabled!", log.getvalue())

    @patch('htd_arguments_container.htd_argument_containter.get_argument_src', return_value="assign1")
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_fields', return_value=["field1", "field2", "field3", "field4"])
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_size', return_value=2)
    @patch('htd_arguments_container.htd_argument_containter.get_not_declared_arguments')
    def test_verify_arguments_check_args_3(self, mock_xarg, mock_irsize, mock_irfields, mock_assign):
        # check fields in not declared argument
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink",
                                                               "excluded_parallel_agents": "tapA,tapB,tapC,tapD",
                                                               "switch_par2ser_pscand_dis": 1}}):
            with patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_opcode_int', return_value=11):
                tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string'},
                                             'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'default': -1, 'type': 'int'},
                                             'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                             'dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                             'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                             'agent': {'assigned': 1, 'declared': 1, 'val': 'tapA', 'default': '', 'type': 'string'},
                                             'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                             'drsize': {'assigned': 0, 'declared': 1, 'default': 45, 'obligatory': 0, 'type': 'int'}
                                             }
                mock_xarg.return_value = {'fieldXX': {'assigned': 1, 'declared': 0}}
                tapaction.dummy_mode = 0
                with self.assertRaises(SystemExit) as cm:
                    with CaptureStdoutLog() as log:
                        tapaction.verify_arguments()
                self.assertIn("Illegal field-\"fieldXX\" name used in action(test_action) definition at assign1.", log.getvalue())

                tapaction.dummy_mode = 1
                self.assertEqual(tapaction.verify_arguments(), None)

    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_opcode_int', return_value=11)
    @patch('htd_arguments_container.htd_argument_containter.get_argument_src', return_value="assign1")
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_fields', return_value=["field1", "field2", "field3", "field4"])
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_size', return_value=2)
    @patch('htd_arguments_container.htd_argument_containter.get_not_declared_arguments')
    def test_verify_arguments_check_args_4(self, mock_xarg, mock_irsize, mock_irfields, mock_assign, mock_opcode):
        # check read_modify_write argument
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink",
                                                               "excluded_parallel_agents": "tapA,tapB,tapC,tapD",
                                                               "switch_par2ser_pscand_dis": 1}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'default': -1, 'type': 'int'},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                         'dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                         'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'agent': {'assigned': 1, 'declared': 1, 'val': 'tapA', 'default': '', 'type': 'string'},
                                         'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'drsize': {'assigned': 0, 'declared': 1, 'default': 45, 'obligatory': 0, 'type': 'int'},
                                         'read_modify_write': {'assigned': 1, 'declared': 1, 'val': 1, 'default': 0, 'type': 'bool'},
                                         'incremental_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'type': 'bool'},
                                         }

            mock_xarg.return_value = {'dri': {'assigned': 1, 'declared': 0}}
            tapaction.dummy_mode = 0
            with patch('htd_hpl_signal_manager.hpl_SignalManager_non_interactive.is_interactive_mode', return_value=1):
                with patch('dts_spf_tap_info.dts_spf_tap_info.rtl_node_exists', return_value=""):
                    with self.assertRaises(SystemExit) as cm:
                        with CaptureStdoutLog() as log:
                            tapaction.verify_arguments()
                    self.assertIn("Missing documented field-\"field1\"(action:\"test_action\") rtl node , while read_modify_write mode enabled ", log.getvalue())

            with patch('dts_spf_tap_info.dts_spf_tap_info.rtl_node_exists', return_value="node1"):
                with patch('dts_spf_tap_info.dts_spf_tap_info.get_rtl_endpoint', return_value="endpoint1"):
                    with patch('htd_hpl_signal_manager.hpl_SignalManager_non_interactive.is_interactive_mode', return_value=1):
                        with patch('htd_hpl_signal_manager.hpl_SignalManager_non_interactive.signal_exists', return_value=False):
                            with self.assertRaises(SystemExit) as cm:
                                with CaptureStdoutLog() as log:
                                    tapaction.verify_arguments()
                            self.assertIn("Rtl field integrity error-\"field1\"(action:\"test_action\") rtl node , while read_modify_write mode enabled", log.getvalue())

    @patch('dts_spf_tap_info.dts_spf_tap_info.get_field_msb', return_value=11)
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_field_lsb', return_value=1)
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_opcode_int', return_value=11)
    @patch('htd_arguments_container.htd_argument_containter.get_argument_src', return_value="assign1")
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_fields', return_value=["field1", "field2", "field3", "field4"])
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_size', return_value=2)
    @patch('htd_arguments_container.htd_argument_containter.get_not_declared_arguments')
    def test_verify_arguments_check_args_5(self, mock_xarg, mock_irsize, mock_irfields, mock_assign, mock_opcode, mock_lsb, mock_msb):
        # check arg value in not declard argument
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink",
                                                               "excluded_parallel_agents": "tapA,tapB,tapC,tapD",
                                                               "switch_par2ser_pscand_dis": 1}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            self.mock_field = htd_action_argument_entry(argvalue=-1, src="", lsb=12, msb=20, strobe=-1, label=-1, capture=-1, mask=-1,
                                                        read_val=-1, zmode=-1, xmode=-1, access_type=HTD_VALUE_DEFAULT_ACCESS,
                                                        verify_arg=1, patmod_en=1, patmod_var=None)

            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'default': -1, 'type': 'int'},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                         'dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                         'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'agent': {'assigned': 1, 'declared': 1, 'val': 'tapA', 'default': '', 'type': 'string'},
                                         'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'drsize': {'assigned': 0, 'declared': 1, 'default': 45, 'obligatory': 0, 'type': 'int'},
                                         'read_modify_write': {'assigned': 1, 'declared': 1, 'val': 0, 'default': 0, 'type': 'bool'},
                                         'incremental_mode': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         'field1': {'assigned': 0, 'declared': 1, 'val': [self.mock_field], 'default': 1, 'type': 'bool'},
                                         }
            mock_xarg.return_value = {'field1': {'assigned': 1, 'declared': 0}}
            tapaction.dummy_mode = 0
            with patch('dts_spf_tap_info.dts_spf_tap_info.rtl_node_exists', return_value=1):
                with self.assertRaises(SystemExit) as cm:
                    with CaptureStdoutLog() as log:
                        tapaction.verify_arguments()
                self.assertIn("field (field1) sub range (12:20) exceed the field boundaries (1:11)", log.getvalue())

    @patch('dts_spf_tap_info.dts_spf_tap_info.get_field_lsb', return_value=2)
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_field_msb', return_value=20)
    @patch('htd_tap_info.htd_tap_info.insensitive_case_doc_field_name_match', return_value="field1")
    @patch('dts_spf_tap_info.dts_spf_tap_info.rtl_node_exists', return_value="node1")
    @patch('htd_arguments_container.htd_argument_containter.verify_obligatory_arguments')
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_opcode_int', return_value=11)
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_fields', return_value=["field1", "field2"])
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_size', return_value=2)
    @patch('htd_arguments_container.htd_argument_containter.get_not_declared_arguments')
    def test_verify_arguments_check_args_6(self, mock_xarg, mock_irsize, mock_irfields, mock_opcode, mock_verify, mock_node, mock_name, mock_msb, mock_lsb):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink", }}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            # check dri argument, error if > max_val
            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'default': 10, 'type': 'int', 'lsb': 1, 'msb': 0},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                         'dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': -1, 'type': 'int', 'lsb': 1, 'msb': 2},
                                         'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'agent': {'assigned': 1, 'declared': 1, 'val': 'tapA', 'default': '', 'type': 'string'},
                                         'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'drsize': {'assigned': 0, 'declared': 1, 'default': 2, 'obligatory': 0, 'type': 'int'},
                                         'read_modify_write': {'assigned': 1, 'declared': 1, 'val': 0, 'default': 0, 'type': 'bool'},
                                         'incremental_mode': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         }
            mock_xarg.return_value = {}
            tapaction.dummy_mode = 0
            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    tapaction.verify_arguments()
            self.assertIn("The tap input raw data assignment (\"dri\":0xa) exceed register size - 2 bit", log.getvalue())

            # check mask_dro argument, error if > max_val
            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'default': 0, 'type': 'int', 'lsb': 1, 'msb': 0},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': 10, 'obligatory': 0, 'type': 'int'},
                                         'dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': -1, 'type': 'int', 'lsb': 1, 'msb': 2},
                                         'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'agent': {'assigned': 1, 'declared': 1, 'val': 'tapA', 'default': '', 'type': 'string'},
                                         'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'drsize': {'assigned': 0, 'declared': 1, 'default': 2, 'obligatory': 0, 'type': 'int'},
                                         'read_modify_write': {'assigned': 1, 'declared': 1, 'val': 0, 'default': 0, 'type': 'bool'},
                                         'incremental_mode': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         }
            mock_xarg.return_value = {}
            tapaction.dummy_mode = 0
            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    tapaction.verify_arguments()
            self.assertIn("The tap input raw data assignment (\"mask_dro\":0xa) exceed register size - 2 bit", log.getvalue())

            # check dro argument, error if > max_val
            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'default': 0, 'type': 'int', 'lsb': 1, 'msb': 0},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': 0, 'obligatory': 0, 'type': 'int'},
                                         'dro': {'assigned': 0, 'declared': 1, 'default': 10, 'obligatory': -1, 'type': 'int', 'lsb': 1, 'msb': 0},
                                         'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'agent': {'assigned': 1, 'declared': 1, 'val': 'tapA', 'default': '', 'type': 'string'},
                                         'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'drsize': {'assigned': 0, 'declared': 1, 'default': 2, 'obligatory': 0, 'type': 'int'},
                                         'read_modify_write': {'assigned': 1, 'declared': 1, 'val': 0, 'default': 0, 'type': 'bool'},
                                         'incremental_mode': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         }
            mock_xarg.return_value = {}
            tapaction.dummy_mode = 0
            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    tapaction.verify_arguments()
            self.assertIn("The tap input raw data assignment (\"dro\":0xa) exceed register size - 2 bit", log.getvalue())

    @patch('dts_spf_tap_info.dts_spf_tap_info.get_field_msb', return_value=11)
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_field_lsb', return_value=1)
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_opcode_int', return_value=11)
    @patch('htd_arguments_container.htd_argument_containter.get_argument_src', return_value="assign1")
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_fields', return_value=["field1", "field2", "field3", "field4"])
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_size', return_value=2)
    @patch('htd_arguments_container.htd_argument_containter.get_not_declared_arguments')
    def test_verify_arguments_check_args_7(self, mock_xarg, mock_irsize, mock_irfields, mock_assign, mock_opcode, mock_lsb, mock_msb):
        # check argument is defined
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink",
                                                               "excluded_parallel_agents": "tapA,tapB,tapC,tapD",
                                                               "switch_par2ser_pscand_dis": 1}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            self.mock_field = htd_action_argument_entry(argvalue=-1, src="", lsb=-1, msb=-1, strobe=-1, label=-1, capture=-1, mask=-1,
                                                        read_val=-1, zmode=-1, xmode=-1, access_type=HTD_VALUE_DEFAULT_ACCESS,
                                                        verify_arg=1, patmod_en=1, patmod_var=None)

            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'default': -1, 'type': 'int'},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                         'dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                         'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'agent': {'assigned': 1, 'declared': 1, 'val': 'tapA', 'default': '', 'type': 'string'},
                                         'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'drsize': {'assigned': 0, 'declared': 1, 'default': 45, 'obligatory': 0, 'type': 'int'},
                                         'read_modify_write': {'assigned': 1, 'declared': 1, 'val': 0, 'default': 0, 'type': 'bool'},
                                         'incremental_mode': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         'check': {'assigned': 0, 'declared': 1, 'default': 1, 'type': 'bool'},
                                         'field1': {'assigned': 0, 'declared': 1, 'val': [self.mock_field], 'default': 1, 'type': 'bool'},
                                         }
            mock_xarg.return_value = {'field1': {'assigned': 1, 'declared': 0}}
            tapaction.dummy_mode = 0
            #rtl_node_exist is False
            with patch('dts_spf_tap_info.dts_spf_tap_info.rtl_node_exists', return_value=""):
                with self.assertRaises(SystemExit) as cm:
                    with CaptureStdoutLog() as log:
                        tapaction.verify_arguments()
                self.assertIn("Missing documented BYPASS->field1 (action:\"test_action\") rtl node", log.getvalue())

            with patch('dts_spf_tap_info.dts_spf_tap_info.rtl_node_exists', return_value="node1"):
                with patch('dts_spf_tap_info.dts_spf_tap_info.get_rtl_endpoint', return_value="endpoint1"):
                    with patch('htd_hpl_signal_manager.hpl_SignalManager_non_interactive.signal_exists', return_value=False):

                        with self.assertRaises(SystemExit) as cm:
                            with CaptureStdoutLog() as log:
                                tapaction.verify_arguments()
                        self.assertIn("Rtl field integrity error BYPASS->field1 (action:\"test_action\") rtl node", log.getvalue())

        # check bfm_mode argument is defined is not able to test since it get stop at "check" argument.

    @patch('dts_spf_tap_info.dts_spf_tap_info.get_field_msb', return_value=11)
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_field_lsb', return_value=1)
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_opcode_int', return_value=11)
    @patch('htd_arguments_container.htd_argument_containter.get_argument_src', return_value="assign1")
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_fields', return_value=["field1", "field2", "field3", "field4"])
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_size', return_value=2)
    @patch('htd_arguments_container.htd_argument_containter.get_not_declared_arguments')
    def test_verify_arguments_check_args_8(self, mock_xarg, mock_irsize, mock_irfields, mock_assign, mock_opcode, mock_lsb, mock_msb):

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink",
                                                               "excluded_parallel_agents": "tapA,tapB,tapC,tapD",
                                                               "switch_par2ser_pscand_dis": 1
                                                               }}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            self.mock_field = htd_action_argument_entry(argvalue=-1, src="", lsb=-1, msb=-1, strobe=-1, label=-1, capture=-1, mask=-1,
                                                        read_val=-1, zmode=-1, xmode=-1, access_type=HTD_VALUE_DEFAULT_ACCESS,
                                                        verify_arg=1, patmod_en=1, patmod_var=None)

            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'default': -1, 'type': 'int'},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                         'dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': 0, 'type': 'int'},
                                         'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'agent': {'assigned': 1, 'declared': 1, 'val': 'tapA', 'default': '', 'type': 'string'},
                                         'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'drsize': {'assigned': 0, 'declared': 1, 'default': 45, 'obligatory': 0, 'type': 'int'},
                                         'read_modify_write': {'assigned': 1, 'declared': 1, 'val': 0, 'default': 0, 'type': 'bool'},
                                         'incremental_mode': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         'check': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         'bfm_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'type': 'bool'},
                                         'pscand_en': {'assigned': 0, 'declared': 1, 'default': 1, 'type': 'bool'},
                                         'man_field_labels': {'assigned': 0, 'declared': 1, 'default': None, 'type': 'bool'},
                                         'overshift_en': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         'field1': {'assigned': 0, 'declared': 1, 'val': [self.mock_field], 'default': 1, 'type': 'bool'},
                                         }
            mock_xarg.return_value = {'field1': {'assigned': 1, 'declared': 0}}
            tapaction.dummy_mode = 0
            with patch('dts_spf_tap_info.dts_spf_tap_info.rtl_node_exists', return_value="node1"):
                #                with patch('dts_spf_tap_info.dts_spf_tap_info.get_rtl_endpoint', return_value="endpoint1"):
                #                    with patch('htd_hpl_signal_manager.hpl_SignalManager_non_interactive.signal_exists', return_value=False):
                tapaction.arguments.arg_l.update({'field_labels': {'assigned': 0, 'declared': 1, 'default': 1, 'type': 'bool'}})
                tapaction.verify_arguments()
                self.assertEqual(tapaction.field_labels_ena, 1)

                tapaction.arguments.arg_l.update({'field_labels': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'}})
                tapaction.arguments.arg_l.update({'field_labels_per_action': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'}})
                tapaction.verify_arguments()
                self.assertEqual(tapaction.field_labels_ena, 0)

                tapaction.arguments.arg_l.update({'man_field_labels': {'assigned': 0, 'declared': 1, 'default': "aa,bb", 'type': 'bool'}})
                tapaction.verify_arguments()
                self.assertEqual(tapaction.man_field_labels, ["aa", "bb"])

                # NEW_LABEL_SPEC=1
                with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": 1, "tap_mode": "taplink",
                                                                       "excluded_parallel_agents": "tapA,tapB,tapC,tapD",
                                                                       "switch_par2ser_pscand_dis": 1,
                                                                       "automatic_field_labels_ena": 1
                                                                       }}):
                    with patch("htd_basic_action.htd_base_action.get_curr_flow") as mock_actionname:
                        mock_actionname().phase_name = "DDDD"  # mock_actionname.phase_name = "aaa" returns MagicMock object
                        tapaction.verify_arguments()
                        self.assertEqual(tapaction.field_labels_ena, 0)

                # automatic_labels_ena defined
                with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink",
                                                                       "excluded_parallel_agents": "tapA,tapB,tapC,tapD",
                                                                       "switch_par2ser_pscand_dis": 1,
                                                                       "automatic_labels_ena": 0
                                                                       }}):
                    tapaction.verify_arguments()
                    self.assertEqual(tapaction.field_labels_ena, 0)

                # automatic_field_labels_ena defined
                with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink",
                                                                       "excluded_parallel_agents": "tapA,tapB,tapC,tapD",
                                                                       "switch_par2ser_pscand_dis": 1,
                                                                       "automatic_field_labels_ena": 1
                                                                       }}):
                    tapaction.verify_arguments()
                    self.assertEqual(tapaction.field_labels_ena, 1)

    @patch('dts_spf_tap_info.dts_spf_tap_info.get_field_lsb', return_value=2)
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_field_msb', return_value=20)
    @patch('htd_tap_info.htd_tap_info.insensitive_case_doc_field_name_match', return_value="field1")
    @patch('dts_spf_tap_info.dts_spf_tap_info.rtl_node_exists', return_value="node1")
    @patch('htd_arguments_container.htd_argument_containter.verify_obligatory_arguments')
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_opcode_int', return_value=11)
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_fields', return_value=["field1", "field2"])
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_ir_size', return_value=2)
    @patch('htd_arguments_container.htd_argument_containter.get_not_declared_arguments')
    def test_verify_arguments_check_args_9(self, mock_xarg, mock_irsize, mock_irfields, mock_opcode, mock_verify, mock_node, mock_name, mock_msb, mock_lsb):
        # checking on the overshift_en argument - fail case
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink",
                                                               "tap_bfm_mode": 12}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'default': 1, 'type': 'int', 'lsb': 1, 'msb': 0},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': 0, 'obligatory': 0, 'type': 'int'},
                                         'dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': -1, 'type': 'int', 'lsb': 1, 'msb': 0},
                                         'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'agent': {'assigned': 1, 'declared': 1, 'val': 'tapA', 'default': '', 'type': 'string'},
                                         'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'drsize': {'assigned': 0, 'declared': 1, 'default': 2, 'obligatory': 0, 'type': 'int'},
                                         'read_modify_write': {'assigned': 1, 'declared': 1, 'val': 0, 'default': 0, 'type': 'bool'},
                                         'incremental_mode': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         'pscand_en': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         'field_labels': {'assigned': 0, 'declared': 1, 'default': 1, 'type': 'bool'},
                                         'man_field_labels': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         'overshift_en': {'assigned': 0, 'declared': 1, 'default': 1, 'type': 'bool'},
                                         'overshift_marker': {'assigned': 0, 'declared': 1, 'default': None, 'type': 'bool'},
                                         'check': {'assigned': 1, 'declared': 1, 'val': 0, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         }
            mock_xarg.return_value = {}
            tapaction.dummy_mode = 0
            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    tapaction.verify_arguments()
            self.assertIn("The tap protocol taplink requires an overshift marker as a binary string", log.getvalue())

            # checking on the overshift_en argument - pass case
            tapaction.arguments.arg_l = {'ir': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string'},
                                         'dri': {'assigned': 1, 'declared': 1, 'lsb': -1, 'default': 1, 'type': 'int', 'lsb': 1, 'msb': 0},
                                         'mask_dro': {'assigned': 0, 'declared': 1, 'default': 0, 'obligatory': 0, 'type': 'int'},
                                         'dro': {'assigned': 0, 'declared': 1, 'default': -1, 'obligatory': -1, 'type': 'int', 'lsb': 1, 'msb': 0},
                                         'read_type': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'agent': {'assigned': 1, 'declared': 1, 'val': 'tapA', 'default': '', 'type': 'string'},
                                         'parallel_mode': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'drsize': {'assigned': 0, 'declared': 1, 'default': 2, 'obligatory': 0, 'type': 'int'},
                                         'read_modify_write': {'assigned': 1, 'declared': 1, 'val': 0, 'default': 0, 'type': 'bool'},
                                         'incremental_mode': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         'pscand_en': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         'field_labels': {'assigned': 0, 'declared': 1, 'default': 1, 'type': 'bool'},
                                         'man_field_labels': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         'overshift_en': {'assigned': 0, 'declared': 1, 'default': 0, 'type': 'bool'},
                                         'overshift_marker': {'assigned': 0, 'declared': 1, 'default': None, 'type': 'bool'},
                                         'check': {'assigned': 1, 'declared': 1, 'val': 0, 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         }

            mock_xarg.return_value = {}
            tapaction.dummy_mode = 0
            with CaptureStdoutLog() as log:
                tapaction.verify_arguments()
            self.assertNotIn("The tap protocol taplink requires an overshift marker as a binary string", log.getvalue())

    def test_update_bitlistrange(self):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            self.assertEqual(tapaction.update_bitlistrange(3, 5, [12345]), [12345, 3, 4, 5])

    def test_is_duplicate_field_already_set(self):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            field_duplicate_tracket = {"field1": ["ff1", "ff2"], "field2": ["ff3"], "field3": []}
            dr = {"ff1": 1, "ff2": 0}
            self.assertEqual(tapaction.is_duplicate_field_already_set("field1", field_duplicate_tracket, dr), (1, "ff1"))
            self.assertEqual(tapaction.is_duplicate_field_already_set("field2", field_duplicate_tracket, dr), (0, None))
            self.assertEqual(tapaction.is_duplicate_field_already_set("field3", field_duplicate_tracket, dr), (0, None))

    def test_get_field_default_val(self):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            with patch('htd_hpl_signal_manager.hpl_SignalManager.is_interactive_mode', return_value=1):
                with patch('dts_spf_tap_info.dts_spf_tap_info.get_field_reset_value', return_value=1):
                    tapaction.arguments.arg_l = {'read_modify_write': {'assigned': 1, 'declared': 1, 'val': 0, 'default': '', 'type': 'string'}}
                    self.assertEqual(tapaction.get_field_default_val("field"), 1)

# TODO: code error on htdPlayer.signal_peek ? htdPlayer.hplSignalMgr.signal_peek
#                with patch('dts_spf_tap_info.dts_spf_tap_info.get_field_reset_value', return_value = 1):
#                    with patch('dts_spf_tap_info.dts_spf_tap_info.get_rtl_endpoint', return_value="endpoint1"):
# with patch('htd_hpl_interactive_socket_interface.hpl_interactive_socket_interface.signal_peek', return_value=0):
#                        with patch('htd_hpl_signal_manager.hpl_SignalManager_non_interactive.signal_peek', return_value=0):
#                            tapaction.arguments.arg_l = {'read_modify_write': {'assigned': 1, 'declared': 1,'val': 1, 'default': '', 'type': 'string'}}
#                            self.assertEqual(tapaction.get_field_default_val("field"), 0)

    def test_transactor_label_assignment(self):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            labels = {1: "label1", 2: "label2", 3: "label3", 5: "label5"}
            tapaction.transactor_label_assignment(labels, 4, "label4")
            self.assertEqual(labels, {1: "label1", 2: "label2", 3: "label3", 4: "label4", 5: "label5"})
            tapaction.transactor_label_assignment(labels, 3, "extend_label")
            self.assertEqual(labels, {1: "label1", 2: "label2", 3: "extend_label__label3", 4: "label4", 5: "label5"})

#    @patch('htd_signal_info.htd_signal_info.normalize_to_32_bit_signals')
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_rtl_endpoint', return_value="path1")
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_field_lsb', return_value=1)
    @patch('dts_spf_tap_info.dts_spf_tap_info.get_field_msb', return_value=5)
    @patch('dts_spf_tap_info.dts_spf_tap_info.rtl_node_exists', return_value="node1")
    def test_check_tap_ep(self, mock_node, mock_msb, mock_lsb, mock_endpoint):  # , mock_signals):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            with patch('htd_hpl_signal_manager.hpl_SignalManager.signalset_pack', return_value=1):
                with patch('htd_hpl_signal_manager.hpl_SignalManager.signalset_wait') as mock_wait:
                    tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                    assigned_fields = {}
                    dr_assignment = {"ENABLE": 0}
                    tapaction.check_tap_ep(assigned_fields, dr_assignment, 1, 100, 'refclock', -1)
                    mock_wait.assert_not_called_with(1, 100, -1, 'refclock', 1, "")

                    mock_wait.reset_mock()
                    tapaction.check_tap_ep(assigned_fields, dr_assignment, -1, 100, 'refclock', -1)
                    mock_wait.assert_called_once_with(1, 100, -1, 'refclock', 1, "", [])

            with patch('htd_hpl_signal_manager.hpl_SignalManager.signalset_pack', return_value=1):
                with patch('htd_hpl_signal_manager.hpl_SignalManager.signalset_wait') as mock_wait:
                    with patch('htd_tap_action.TAP.field_should_be_verified', return_value=0):
                        tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                        assigned_fields = {"ENABLE": 11}
                        dr_assignment = {"ENABLE": 0}
                        tapaction.check_tap_ep(assigned_fields, dr_assignment, -1, 100, 'refclock', -1)
                        mock_wait.assert_called_once_with(1, 100, -1, 'refclock', 1, "", [])

            with patch('htd_hpl_signal_manager.hpl_SignalManager.signalset_pack', return_value=1):
                with patch('htd_hpl_signal_manager.hpl_SignalManager.signalset_wait') as mock_wait:
                    with patch('htd_tap_action.TAP.field_should_be_verified', return_value=1):
                        tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                        assigned_fields = {"ENABLE": 11}
                        dr_assignment = {"ENABLE": 0}
                        tapaction.check_tap_ep(assigned_fields, dr_assignment, -1, 100, 'refclock', -1)
                        # TODO: mock a method which return 2 values?
                        mock_wait.assert_called_once_with(1, 100, -1, 'refclock', 1, "", [])

    def test_field_should_be_verified(self):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            self.mock_field = htd_action_argument_entry(argvalue=-1, src="", verify_arg=1)
            tapaction.arguments.arg_l = {'field1': {'assigned': 1, 'declared': 1, 'val': [self.mock_field], 'default': '', 'type': 'string'}}
            self.assertEqual(tapaction.field_should_be_verified("field1"), 1)

            self.mock_field = htd_action_argument_entry(argvalue=-1, src="", verify_arg=0)
            tapaction.arguments.arg_l = {'field1': {'assigned': 1, 'declared': 1, 'val': [self.mock_field], 'default': '', 'type': 'string'}}
            self.assertEqual(tapaction.field_should_be_verified("field1"), 0)

    def test_transactor_strobe_properties_assignment(self):
        pass

    def test_TransactShiftIr(self):
        # mocking on CFG[HPL]["execution_mode"] = "itpp" not works due to htdPlayer set the object in __init__()
        # but the code did not go thru __init__(), hence it will point back to htd_hpl_spf_interface
        self.hpl_itpp_obj = hpl_itpp_interface("a", "b", "c")
        setattr(htdPlayer, "hpl_to_dut_interface", self.hpl_itpp_obj)
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            with patch('htd_hpl_itpp_interface.hpl_itpp_interface.ShiftIr') as mock_shiftir:
                tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                labels = {5: "Start_Ir", 10: "EndIr"}
                tapaction.TransactShiftIr("bin", 5, 3, labels)
                mock_shiftir.assert_called_once_with("bin", 5, {8: 'Start_Ir', 13: 'EndIr'})

    def test_TransactShiftDr(self):
        self.hpl_itpp_obj = hpl_itpp_interface("a", "b", "c")
        setattr(htdPlayer, "hpl_to_dut_interface", self.hpl_itpp_obj)
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}
                                                       }):
            with patch('htd_hpl_itpp_interface.hpl_itpp_interface.ShiftDr') as mock_shiftdr:

                tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                tapaction.TransactShiftDr(1, 1, 0, 0)
                mock_shiftdr.assert_called_once_with(1, 1, {}, {}, {}, {}, 0, 0)

                tapaction.TransactShiftDr(1, 4, 5, 1, {1: "label1", 2: "label2"}, {1: "mask1", 2: "mask2"}, {1: "captures1", 2: "captures2"}, {1: "strobes1", 2: "strobes1"})
                mock_shiftdr.assert_called_with(1, 4, {6: "label1", 7: "label2"}, {2: "mask1", 3: "mask2"}, {2: "captures1", 3: "captures2"}, {2: "strobes1", 3: "strobes1"}, 0, 0)

                #strobe_bit < 0
                tapaction.TransactShiftDr(1, 4, 5, -1, {1: "label1", 2: "label2"}, {1: "mask1", 2: "mask2"}, {1: "captures1", 2: "captures2"}, {1: "strobes1", 2: "strobes1"})
                mock_shiftdr.assert_called_with(1, 4, {6: "label1", 7: "label2"}, {1: "mask1", 2: "mask2"}, {1: "captures1", 2: "captures2"}, {1: "strobes1", 2: "strobes1"}, 0, 0)

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"},
                                                       "SliceInfo": "1,2,3,4"}):
            with patch('htd_tap_action.TAP.noa_offset_mode_needed', return_value=1):
                with patch('htd_tap_action.TAP.get_noa_offset_pins_and_delay', return_value=(['pin1', 'pin2', 'pin3'], [2, 2, 2])):
                    with patch('htd_tap_action.TAP.get_slices_list', return_value=[1, 3, 4, 5]):
                        with patch('htd_hpl_itpp_interface.hpl_itpp_interface.ShiftParallelDr') as mock_shiftpdr:
                            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                            tapaction.TransactShiftDr(1, 10, 5, 5, {1: "label1", 2: "label2"}, {1: "mask1", 2: "mask2"}, {1: "captures1", 2: "captures2"}, {1: "strobes1", 2: "strobes1"})
                            mock_shiftpdr.assert_called_with(1, 10, {6: "label1", 7: "label2"}, {6: "mask1", 7: "mask2"}, ["pin2"], {6: "captures1", 7: "captures2"}, {6: "strobes1", 7: "strobes1"}, [3])

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"},
                                                       "SliceInfo": "1,2,3,4"}):
            with patch('htd_tap_action.TAP.noa_offset_mode_needed', return_value=1):
                with patch('htd_tap_action.TAP.get_noa_offset_pins_and_delay', return_value=(['pin1', 'pin2', 'pin3'], [2, 2, 2])):
                    with patch('htd_tap_action.TAP.get_slices_list', return_value=[1, 3, 4, 5]):
                        with patch('htd_hpl_itpp_interface.hpl_itpp_interface.ShiftParallelDr') as mock_shiftpdr:
                            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                            tapaction.arguments.arg_l = {'first_rdbit_label': {'assigned': 1, 'declared': 1, 'val': 'BYPASS', 'default': '', 'type': 'string'}}
                            tapaction.TransactShiftDr(1, 10, 5, 5, {1: "label1", 2: "label2"}, {1: "mask1", 2: "mask2"}, {1: "captures1", 2: "captures2"}, {1: "strobes1", 2: "strobes1"})
                            mock_shiftpdr.assert_called_with(1, 10, {5: "BYPASS", 6: "label1", 7: "label2"}, {6: "mask1", 7: "mask2"}, ["pin2"], {6: "captures1", 7: "captures2"}, {6: "strobes1", 7: "strobes1"}, [3])

    def test_noa_offset_mode_needed(self):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):

            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.parallel = 0
            res = tapaction.noa_offset_mode_needed(1)
            self.assertEqual(res, 0)
            res = tapaction.noa_offset_mode_needed(0)
            self.assertEqual(res, 0)

            with patch('htd_arguments_container.htd_argument_containter.get_argument', return_value=None):
                tapaction.parallel = 1
                res = tapaction.noa_offset_mode_needed(1)
                self.assertEqual(res, 0)

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}, "NoaOffsets": {"supported_taps": "tapA,tapB,tapC"}}):
            with patch('htd_arguments_container.htd_argument_containter.get_argument', return_value=True):
                with patch('htd_tap_action.TAP.noa_offset_enabled', return_value=True):
                    tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                    tapaction.parallel = 1

                    tapaction.agent = "tapE"
                    res = tapaction.noa_offset_mode_needed(1)
                    self.assertEqual(res, False)

                    tapaction.agent = "tapB"
                    res = tapaction.noa_offset_mode_needed(1)
                    self.assertEqual(res, True)

                with patch('htd_tap_action.TAP.noa_offset_enabled', return_value=False):
                    tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                    tapaction.parallel = 1

                    tapaction.agent = "tapB"
                    res = tapaction.noa_offset_mode_needed(1)
                    self.assertEqual(res, 0)

    @patch('htd_logger.Logger.inform')
    def test_noa_offset_enabled(self, mock_inform):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            self.assertEqual(tapaction.noa_offset_enabled(), 0)

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink", "disable_pscand": 1}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            res = tapaction.noa_offset_enabled()
            mock_inform.assert_called_once_with("Pscand was disabled by setting 'disable_pscand' key. Will use scand instead")
            self.assertEqual(res, 0)
            mock_inform.reset_mock()

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink", "disable_pscand": 0}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            self.assertEqual(tapaction.noa_offset_enabled(), 0)

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink", "disable_pscand": 0},
                                                       "NoaOffsets": {"enabled": 1}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            self.assertEqual(tapaction.noa_offset_enabled(), 1)

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}, "NoaOffsets": {"enabled": 1}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            self.assertEqual(tapaction.noa_offset_enabled(), 1)

    def test_get_pscan_type(self):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            self.assertEqual(tapaction.get_pscan_type(), (None, None))

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.agent = "CORE_ABC"
            self.assertEqual(tapaction.get_pscan_type(), ("core", "slices_index"))

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}, "SliceInfo": "cores_index"}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.agent = "CORE_ABC"
            self.assertEqual(tapaction.get_pscan_type(), ("core", "cores_index"))

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.agent = "CBO_ABC"
            self.assertEqual(tapaction.get_pscan_type(), ("cbo", "slices_index"))

    def test_get_noa_offset_pins_and_delay(self):

        with patch("htd_tap_action.TAP.get_pscan_type", return_value=(None, None)):
            with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"},
                                                           "NoaOffsets": {"abc_noa_pins": "L,X,J,F", "abc_offset": "1,2,3,4"}}):
                with patch('htd_arguments_container.htd_argument_containter.get_argument', return_value=None):
                    tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                    tapaction.agent = "aaa"
                    with self.assertRaises(SystemExit) as cm:
                        with CaptureStdoutLog() as log:
                            tapaction.get_noa_offset_pins_and_delay()
                    self.assertIn("NOA offset pins and offsets for tap agent aaa were not found", log.getvalue())

        with patch("htd_tap_action.TAP.get_pscan_type", return_value=("cbo", "slices_index")):
            with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"},
                                                           "NoaOffsets": {"abc_noa_pins": "L,X,J,F",
                                                                          "abc_offsets": "1,2,3,4"}}):
                with patch('htd_arguments_container.htd_argument_containter.get_argument', return_value="abc"):
                    tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                    res1, res2 = tapaction.get_noa_offset_pins_and_delay()
                    self.assertEqual(res1, ['L', 'X', 'J', 'F'])
                    self.assertEqual(res2, ['1', '2', '3', '4'])

            with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"},
                                                           "NoaOffsets": {"abc_noa_pins": "L,X,J,F",
                                                                          "abc_offsets": "1,2,3,4",
                                                                          "offset_lookup": "tapA:2,tapB:5"
                                                                          }}):
                with patch('htd_arguments_container.htd_argument_containter.get_argument', return_value="abc"):
                    tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                    tapaction.agent = "tapA"
                    res1, res2 = tapaction.get_noa_offset_pins_and_delay()
                    self.assertEqual(res1, ['L', 'X', 'J', 'F'])
                    self.assertEqual(res2, ['1', '2', '3', '4'])

            with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"},
                                                           "NoaOffsets": {"abc_noa_pins": "L,X,J,F",
                                                                          "abc_offsets": "1,2,3,4",
                                                                          "offset_lookup": "tapA:mock_offset",
                                                                          "mock_offset": "4,5,6"
                                                                          }}):
                with patch('htd_arguments_container.htd_argument_containter.get_argument', return_value="abc"):
                    tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                    tapaction.agent = "tapA"
                    res1, res2 = tapaction.get_noa_offset_pins_and_delay()
                    self.assertEqual(res1, ['L', 'X', 'J', 'F'])
                    self.assertEqual(res2, ['1', '2', '3', '4'])

    def test_transactgotostate(self):
        #        with patch.dict('htd_collaterals_parser.CFG',{"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
        #            with patch("htd_hpl_spf_interface.hpl_spf_interface") as mock_spf:
        #                with patch('htd_player_ui.htd_player_ui') as mock_player:
        #                    tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
        #    #                tap_state = "abcd"
        #                    mock_spf.to_state.return_value = "aaa"
        #                    tapaction.TransactGotoState("abcd")
        #                    mock_player.assert_called_once()
        pass

    def test_low_level_tap_bfm_transactor(self):
        pass

    def test_get_pscand_params(self):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            with patch('htd_tap_action.TAP.noa_offset_mode_needed', return_value=0):
                tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                tapaction.pscand_en = 0
                self.assertEqual(tapaction.get_pscand_params(), (0, [''], [0]))

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            with patch('htd_tap_action.TAP.noa_offset_mode_needed', return_value=1):
                with patch('htd_tap_action.TAP.get_noa_offset_pins_and_delay', return_value=(['L', 'X', 'J', 'F'], ['1'])):
                    with patch('htd_tap_action.TAP.get_pscan_type', return_value=("core", "core_slices")):
                        with patch('htd_tap_action.TAP.get_slices_list', return_value=[1, 3, 5, 6]):
                            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                            tapaction.pscand_en = 0
                            tapaction.pscand_pins = ""
                            self.assertEqual(tapaction.get_pscand_params(), (1, ['X', 'F'], ['1', '1']))

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            with patch('htd_tap_action.TAP.noa_offset_mode_needed', return_value=1):
                with patch('htd_tap_action.TAP.get_noa_offset_pins_and_delay', return_value=(['L', 'X', 'J', 'F'], ['1', '2'])):
                    with patch('htd_tap_action.TAP.get_pscan_type', return_value=("core", "core_slices")):
                        with patch('htd_tap_action.TAP.get_slices_list', return_value=[1, 3, 5, 6]):
                            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                            tapaction.pscand_en = 0
                            tapaction.pscand_pins = ""
                            with self.assertRaises(SystemExit) as cm:
                                with CaptureStdoutLog() as log:
                                    tapaction.get_pscand_params()
                            self.assertIn("Noaoffsets list length is not the same as the length of the noa pins list", log.getvalue())
#                            self.assertEqual(tapaction.get_pscand_params(), (1, ['X', 'F'], ['1', '1']))

#    @patch('htd_arguments_container.htd_argument_containter.get_argument')
#    @patch('htd_arguments_container.htd_argument_containter.get_not_declared_arguments')
    @patch('htd_patmod_manager.HtdPatmodManager.global_patmods_enabled', return_Value=True)
    def test_get_patmods_for_register_field(self, mock_patmod):  # , mock_xargs, mock_args):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.patmod_en = 0
            tapaction.arguments.arg_l = Mock()
            tapaction.arguments.arg_l = {'patmod_en': {'assigned': 0, 'declared': 1, 'default': 1, 'obligatory': 0, 'type': 'int'},
                                         'patmod_vars': {'assigned': 0, 'declared': 1, 'default': '', 'obligatory': 0, 'type': 'string_or_list'},
                                         'field1': {'assigned': 0, 'declared': 0, 'obligatory': 0, 'type': 'bool',
                                                    'val': {'patmod_var': None,
                                                                   'patmod_en': 0

                                                            }
                                                    },
                                         }
            # testcase1
            self.assertEqual(tapaction.get_patmods_for_register_field("aaa", True, True), [])

            # testcase2
            tapaction.patmod_en = 1
            self.assertEqual(tapaction.get_patmods_for_register_field("aaa", True, True), [])

#            #testcase3
##            mock_args.return_value = args
#            tapaction.patmod_vars = []
#            self.assertEqual(tapaction.get_patmods_for_register_field("field1", True, True), [])

    @patch("dts_spf_tap_info.dts_spf_tap_info.get_field_lsb", return_value=3)
    @patch("dts_spf_tap_info.dts_spf_tap_info.get_field_msb", return_value=6)
    @patch('htd_logger.Logger.error')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value="name1")
    @patch("htd_patmod_manager.HtdPatmodManager.get_patmods_for_register")
    @patch("htd_patmod_manager.HtdPatmodManager.global_patmods_enabled", return_Value=True)
    def test_get_patmods_for_register(self, mock_patmod_enabled, mock_patmod_register, mock_action, mock_error, mock_msb, mock_lsb):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            # testcase1
            tapaction.patmod_en = 0
            tapaction.patmod_vars = "var1"
            tapaction.agent = "agent1"
            tapaction.irname = "ir1"
            patmod1 = {"name": "patmodname",
                       "reg_field": "patmodregfield",
                       "field": "",
                       "bits": "5:3,8:4,7:2",
                       "value": "",
                       "type": "",
                       "label": ""}
            mock_patmod_register.return_value = [patmod1]
            self.assertEqual(tapaction.get_patmods_for_register(False, False), [])

            mock_error.reset_mock()
            mock_patmod_register.reset_mock()
            mock_patmod_enabled.reset_mock()

            # testcase2
            tapaction.patmod_en = 1
            mock_patmod_register.return_value = [patmod1]
            tapaction.get_patmods_for_register(False, False)
            mock_error.assert_called_with("Bits 4, 5, 3, 4, 5, 6, 7 found in multiple patmods. Pleas use patmod_var action param to  specify which variables to use")

            mock_error.reset_mock()
            mock_patmod_register.reset_mock()
            patmod1 = {"name": "patmodname",
                       "reg_field": "patmodregfield",
                       "field": "",
                       "bits": "4:2,8:5",
                       "value": "",
                       "type": "",
                       "label": ""}
            mock_patmod_register.return_value = [patmod1]
            expected_res = [{'name': 'patmodname', 'bits': '4:2,8:5', 'value': '', 'label': '', 'field': 'DR',
                             'reg_field': 'patmodregfield', 'type': ''}]
            self.assertEqual(tapaction.get_patmods_for_register(False, False), expected_res)

            # testcase3
            mock_error.reset_mock()
            mock_patmod_register.reset_mock()
            patmod1 = {"name": "patmodname",
                       "reg_field": "patmodregfield",
                       "field": "IR",
                       "bits": "4:2,8:5",
                       "value": "",
                       "type": "",
                       "label": ""}
            mock_patmod_register.return_value = [patmod1]
            expected_res = [{'name': 'patmodname', 'bits': '6:3', 'value': '', 'label': '', 'field': 'DR',
                             'reg_field': 'patmodregfield', 'type': ''}]
            self.assertEqual(tapaction.get_patmods_for_register(False, False), expected_res)

    @patch('htd_player_ui.htd_player_ui.tap_compression_on')
    @patch('htd_player_ui.htd_player_ui.tap_compression_off')
    @patch('htd_player_ui.htd_player_ui.tap_expandata')
    @patch('htd_tap_action.TAP.send_cmd')
    @patch('htd_logger.Logger.inform')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=3)
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value="file1")
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value="name1")
    @patch('htd_basic_action.htd_base_action.get_action_type', return_value="type1")
    def test_run(self, mock_type, mock_name, mock_file, mock_value, mock_logger, mock_send, mock_expand, mock_off, mock_on):
        # compression on, expandata < 1
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.arguments.arg_l = Mock()
            tapaction.arguments.arg_l = {'patmod_en': {'assigned': 0, 'declared': 1, 'description': 'Enable/Disable patmod support on this action', 'default': 1, 'obligatory': 0, 'type': 'int'},
                                         'patmod_vars': {'assigned': 0, 'declared': 1, 'description': 'Specify which patmod vars to use for this action', 'default': '', 'obligatory': 0, 'type': 'string_or_list'},
                                         'expandata': {'assigned': 0, 'declared': 1, 'description': 'Slow TCLK for this instruction by this multiplier', 'default': -1, 'obligatory': 0, 'type': 'int'},
                                         'compression': {'assigned': 0, 'declared': 1, 'description': 'Compression On/Off ', 'default': 0, 'obligatory': 0, 'type': 'bool'},
                                         'read_type': {'assigned': 0, 'declared': 1, 'description': 'Select readback mode on external DUT pins for current action functionality', 'default': 0, 'obligatory': 0, 'type': 'bool'}
                                         }
            tapaction.run()
            mock_off.assert_called_once_with()
            mock_on.assert_called_once_with()
            mock_send.assert_called_once_with(0)

        mock_off.reset_mock()
        mock_on.reset_mock()
        mock_send.reset_mock()

        # compression off, expandata > 1
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.arguments.arg_l = Mock()
            tapaction.arguments.arg_l = {'patmod_en': {'assigned': 0, 'declared': 1, 'description': 'Enable/Disable patmod support on this action', 'default': 1, 'obligatory': 0, 'type': 'int'},
                                         'patmod_vars': {'assigned': 0, 'declared': 1, 'description': 'Specify which patmod vars to use for this action', 'default': '', 'obligatory': 0, 'type': 'string_or_list'},
                                         'expandata': {'assigned': 0, 'declared': 1, 'description': 'Slow TCLK for this instruction by this multiplier', 'default': 2, 'obligatory': 0, 'type': 'int'},
                                         'compression': {'assigned': 0, 'declared': 1, 'description': 'Compression On/Off ', 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'read_type': {'assigned': 0, 'declared': 1, 'description': 'Select readback mode on external DUT pins for current action functionality', 'default': 0, 'obligatory': 0, 'type': 'bool'}
                                         }
            tapaction.run()
            mock_send.assert_called_once_with(0)
            mock_expand.assert_called_with("xxTCK", 1)
            mock_off.assert_not_called_with()
            mock_on.assert_not_called_with()

        mock_off.reset_mock()
        mock_on.reset_mock()
        mock_send.reset_mock()
        mock_expand.reset_mock()

        # compression off, expandata > 1, TCKPin define in CFG, patmod_vars is not str/unicode
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "",
                                                               "tap_mode": "taplink",
                                                               "TCKPin": "TCK"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            tapaction.arguments.arg_l = Mock()
            tapaction.arguments.arg_l = {'patmod_en': {'assigned': 0, 'declared': 1, 'description': 'Enable/Disable patmod support on this action', 'default': 1, 'obligatory': 0, 'type': 'int'},
                                         'patmod_vars': {'assigned': 0, 'declared': 1, 'description': 'Specify which patmod vars to use for this action', 'default': 1, 'obligatory': 0, 'type': 'string_or_list'},
                                         'expandata': {'assigned': 0, 'declared': 1, 'description': 'Slow TCLK for this instruction by this multiplier', 'default': 2, 'obligatory': 0, 'type': 'int'},
                                         'compression': {'assigned': 0, 'declared': 1, 'description': 'Compression On/Off ', 'default': 1, 'obligatory': 0, 'type': 'bool'},
                                         'read_type': {'assigned': 0, 'declared': 1, 'description': 'Select readback mode on external DUT pins for current action functionality', 'default': 0, 'obligatory': 0, 'type': 'bool'}
                                         }
            tapaction.run()
            mock_send.assert_called_once_with(0)
            mock_expand.assert_any_call("TCK", 2)
            mock_expand.assert_any_call("TCK", 1)
            mock_off.assert_not_called_with()
            mock_on.assert_not_called_with()

    @patch('htd_logger.Logger.inform')
    @patch("htd_tap_action.TAP.send_cmd")
    def test_debug_readback(self, mock_cmd, mock_logger):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            with patch('htd_arguments_container.htd_argument_containter.get_argument', return_value=True):
                tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                tapaction.debug_readback()
                mock_logger.assert_not_called_with("         Running Debug ReadBack")
                mock_cmd.assert_not_called_with(1)

        mock_logger.reset_mock()
        mock_cmd.reset_mock()

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            with patch('htd_arguments_container.htd_argument_containter.get_argument', return_value=False):
                tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                tapaction.debug_readback()
                mock_logger.assert_called_once_with(" [test_action:test_file:0]          Running Debug ReadBack TAP::test_action:test_file:0 \n\n")
                mock_cmd.assert_called_once_with(1)
#

    def test_get_defined_label(self):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            with patch('htd_basic_action.htd_base_action.get_action_name', return_value="AAAA"):
                with patch("htd_basic_action.htd_base_action.get_curr_flow") as mock_actionname:
                    mock_actionname().phase_name = "DDDD"  # mock_actionname.phase_name = "aaa" returns MagicMock object
                    tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                    tapaction.agent = "BBBB"
                    tapaction.irname = "CCCC"
                    tapaction.drsize = 6
                    self.assertEqual(tapaction.get_defined_label(), "AAAA__BBBB__CCCC__0__5__PhaseDDDD")

    def test_get_slices_list(self):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            with patch('htd_logger.Logger.error') as mock_error:
                tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                tapaction.get_slices_list("sliceA", 0)
                mock_error.assert_called_once_with("failed to obtain the slices to use")

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"},
                                                       "SliceInfo": {"sliceA": "1,3,2,4"}}):
            tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
            res = tapaction.get_slices_list("sliceA", 1)
            self.assertEqual(res, [1, 3, 2, 4])

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"NEW_LABEL_SPEC": "", "tap_mode": "taplink"}}):
            with patch('os.environ', return_value="abc"):
                # TODO:ynga how to mock util_get_slices_list
                tapaction = TAP(self.actionname, self.sourcefile, self.sourcelineno, self.currentflow, self.is_internal)
                res = tapaction.get_slices_list("sliceA", 1)
                self.assertEqual(res, [0])


if __name__ == '__main__':
    unittest.main()
