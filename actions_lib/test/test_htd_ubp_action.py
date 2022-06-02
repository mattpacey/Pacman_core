#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -B
# import unittest
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

from htd_ubp_action import *
from utils.files import TempDir
from utils.mock import patch, Mock, MagicMock
#from utils.ut import TestCase, unittest


class TestHtdUbpAction(unittest.TestCase):

    def setUp(self):
        self.ubp_obj = UBP('test_action_name', 'test_source_file', 'test_source_lineno', 'test_currentFlow', 'test_is_internal')

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

    @patch("htd_ubp_action.UBP.error")
    def test_init(self, mock_error):
        # testing absense of HPL key in CFG
        self.assertEqual(self.ubp_obj.tap_protocol, 'taplink')  # default value is taplink
        temp = CFG['HPL']
        CFG.pop('HPL', None)
        self.ubp_obj.__init__('test_action_name', 'test_source_file', 'test_source_lineno', 'test_currentFlow', 'test_is_internal')
        self.assertEqual(self.ubp_obj.tap_protocol, '')  # no HPL defined
        CFG['HPL'] = temp
        self.ubp_obj.__init__('test_action_name', 'test_source_file', 'test_source_lineno', 'test_currentFlow', 'test_is_internal')
        self.assertEqual(self.ubp_obj.tap_protocol, 'taplink')  # default value is taplink

        temp = self.ubp_obj.tap_protocol
        CFG['TE'] = {'tap_mode': 'tapnetwork', 'inf_waitcycle_time': 1000}
        self.ubp_obj.__init__('test_action_name', 'test_source_file', 'test_source_lineno', 'test_currentFlow', 'test_is_internal')
        self.assertEqual(self.ubp_obj.tap_protocol, 'tapnetwork')  # tap_mode = tapnetwork

        CFG['TE']['tap_mode'] = 'invalid_tap'
        self.ubp_obj.__init__('test_action_name', 'test_source_file', 'test_source_lineno', 'test_currentFlow', 'test_is_internal')
        # tap_mode is NOT taplink or tapnetwork
        mock_error.assert_called_with('Action\'s (test_action_name) : Illegal TAP protocol type selection in CFG["TE"]["tap_mode"]: expected "tapnetwork" or "taplink" ,received - "invalid_tap" ', 1)

        # reset CFG['TE'] else some of the other functions will fail
        CFG['TE']['tap_mode'] = 'tapnetwork'

    def test_debug_readback(self):
        self.ubp_obj.debug_readback()
        # TODO: check if function can be removed as it does nothing

    def test_get_action_not_declared_argument_names(self):
        self.ubp_obj.get_action_not_declared_argument_names()
        # TODO: check if function can be removed as it does nothing

    def test_check_tap_var(self):
        self.assertIsNone(self.ubp_obj.check_tap_var())
        # TODO: check if code does anything, if(0) condition will never trigger

    @patch('htd_logger.Logger.error')
    @patch('htd_ubp_action.htdPlayer.hpl_to_dut_interface.add_comment')
    @patch("dts_spf_tap_info.dts_spf_tap_info.get_ir_fields")
    def test_send_tap_flow(self, mock_get_ir_fields, mock_add_comment, mock_error_logger):
        with patch("htd_basic_action.htd_base_action.get_curr_flow") as mock_get_curr_flow:
            # allow entry into matchObj if condition
            self.ubp_obj.fields = {'ir': 'ir0', 'check': 0, 'agent': 'agent0'}
            mock_get_ir_fields.return_value = {'ir': 'ir0', 'check': 0, 'agent': 'agent0'}
            self.ubp_obj.send_tap_flow()
            mock_add_comment.assert_any_call('Sending TAP ir: ')
            mock_add_comment.assert_any_call('Sending TAP agent: ')
            mock_get_curr_flow().exec_action.assert_called_with({'ir': 'ir0', 'parallel_mode': 1, 'check': '0', 'agent': 'agent0'}, 'TAP', 'UBP', 0, 'test_action_name')
            mock_add_comment.assert_called_with('Sending TAP field: agent with value = agent0')

            # multiple matchObj
            mock_add_comment.reset_mock()
            mock_get_curr_flow.reset_mock()
            mock_get_ir_fields.return_value = {'ir': 'ir', 'ir0': 'ir0'}
            self.ubp_obj.send_tap_flow()
            mock_add_comment.assert_not_called()
            mock_error_logger.assert_called_with('More that 1 hit for ir')
            mock_get_curr_flow().exec_action.assert_called_with({'ir': 'ir0', 'parallel_mode': 1, 'check': 0, 'agent': ''}, 'TAP', 'UBP', 0, 'test_action_name')

            # no matchObj
            mock_add_comment.reset_mock()
            mock_get_curr_flow.reset_mock()
            self.ubp_obj.fields = {'xir': 'xir0'}
            self.ubp_obj.send_tap_flow()
            mock_add_comment.assert_not_called()
            mock_error_logger.assert_not_called()
            mock_get_curr_flow().exec_action.assert_called_with({'ir': '', 'parallel_mode': 1, 'check': 0, 'agent': ''}, 'TAP', 'UBP', 0, 'test_action_name')

    @patch("dts_spf_tap_info.dts_spf_tap_info.get_ir_commands", return_value=('ip0', 'ip1', 'ip2', 'test_BRKPTCTL1'))
    def test_action_config(self, mock_get_ir_commands):
        self.ubp_obj.tap_cmds = []
        self.ubp_obj.ubp_action = 'TEST_UBP_ACTION'
        self.ubp_obj.Actions_Dictionary["TEST_UBP_ACTION"] = {'CONFIGURED': 0,
                                                              'ACTION': {'action': 'test_action',
                                                                         'action[2]': 'test_action',
                                                                         'trigger': 'test_action_trigger',
                                                                         'detect': 'test CO detect',
                                                                         'misc': 'test ACT misc.|_test'},
                                                              'IP': 'ip0,ip1,ip2,ip3',
                                                              'UBP': 'test_BRKPTCTL1',
                                                              'TRIGGER': {'trigger0': 'test_trigger0',
                                                                          'trigger1': 'test_trigger1'},
                                                              'REARM': 1,
                                                              'MBP_ACTION': 'MBP0'}
        self.ubp_obj.action_config()
        temp_output = [{'rmw': 1, 'fields': {'.*(ACT|CO).*[\\.|_]misc.*': 'test ACT misc.|_test', '.*(CO)?.*detect.*': 'test CO detect', '.*trigger0.*': 'test_trigger0', 'trigger': 'test_action_trigger', '.*ACTIONS.MBP|fabric_actions': 'MBP0', 'action': 4, '.*CONTROLLER_ARM.*': 2, '.*trigger1.*': 'test_trigger1'}, 'ir': 'test_BRKPTCTL1', 'manual': 1, 'bfm': 'tap', 'agent': 'ip0', 'check': 1}, {'rmw': 1, 'fields': {'.*(ACT|CO).*[\\.|_]misc.*': 'test ACT misc.|_test', '.*(CO)?.*detect.*': 'test CO detect', '.*trigger0.*': 'test_trigger0', 'trigger': 'test_action_trigger', '.*ACTIONS.MBP|fabric_actions': 'MBP0', 'action': 4, '.*CONTROLLER_ARM.*': 2, '.*trigger1.*': 'test_trigger1'}, 'ir': 'test_BRKPTCTL1', 'manual': 1, 'bfm': 'tap', 'agent': 'ip1', 'check': 1}, {'rmw': 1, 'fields': {'.*(ACT|CO).*[\\.|_]misc.*': 'test ACT misc.|_test', '.*(CO)?.*detect.*': 'test CO detect', '.*trigger0.*': 'test_trigger0', 'trigger': 'test_action_trigger', '.*ACTIONS.MBP|fabric_actions': 'MBP0', 'action': 4, '.*CONTROLLER_ARM.*': 2, '.*trigger1.*': 'test_trigger1'}, 'ir': 'test_BRKPTCTL1', 'manual': 1, 'bfm': 'tap', 'agent': 'ip2', 'check': 1}, {'rmw': 1, 'fields': {'.*(ACT|CO).*[\\.|_]misc.*': 'test ACT misc.|_test', '.*(CO)?.*detect.*': 'test CO detect', '.*trigger0.*': 'test_trigger0', 'trigger': 'test_action_trigger', '.*ACTIONS.MBP|fabric_actions': 'MBP0', 'action': 4, '.*CONTROLLER_ARM.*': 2, '.*trigger1.*': 'test_trigger1'}, 'ir': 'test_BRKPTCTL1', 'manual': 1, 'bfm': 'tap', 'agent': 'ip3', 'check': 1}]
        self.assertEqual(self.ubp_obj.tap_cmds, temp_output)

    @patch("dts_spf_tap_info.dts_spf_tap_info.get_ir_commands", return_value=('ip0', 'ip1', 'ip2'))
    def test_action_enable(self, mock_get_ir_commands):
        self.ubp_obj.tap_cmds = []
        self.ubp_obj.ubp_action = 'TEST_UBP_ACTION'
        self.ubp_obj.enable_action = 'TEST_UBP_ENABLE_ACTION'
        self.ubp_obj.Actions_Dictionary["TEST_UBP_ACTION"] = {'UBP': 'BRK CTL0',
                                                              'IP': 'ip0,ip1,ip2,ip3'}
        self.ubp_obj.action_enable()
        temp_list = [{'rmw': 1, 'fields': {'.*ENABLE.*|.*brk.*en.*': 'TEST_UBP_ENABLE_ACTION'}, 'ir': '', 'manual': 1, 'bfm': 'tap', 'agent': 'ip0', 'check': 1}, {'rmw': 1, 'fields': {'.*ENABLE.*|.*brk.*en.*': 'TEST_UBP_ENABLE_ACTION'}, 'ir': '', 'manual': 1, 'bfm': 'tap', 'agent': 'ip1', 'check': 1}, {'rmw': 1, 'fields': {'.*ENABLE.*|.*brk.*en.*': 'TEST_UBP_ENABLE_ACTION'}, 'ir': '', 'manual': 1, 'bfm': 'tap', 'agent': 'ip2', 'check': 1}, {'rmw': 1, 'fields': {'.*ENABLE.*|.*brk.*en.*': 'TEST_UBP_ENABLE_ACTION'}, 'ir': '', 'manual': 1, 'bfm': 'tap', 'agent': 'ip3', 'check': 1}]
        self.assertEqual(self.ubp_obj.tap_cmds, temp_list)

    @patch('htd_logger.Logger.error')
    def test_verify_ubp_action(self, mock_logger):
        self.ubp_obj.verify_ubp_action()
        mock_logger.assert_any_call('Missing tap sequence \"bit0\" index...')
        mock_logger.assert_any_call('UBP action not defined')

        # bypass both if conditions
        mock_logger.reset_mock()
        self.ubp_obj.Actions_Dictionary = {"test": "test_value"}
        self.ubp_obj.arguments.set_argument("Ubp_action", "test")
        self.assertIsNone(self.ubp_obj.verify_ubp_action())
        mock_logger.assert_not_called()

    @patch('htd_ubp_action.UBP.check_tap_var')
    @patch('htd_ubp_action.UBP.verify_ubp_action')
    @patch('htd_ubp_action.UBP.get_product_setup')
    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='test_action_type')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='test_action_name')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='test_action_file')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    def test_verify_arguments(self, mock_lineno, mock_file, mock_name, mock_type, mock_product, mock_verify, mock_tap_var):

        # no ir, reset=0, disable=0
        self.ubp_obj.verify_arguments()
        self.assertEqual(mock_verify.call_count, 1)

        # disable = 1
        mock_verify.reset_mock()
        self.ubp_obj.arguments.set_argument("disable", "1")
        self.ubp_obj.verify_arguments()
        self.assertEqual(mock_verify.call_count, 0)

        # ir = test_ir
        mock_verify.reset_mock()
        self.ubp_obj.arguments.set_argument("ir", "test_ir")
        self.ubp_obj.verify_arguments()
        self.assertEqual(mock_verify.call_count, 0)
        self.assertEqual(mock_tap_var.call_count, 1)
        # TODO: need to handle undeclared argument

    def test_verify_last_config(self):
        self.ubp_obj.verify_last_config()
        # TODO: function does nothing

    @patch('htd_ubp_action.UBP.send_tap_flow')
    def test_send_tap_array(self, mock_send_tap_flow):
        self.ubp_obj.tap_cmds = [{'ir': 'test_ir',
                                  'agent': 'test_agent',
                                  'check': 0,
                                  'rmw': 'r',
                                  'bfm': 'test_bfm',
                                  'fields': {'field0': 'testField0'}}]
        self.ubp_obj.send_tap_array()
        self.assertEqual(self.ubp_obj.ir_name, 'test_ir')
        self.assertEqual(self.ubp_obj.ir_agent, 'test_agent')
        self.assertEqual(self.ubp_obj.check, 0)
        self.assertEqual(self.ubp_obj.read_modify_write, 'r')
        self.assertEqual(self.ubp_obj.bfm_mode, 'test_bfm')
        self.assertDictEqual(self.ubp_obj.fields, {'field0': 'testField0'})
        self.assertEqual(mock_send_tap_flow.call_count, 1)

    @patch('htd_logger.Logger.error')
    def test_get_product_setup(self, mock_error):
        CFG['UBP_actions'] = {'test_action': {'IP': 'test_ip',
                                              'UBP': 'test_ubp',
                                              'TRIGGER': 'test_trigger',
                                              'ACTION': 'test_action',
                                              'REARM': 'test_rearm',
                                              'ALLOW_TOG': 'test_allow_tog'},
                              'test_action_0': {'IP': 'test_ip_0',
                                                'UBP': 'test_ubp_0',
                                                'TRIGGER': 'test_trigger_0:test_trigger_1',
                                                'ACTION': 'test_action_0:test_action_1',
                                                'REARM': 'test_rearm_0',
                                                'MBP_ACTION': 'test_mbp_action_0',
                                                'ALLOW_TOG': 'test_allow_tog_0'},
                              'test_action_1': {'IP': 'test_ip_0',
                                                'UBP': 'test_ubp_0',
                                                'TRIGGER': 'test_trigger_0:test_trigger_1,test_trigger_2:test_trigger_3',
                                                'ACTION': 'test_action_0:test_action_1,test_action_2:test_action_3',
                                                'REARM': 'test_rearm_0',
                                                'MBP_ACTION': 'test_mbp_action_0',
                                                'ALLOW_TOG': 'test_allow_tog_0'}}
        self.ubp_obj.Actions_Dictionary = {'test_action': {'IP': 'test_ip',
                                                           'UBP': 'test_ubp',
                                                           'TRIGGER_STR': 'test_trigger',
                                                           'ACTION_STR': 'test_action',
                                                           'REARM': 'test_rearm',
                                                           'ALLOW_TOG': 'test_allow_tog'}}
        self.ubp_obj.get_product_setup()
        self.assertDictEqual(self.ubp_obj.Actions_Dictionary['test_action'], {'UBP': 'test_ubp', 'REARM': 'test_rearm', 'IP': 'test_ip', 'TRIGGER_STR': 'test_trigger', 'ACTION_STR': 'test_action', 'ALLOW_TOG': 'test_allow_tog'})
        self.assertDictEqual(self.ubp_obj.Actions_Dictionary['test_action_0'], {'UBP': 'test_ubp_0', 'REARM': 'test_rearm_0', 'IP': 'test_ip_0', 'CONFIGURED': 0, 'ENABLED': 0, 'MBP_ACTION': 'test_mbp_action_0', 'ACTION': {'test_action_0': 'test_action_1'}, 'TRIGGER': {'test_trigger_0': 'test_trigger_1'}, 'TRIGGER_STR': 'test_trigger_0:test_trigger_1', 'ACTION_STR': 'test_action_0:test_action_1', 'ALLOW_TOG': 'test_allow_tog_0'})
        self.assertDictEqual(self.ubp_obj.Actions_Dictionary['test_action_1'], {'UBP': 'test_ubp_0', 'REARM': 'test_rearm_0', 'IP': 'test_ip_0', 'CONFIGURED': 0, 'ENABLED': 0, 'MBP_ACTION': 'test_mbp_action_0', 'ACTION': {'test_action_0': 'test_action_1', 'test_action_2': 'test_action_3'}, 'TRIGGER': {'test_trigger_2': 'test_trigger_3', 'test_trigger_0': 'test_trigger_1'}, 'TRIGGER_STR': 'test_trigger_0:test_trigger_1,test_trigger_2:test_trigger_3', 'ACTION_STR': 'test_action_0:test_action_1,test_action_2:test_action_3', 'ALLOW_TOG': 'test_allow_tog_0'})

        # trigger all errors
        self.ubp_obj.Actions_Dictionary['test_action']['IP'] = 'fail'
        self.ubp_obj.Actions_Dictionary['test_action']['UBP'] = 'fail'
        self.ubp_obj.Actions_Dictionary['test_action']['TRIGGER_STR'] = 'fail'
        self.ubp_obj.Actions_Dictionary['test_action']['ACTION_STR'] = 'fail'
        self.ubp_obj.Actions_Dictionary['test_action']['REARM'] = 'fail'
        self.ubp_obj.Actions_Dictionary['test_action']['ALLOW_TOG'] = 'fail'
        self.ubp_obj.get_product_setup()
        mock_error.assert_any_call('IP in this action diff from TE_CFG to pickle')
        mock_error.assert_any_call('UBP in this action diff from TE_CFG to pickle')
        mock_error.assert_any_call('TRIGGER in this action diff from TE_CFG to pickle')
        mock_error.assert_any_call('ACTION in this action diff from TE_CFG to pickle')
        mock_error.assert_any_call('REARM in this action diff from TE_CFG to pickle')
        mock_error.assert_any_call('Allow together in this action diff from TE_CFG to pickle')

    @patch('htd_ubp_action.htdPlayer.hpl_to_dut_interface.add_comment')
    def test_print_current_ubps(self, mock_add_comment):
        self.ubp_obj.Actions_Dictionary = {'test_action': {'IP': 'test_ip',
                                                           'UBP': 'test_ubp',
                                                           'TRIGGER': {0: 0, 1: 1},
                                                           'TRIGGER_STR': 'test_trigger',
                                                           'ACTION_STR': 'test_action',
                                                           'REARM': 'test_rearm',
                                                           'ALLOW_TOG': 'test_allow_tog',
                                                           'ENABLED': 1,
                                                           'CONFIGURED': 1}}
        self.ubp_obj.print_current_ubps()
        mock_add_comment.assert_any_call('|test_action              |test_ip             |test_ubp            |    1    |     1      |0                           =          0|')  # if first_trig
        mock_add_comment.assert_any_call('|                         |                    |                    |         |            |1                           =          1|')  # else after first_trig

    @patch("htd_ubp_action.UBP.action_config")
    @patch('htd_ubp_action.htdPlayer.hpl_to_dut_interface.add_comment')
    @patch("htd_ubp_action.UBP.print_current_ubps")
    @patch("htd_ubp_action.UBP.get_product_setup")
    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRun_InvalidOP')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    def test_run(self, mock_setup, mock_lineno, mock_file, mock_name, mock_type, mock_print, mock_comment, mock_action_config):
        self.ubp_obj.Actions_Dictionary = {'test_action': {'IP': 'test_ip',
                                                           'UBP': 'test_ubp',
                                                           'TRIGGER_STR': 'test_trigger',
                                                           'ACTION_STR': 'test_action',
                                                           'REARM': 'test_rearm',
                                                           'ALLOW_TOG': 'test_allow_tog',
                                                           'ENABLED': 1,
                                                           'CONFIGURED': 1,
                                                           'TRIGGER': 'test_trigger'}}
        self.ubp_obj.ubp_action = 'test_action'
        self.ubp_obj.run()
        self.assertEquals(mock_comment.call_count, 3)
        mock_comment.assert_any_call('UBP actions status at start of action')
        mock_comment.assert_any_call('uBP action already enabled: test_action')
        mock_comment.assert_any_call('UBP actions status at end of action')

        mock_comment.reset_mock()
        self.ubp_obj.Actions_Dictionary['test_action']['ENABLED'] = 0
        self.ubp_obj.run()
        self.assertEquals(mock_comment.call_count, 4)
        mock_comment.assert_any_call('UBP actions status at start of action')
        mock_comment.assert_any_call('uBP action already configured: test_action')
        mock_comment.assert_any_call('Enabling uBP action: test_action')
        mock_comment.assert_any_call('UBP actions status at end of action')

        self.ubp_obj.Actions_Dictionary['test_action_1'] = {'IP': 'test_ip',
                                                            'UBP': 'test_ubp',
                                                            'TRIGGER_STR': 'test_trigger',
                                                            'ACTION_STR': 'test_action',
                                                            'REARM': 'test_rearm',
                                                            'ALLOW_TOG': 'test_allow_tog',
                                                            'ENABLED': 1,
                                                            'CONFIGURED': 1,
                                                            'TRIGGER': 'test_trigger'}
        mock_comment.reset_mock()
        self.ubp_obj.Actions_Dictionary['test_action']['ENABLED'] = 0
        self.ubp_obj.run()
        self.assertEquals(mock_comment.call_count, 6)
        mock_comment.assert_any_call('UBP actions status at start of action')
        mock_comment.assert_any_call('Disabling uBP action because conflict with same MBP pin enabled: test_action_1')
        mock_comment.assert_any_call('Setting uBP action as de-configured because conflict with same UBP in use: test_action')
        mock_comment.assert_any_call('uBP action already configured: test_action')
        mock_comment.assert_any_call('Enabling uBP action: test_action')
        mock_comment.assert_any_call('UBP actions status at end of action')

        self.ubp_obj.Actions_Dictionary['test_action']['ENABLED'] = 0
        self.ubp_obj.Actions_Dictionary['test_action']['CONFIGURED'] = 0
        mock_comment.reset_mock()
        self.ubp_obj.run()
        self.assertEquals(mock_comment.call_count, 5)
        self.assertEquals(mock_action_config.call_count, 1)
        mock_comment.assert_any_call('UBP actions status at start of action')
        mock_comment.assert_any_call('Setting uBP action as de-configured because conflict with same UBP in use: test_action')
        mock_comment.assert_any_call('Configuring uBP action: test_action')
        mock_comment.assert_any_call('Enabling uBP action: test_action')
        mock_comment.assert_any_call('UBP actions status at end of action')

        self.ubp_obj.arguments.set_argument("disable", "1")
        self.ubp_obj.arguments.set_argument("Ubp_action", "test_action")
        mock_comment.reset_mock()
        self.ubp_obj.run()
        self.assertEquals(mock_comment.call_count, 3)
        mock_comment.assert_any_call('UBP actions status at start of action')
        mock_comment.assert_any_call('Disabling uBP action test_action')
        mock_comment.assert_any_call('UBP actions status at end of action')


if __name__ == '__main__':
    unittest.main()
