from htd_utilities import *
from htd_collaterals import *
import re
from htd_unix_socket import *
from htd_hpl_itpp_interface import *
from htd_hpl_spf_interface import *
import time

# -----------------------------------------------------------------------------------------------------------------
# Anonymous handler redirect the all "unknown" method to decoder.write, while stream is defined as a socket handler
# Server response expected on dual way:1- immediate : "OK" and second with timeout of 7days
# -----------------------------------------------------------------------------------------------------------------


class hpl_interactive_socket_interface(hpl_itpp_interface):
    def __init__(self, uiptr):

        # open the stream log and the socket
        self.streamLog = open("itpp_streamlog.itpp", "w", 1)
        self.socket = htd_unix_socket_client(
            CFG["HPL"]["socket_interface_delay"] if ("socket_interface_delay" in list(CFG["HPL"].keys())) else 12,
            self.streamLog, True)
        hpl_itpp_interface.__init__(self, "", uiptr, self.socket)
        self.uiptr = uiptr
        htdte_logger.enforce_interface_print_only()
    # ------------------------------
    # The all API is inherited from ITPP
    # ------------------------------
   # ------------------------------------------------------------------------------------------------------------------------------------

    def execute_command(self, msg, err_suppress=False):
        res = self.logStream.write(msg)
        if (self.silent_mode):
            return "1"
        if (self.interface_debug_mode):
            htdte_logger.inform(("HPL Interface debug command: %s") % (msg))
            htdte_logger.inform(("HPL Interface debug result: %s") % (res))
        if (not re.search("|", res)):
            htdte_logger.error(
                'Improper message format received from DPI : expected <status>|<value>, while received - \"%s\" ' % (
                    res))
        # remove spaces that might have been returned
        res = res.replace(" ", "")
        status = res.split("|")
        if (len(status) > 1 and status[0] == "FAIL"):
            if (not err_suppress):
                htdte_logger.error(("DPI indicate internal fail during executing:%s:%s") % (msg, status))
            else:
                return "0"
        if (len(status) > 1):
            return status[1]
        else:
            return status
   # ------------------------------------------------------------------------------------------------------------------------------------

    def close(self):
        try:
            print('Sending HTD_CLOSE_SERVER message..\n')
            self.socket.socketHandler.send("HTD_CLOSE_SERVER")
        except socket.error:  # in case there's an error with sending the message
            print('Send failed while closing hpl_interactive_socket_interface')
            htdte_logger.error('Send failed while closing hpl_interactive_socket_interface ')
        try:
            self.socket.socketHandler.close()
        except NameError:
            pass
        self.streamLog.close()
        return

   # ------------------------------------------------------------------------------------------------------------------------------------
    def get_model_time(self):
        return float(self.execute_command("rem: model_time \n").replace(" ", "").replace("(", "").replace(")", ""))
   # ------------------------------------------------------------------------------------------------------------------------------------

    def signal_exists(self, full_path):
        res = self.execute_command(("rem:  check_signal  %s\n") % (full_path))
        if (res == "null handle" or res == "0"):
            return 0
        return 1
   # ------------------------------------------------------------------------------------------------------------------------------------

    def signal_peek(self, full_path, value=-1):
        if(value < 0):
            return util_get_int_value(self.execute_command(("rem: peek_signal %s \n") % (full_path)))[1]
        else:
            if(util_get_int_value(self.execute_command(("rem: peek_signal %s \n") % (full_path)))[1] != value):
                htdte_logger.error(('Signal check failure - %s expected 0x%x, actual 0x%x  ') % (full_path, value, util_get_int_value(self.execute_command(("rem: peek_signal %s \n") % (full_path)))[1]))

   # ------------------------------------------------------------------------------------------------------------------------------------
    def signal_peek_str(self, full_path, value):
        return_value = self.execute_command(("rem: peek_signal %s \n") % (full_path))
        if (return_value != value):
            htdte_logger.error(('Signal check failure - %s expected %s, actual %s  ') % (full_path, value, return_value))

    def error(self, message):
        self.execute_command(("rem: error %s\n") % (message))
        time.sleep(5)
   # ------------------------------------------------------------------------------------------------------------------------------------

    def wait_tick(self):
        # FIXME:bring me back
        self.logStream.write(("rem:   wait 1;\n"))
        return
   # -------------------

    def train_tick_time(self):
        t1 = self.get_model_time()
        # identify if SYS_CLK is its the fastest clock to get real tick in model from Shareek/Kasem - one tick step @SYS_CLK???? (wait 1tick)
        t2 = self.get_model_time()
        return t2 - t1  # convert to string with scale ps /ns
        # 1.t1=get_time()
        # 2.one tick
        # 3.t2=get_time()
        # Return t2-t1
        # TODO: VIk has alraedy moved this to CLock class.
   # ------------------------------------------------------------------------------------------------------------------------------------

    def train_clock(self, clock_name):
        if(clock_name not in self.uiptr.hplClockMgr.get_all_clocks()):
            htdte_logger.error(('Illegal clock name - %s, Available clocks are : %s ') % (str(self.uiptr.hplClockMgr.get_all_clocks())))
        self.train_tick_time()
        clk_path = self.uiptr.hplClockMgr.get_clock_rtl_path(clock_name)
        # while (self.signal_peek(clk_path)!=0): step @SYS_CLK????
        # while (self.signal_peek(clk_path)!=1): step @SYS_CLK????
        t1 = self.get_model_time()  # Rising edge
        # while (self.signal_peek(clk_path)!=0): step @SYS_CLK????
        # while (self.signal_peek(clk_path)!=1): step @SYS_CLK????
        t2 = self.get_model_time()
        self.uiptr.hplClockMgr.set_clock_rate(clock_name, (t2 - t1) // self.time_scale)
   # ------------------------------------------------------------------------------------------------------------------------------------

    def train_clocks(self):
        clocks_l = self.uiptr.hplClockMgr.get_all_clocks()
        for clk in clocks_l:
            self.uiptr.hplClockMgr.train_clock(clk)
   # ------------------------------------------------------------------------------------------------------------------------------------

    def check_signal(self, full_path, value):
        if (isinstance(value, int)):
            return (self.signal_peek(full_path) == value)
        else:
            return (self.signal_peek_str(full_path) == value)
   # ------------------------------------------------------------------------------------------------------------------------------------
   # ------------------------------------------------------------------------------------------------------------------------------------

    def check_signal_not(self, full_path, value):
        return (self.signal_peek_not(full_path) == value)
