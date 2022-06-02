#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -B
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

from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
from htd_arguments_container import *
from htd_signal_action import *

from utils.files import TempDir
from utils.mock import patch, Mock, MagicMock
#from utils.ut import TestCase, unittest
from utils.helperclass import CaptureStdoutLog


class TestHtdSignalAction(unittest.TestCase):

    def setUp(self):
        self.mock_lsb_msb = htd_action_argument_entry(argvalue=-1, src="", lsb=-1, msb=-1, strobe=-1, label=-1, capture=-1, mask=-1, read_val=-1, zmode=-1, xmode=-1, access_type=HTD_VALUE_DEFAULT_ACCESS, verify_arg=1, patmod_en=1, patmod_var=None)
        self.SIG = SIG('action_name', 'source_file', 1, 'currentFlow', 'is_internal')

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
        self.SIG.arguments.arg_l = {}
        self.SIG.__init__('action_name', 'source_file', 1, 'currentFlow', 'is_internal')
        self.assertEqual(self.SIG.arguments.arg_l['op']['description'], ("Signal action type.Supported types are: %s..") % (self.SIG.signal_action_types))
        self.assertEqual(self.SIG.arguments.arg_l['sel']['description'], 'Used as a wildcard in regexp to filter in actual signals from multiple module matching	')
        self.assertEqual(self.SIG.arguments.arg_l['postdelay']['src'], 'SIG action restriction')
        self.assertEqual(self.SIG.arguments.arg_l['postalignment']['src'], 'SIG action restriction')

    def test_arguments_override(self):
        self.SIG.arguments_override()
        self.assertEqual(self.SIG.arguments.arg_l['postdelay']['src'], 'SIG action restriction')
        self.assertEqual(self.SIG.arguments.arg_l['postalignment']['src'], 'SIG action restriction')

    def test_get_action_not_declared_argument_names(self):
        # function not running anything
        self.SIG.get_action_not_declared_argument_names()

    @patch('htd_arguments_container.htd_argument_containter.declare_arg')
    @patch('htd_basic_action.htd_base_action.get_not_declared_arguments', return_value=['mock_value1', 'mock_value2'])
    @patch('htd_signal_info.htd_signal_info.extract_full_signal_path', return_value=['mock_value1', 'mock_value2'])
    def test_verify_arguments(self, mock_signal_path, mock_get_not_declared_arguments, mock_declare_arg):
        with patch('htd_signal_action.SIG.get_action_argument', return_value='SERIALSET'):
            self.SIG.dummy_mode = 1
            self.SIG.verify_arguments()
            mock_declare_arg.assert_called_with("width", "Serial sequece set length..", "int", 0, 1)
            mock_get_not_declared_arguments.assert_not_called()
        self.SIG.dummy_mode = 0
        with patch('htd_hpl_signal_manager.hpl_SignalManager_non_interactive.signal_exists', return_value=False):
            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    self.SIG.verify_arguments()
            self.assertIn('       Verification fail (one or more signals are not exists on current DUT model.', log.getvalue())

        with patch('htd_hpl_signal_manager.hpl_SignalManager_non_interactive.signal_exists', return_value=True),\
                patch('htd_signal_action.SIG.get_action_argument', return_value='SERIALSET'),\
                patch('htd_basic_action.htd_base_action.error') as mock_error:
            self.SIG.verify_arguments()
            assert mock_error.called == False

    def test_run(self):
        with patch('htd_signal_action.SIG.get_action_argument', return_value='START_MONITOR'):
            self.SIG.run()

        with patch('htd_signal_action.SIG.get_action_argument', return_value='STOP_MONITOR'):
            self.SIG.run()

        # TODO:code bug, not enough string arg
        # with patch('htd_signal_action.SIG.get_action_argument',return_value= 'test_raise_error'),\
        #      patch('htd_signal_action.SIG.get_action_argument',return_value= 'test_error_argument'):
        #     with self.assertRaises(SystemExit) as cm:
        #         with CaptureStdoutLog() as log:
        #             self.SIG.run()
        #     self.assertIn('Action\'s (action_name) illegal/unsupported SIGNAL opcode - "op"="test_error_argument" foun',log.getvalue())

        '''
        test WAIT op
        '''
        with patch('htd_basic_action.htd_base_action.get_not_declared_arguments', return_value=['postalignment', 'postalignment']),\
                patch('htd_hpl_signal_manager.hpl_SignalManager.signalset_wait') as mock_set_wait:
            self.SIG.arguments.arg_l = {
                'op': {'assigned': 0, 'declared': 1, 'description': "Signal action type.Supported types are: ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']..", 'default': 'WAIT', 'obligatory': 1, 'type': ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']},
                'postalignment': {'assigned': 1, 'declared': 0, 'description': 'Enable/Disable Post action run sync to modulo clocks (like SAL) ..', 'val': [self.mock_lsb_msb], 'src': 'SIG action restriction', 'default': 1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
                'waitcycles': {'assigned': 0, 'declared': 1, 'description': 'Define action verification range (error asserted if range exceed) or waiting cycles number.', 'default': 100, 'obligatory': 0, 'type': 'int'},
                'maxtimeout': {'assigned': 0, 'declared': 1, 'description': 'Define action simulation FATAL error timeout.', 'default': -1, 'obligatory': 0, 'type': 'int'},
                'refclock': {'assigned': 0, 'declared': 1, 'description': 'Define action verification clock resolution (accuracy)  .', 'default': 'bclk', 'obligatory': 0, 'type': 'string'},
                'sel': {'assigned': 0, 'declared': 1, 'description': 'Used as a wildcard in regexp to filter in actual signals from multiple module matching\t', 'default': '', 'obligatory': 0, 'type': 'string'},
                'peeksignal_disable': {'assigned': 0, 'declared': 1, 'description': 'Disable peek_signal printout', 'val': 0, 'src': 'SIG action restriction', 'default': 0, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
            }
            self.SIG.run()
            mock_set_wait.assert_called_with({'postalignment': {-1: {-1: -1}}}, 100, -1, 'bclk', 1, '', peeksignal_disable=0)

        '''
        test SERIALSET op
        '''
        with patch('htd_basic_action.htd_base_action.get_not_declared_arguments', return_value=['postalignment', 'postalignment']),\
                patch('htd_hpl_signal_manager.hpl_SignalManager.signalset_serial_set') as mock_set_serial_set:
            self.SIG.arguments.arg_l = {
                'op': {'assigned': 0, 'declared': 1, 'description': "Signal action type.Supported types are: ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']..", 'default': 'SERIALSET', 'obligatory': 1, 'type': ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']},
                'postalignment': {'assigned': 1, 'declared': 0, 'description': 'Enable/Disable Post action run sync to modulo clocks (like SAL) ..', 'val': [self.mock_lsb_msb], 'src': 'SIG action restriction', 'default': 1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
                'sel': {'assigned': 0, 'declared': 1, 'description': 'Used as a wildcard in regexp to filter in actual signals from multiple module matching\t', 'default': '', 'obligatory': 0, 'type': 'string'},
                'width': {'assigned': 0, 'declared': 1, 'description': 'unittest', 'default': 100, 'obligatory': 0, 'type': 'int'}
            }
            self.SIG.run()
            mock_set_serial_set.assert_called_with({'postalignment': {-1: {-1: -1}}}, 100, '')
            self.SIG.arguments.arg_l = {
                'op': {'assigned': 0, 'declared': 1, 'description': "Signal action type.Supported types are: ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']..", 'default': 'SERIALSET', 'obligatory': 1, 'type': ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']},
                'postalignment': {'assigned': 1, 'declared': 0, 'description': 'Enable/Disable Post action run sync to modulo clocks (like SAL) ..', 'val': [self.mock_lsb_msb], 'src': 'SIG action restriction', 'default': 1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
                'sel': {'assigned': 0, 'declared': 1, 'description': 'Used as a wildcard in regexp to filter in actual signals from multiple module matching\t', 'default': '', 'obligatory': 0, 'type': 'string'},
            }
            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    self.SIG.run()
            self.assertIn("Action's (action_name) missing obligatory argument - \"width\" for \"op\"=SERIALSET", log.getvalue())

        '''
        test PULSE op
        '''
        with patch('htd_basic_action.htd_base_action.get_not_declared_arguments', return_value=['postalignment', 'postalignment']),\
                patch('htd_hpl_signal_manager.hpl_SignalManager.signalset_pulse') as mock_set_pulse:
            self.SIG.arguments.arg_l = {
                'op': {'assigned': 0, 'declared': 1, 'description': "Signal action type.Supported types are: ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']..", 'default': 'PULSE', 'obligatory': 1, 'type': ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']},
                'postalignment': {'assigned': 1, 'declared': 0, 'description': 'Enable/Disable Post action run sync to modulo clocks (like SAL) ..', 'val': [self.mock_lsb_msb], 'src': 'SIG action restriction', 'default': 1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
                'waitcycles': {'assigned': 0, 'declared': 1, 'description': 'Define action verification range (error asserted if range exceed) or waiting cycles number.', 'default': 100, 'obligatory': 0, 'type': 'int'},
                'refclock': {'assigned': 0, 'declared': 1, 'description': 'Define action verification clock resolution (accuracy)  .', 'default': 'bclk', 'obligatory': 0, 'type': 'string'},
                'sel': {'assigned': 0, 'declared': 1, 'description': 'Used as a wildcard in regexp to filter in actual signals from multiple module matching\t', 'default': '', 'obligatory': 0, 'type': 'string'}
            }
            self.SIG.run()
            mock_set_pulse.assert_called_with({'postalignment': {-1: {-1: -1}}}, 100, 'bclk', '')

        '''
        test CHECK op
        '''
        with patch('htd_basic_action.htd_base_action.get_not_declared_arguments', return_value=['postalignment']):
            htdPlayer.hplSignalMgr.signal_check = Mock()
            htdPlayer.hplSignalMgr.signal_check.side_effect = [1, 0]
            self.SIG.arguments.arg_l = {
                'op': {'assigned': 0, 'declared': 1, 'description': "Signal action type.Supported types are: ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']..", 'default': 'CHECK', 'obligatory': 1, 'type': ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']},
                'postalignment': {'assigned': 1, 'declared': 0, 'description': 'Enable/Disable Post action run sync to modulo clocks (like SAL) ..', 'val': [self.mock_lsb_msb], 'src': 'SIG action restriction', 'default': 1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
                'check': {'assigned': 0, 'declared': 1, 'description': 'Enable/Disable checkers on current action..', 'default': 1, 'obligatory': 0, 'type': 'bool'},
                'sel': {'assigned': 0, 'declared': 1, 'description': 'Used as a wildcard in regexp to filter in actual signals from multiple module matching\t', 'default': '', 'obligatory': 0, 'type': 'string'}
            }
            self.SIG.run()
            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    self.SIG.run()
            self.assertIn("Action's (action_name) fail signal check: postalignment", log.getvalue())

        '''
        test CHECKNOT op
        '''
        # TODO:code bug, not enough string arg
        # with patch('htd_basic_action.htd_base_action.get_not_declared_arguments',return_value=['postalignment']):
        #     htdPlayer.hplSignalMgr.signal_check_not = Mock()
        #     htdPlayer.hplSignalMgr.signal_check_not.side_effect = [1,0]
        #     self.SIG.arguments.arg_l = {
        #     'op': {'assigned': 0, 'declared': 1, 'description': "Signal action type.Supported types are: ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']..", 'default': 'CHECKNOT', 'obligatory': 1, 'type': ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']},
        #     'postalignment': {'assigned': 1, 'declared': 0, 'description': 'Enable/Disable Post action run sync to modulo clocks (like SAL) ..', 'val': [self.mock_lsb_msb], 'src': 'SIG action restriction', 'default': 1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
        #     'check': {'assigned': 0, 'declared': 1, 'description': 'Enable/Disable checkers on current action..', 'default': 0, 'obligatory': 0, 'type': 'bool'},
        #     'sel': {'assigned': 0, 'declared': 1, 'description': 'Used as a wildcard in regexp to filter in actual signals from multiple module matching\t', 'default': '', 'obligatory': 0, 'type': 'string'}
        #      }
        #     self.SIG.run()
        #     with self.assertRaises(SystemExit) as cm:
        #         with CaptureStdoutLog() as log:
        #             self.SIG.run()
        #     self.assertIn("Action's (action_name) fail signal check: postalignment!= ",log.getvalue())

        '''
        test GET op
        '''
        with patch('htd_basic_action.htd_base_action.get_not_declared_arguments', return_value={}),\
                patch('htd_hpl_signal_manager.hpl_SignalManager_non_interactive.signal_peek') as mock_signal_peek:
            self.SIG.arguments.arg_l = {
                'op': {'assigned': 0, 'declared': 1, 'description': "Signal action type.Supported types are: ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']..", 'default': 'GET', 'obligatory': 1, 'type': ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']},
                'postalignment': {'assigned': 1, 'declared': 0, 'description': 'Enable/Disable Post action run sync to modulo clocks (like SAL) ..', 'val': [self.mock_lsb_msb], 'src': 'SIG action restriction', 'default': 1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
                'sel': {'assigned': 0, 'declared': 1, 'description': 'Used as a wildcard in regexp to filter in actual signals from multiple module matching\t', 'default': '', 'obligatory': 0, 'type': 'string'}
            }
            self.SIG.run()

        with patch('htd_basic_action.htd_base_action.get_not_declared_arguments', return_value=['postalignment']),\
                patch('htd_hpl_signal_manager.hpl_SignalManager_non_interactive.signal_peek') as mock_signal_peek:
            self.SIG.arguments.arg_l = {
                'op': {'assigned': 0, 'declared': 1, 'description': "Signal action type.Supported types are: ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']..", 'default': 'GET', 'obligatory': 1, 'type': ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']},
                'postalignment': {'assigned': 1, 'declared': 0, 'description': 'Enable/Disable Post action run sync to modulo clocks (like SAL) ..', 'val': [], 'src': 'SIG action restriction', 'default': 1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
                'sel': {'assigned': 0, 'declared': 1, 'description': 'Used as a wildcard in regexp to filter in actual signals from multiple module matching\t', 'default': '', 'obligatory': 0, 'type': 'string'}
            }
            self.SIG.run()

        with patch('htd_basic_action.htd_base_action.get_not_declared_arguments', return_value=['postalignment']),\
                patch('htd_hpl_signal_manager.hpl_SignalManager_non_interactive.signal_peek') as mock_signal_peek:
            self.SIG.arguments.arg_l = {
                'op': {'assigned': 0, 'declared': 1, 'description': "Signal action type.Supported types are: ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']..", 'default': 'GET', 'obligatory': 1, 'type': ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']},
                'postalignment': {'assigned': 1, 'declared': 0, 'description': 'Enable/Disable Post action run sync to modulo clocks (like SAL) ..', 'val': [self.mock_lsb_msb], 'src': 'SIG action restriction', 'default': 1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
                'sel': {'assigned': 0, 'declared': 1, 'description': 'Used as a wildcard in regexp to filter in actual signals from multiple module matching\t', 'default': '', 'obligatory': 0, 'type': 'string'}
            }
            self.SIG.run()
            mock_signal_peek.assert_called_with('postalignment', -1, -1, '')

        '''
        test SET op
        '''
        with patch('htd_basic_action.htd_base_action.get_not_declared_arguments', return_value=['postalignment', 'postalignment']),\
                patch('htd_hpl_signal_manager.hpl_SignalManager.signalset_set') as mock_set_set:
            self.SIG.arguments.arg_l = {
                'op': {'assigned': 0, 'declared': 1, 'description': "Signal action type.Supported types are: ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']..", 'default': 'SET', 'obligatory': 1, 'type': ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']},
                'postalignment': {'assigned': 1, 'declared': 0, 'description': 'Enable/Disable Post action run sync to modulo clocks (like SAL) ..', 'val': [self.mock_lsb_msb], 'src': 'SIG action restriction', 'default': 1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
                'sel': {'assigned': 0, 'declared': 1, 'description': 'Used as a wildcard in regexp to filter in actual signals from multiple module matching\t', 'default': '', 'obligatory': 0, 'type': 'string'}
            }
            self.SIG.run()
            mock_set_set.assert_called_with({'postalignment': {-1: {-1: -1}}}, '')

        '''
        test FORCE op
        '''
        with patch('htd_basic_action.htd_base_action.get_not_declared_arguments', return_value=['postalignment', 'postalignment']),\
                patch('htd_hpl_signal_manager.hpl_SignalManager.signalset_force') as mock_set_force:
            self.SIG.arguments.arg_l = {
                'op': {'assigned': 0, 'declared': 1, 'description': "Signal action type.Supported types are: ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']..", 'default': 'FORCE', 'obligatory': 1, 'type': ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']},
                'postalignment': {'assigned': 1, 'declared': 0, 'description': 'Enable/Disable Post action run sync to modulo clocks (like SAL) ..', 'val': [self.mock_lsb_msb], 'src': 'SIG action restriction', 'default': 1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
                'sel': {'assigned': 0, 'declared': 1, 'description': 'Used as a wildcard in regexp to filter in actual signals from multiple module matching\t', 'default': '', 'obligatory': 0, 'type': 'string'}
            }
            self.SIG.run()
            mock_set_force.assert_called_with({'postalignment': {-1: {-1: -1}}}, '')

        '''
        test UNFORCE op
        '''
        with patch('htd_basic_action.htd_base_action.get_not_declared_arguments', return_value=['postalignment', 'postalignment']),\
                patch('htd_hpl_signal_manager.hpl_SignalManager.signalset_unforce') as mock_set_unforce:
            self.SIG.arguments.arg_l = {
                'op': {'assigned': 0, 'declared': 1, 'description': "Signal action type.Supported types are: ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']..", 'default': 'UNFORCE', 'obligatory': 1, 'type': ['WAIT', 'SERIALSET', 'CHECK', 'CHECKNOT', 'PULSE', 'FORCE', 'UNFORCE', 'START_MONITOR', 'STOP_MONITOR', 'SET', 'GET']},
                'postalignment': {'assigned': 1, 'declared': 0, 'description': 'Enable/Disable Post action run sync to modulo clocks (like SAL) ..', 'val': [self.mock_lsb_msb], 'src': 'SIG action restriction', 'default': 1, 'obligatory': 0, 'ever_accessed': 0, 'type': 'bool'},
                'sel': {'assigned': 0, 'declared': 1, 'description': 'Used as a wildcard in regexp to filter in actual signals from multiple module matching\t', 'default': '', 'obligatory': 0, 'type': 'string'}
            }
            self.SIG.run()
            mock_set_unforce.assert_called_with({'postalignment': {-1: {-1: -1}}}, '')

    @patch('htd_signal_action.SIG.get_action_name', return_value='mock_action_name')
    @patch('htd_signal_action.SIG.get_action_argument', return_value='mock_action_argument')
    def test_get_defined_label(self, mock_get_action_argument, mock_get_action_name):
        self.assertEqual(self.SIG.get_defined_label(), "mock_action_name__mock_action_argument")


if __name__ == '__main__':
    unittest.main()
