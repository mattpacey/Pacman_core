import socket
import sys
import re
import os
import subprocess
import random
import multiprocessing
import atexit
import signal
import os
from htd_logger import *
socket_in_progress = False
# ---create htdte_logger if not exists-----
try:
    htdte_logger.inform("Loading Socket Lib..")
except NameError:
    htdte_logger = Logger("htd_socket_lib.log")

clientProcess = None
# ------------------------------------


def signal_handler(signum, frame):
    killzombies()


def process_handler_execute_client_cmd():
    htdte_logger.inform((" Running CLIENT CMD: %s") % (os.environ["HTD_TE_CMD"]))
    status = subprocess.call(os.environ["HTD_TE_CMD"], shell=True)
    if (status):
        htdte_logger.error(' Client exited abnormally.')


def killzombies():
    if (clientProcess is not None and clientProcess.poll() is None):
        clientProcess.terminate()


class htd_unix_socket_server(object):
    def __init__(self, server_name, noclient_run=0, debug_mode=0):
        if ('HTD_SOCKET_FILE' not in list(os.environ.keys())):
            htdte_logger.error("Missing unix env[HTD_SOCKET_FILE] used for socket file name specification")
        htdte_logger.inform((" Opening HTD SERVER on file: %s") % (os.environ['HTD_SOCKET_FILE']))
        if ("HTD_TE_CMD" not in list(os.environ.keys()) and (not noclient_run)):
            htdte_logger.error(
                ' Missing HTD CLIENT CMD env["HTD_TE_CMD"] used by server to initiate a client process interactively.')
        if (not noclient_run):
            htdte_logger.inform((" HTD CLIENT CMD: %s") % (os.environ['HTD_TE_CMD']))
        # -----------------------------------------------
        self.socket_file = os.environ['HTD_SOCKET_FILE']
        self.server_name = server_name
        self.debug_mode = debug_mode
        self.clientSock = None
        self.clientCmd = os.environ["HTD_TE_CMD"] if (not noclient_run) else "None"
        # ----Executiong client-------------
        if (self.clientCmd != "None" and self.clientCmd != "none"):
            htdte_logger.inform((" Running CLIENT CMD: %s") % (self.clientCmd))
            p = multiprocessing.Process(target=process_handler_execute_client_cmd)
            p.start()
            clientProcess = p
        # ---------------------------------------------
        atexit.register(killzombies)
        # signal.signal(signal.SIG*, signal_handler)
        htdte_logger.inform(("Openning socket on %s...") % (self.socket_file))
        lockfile = ("%s_sboot") % (self.socket_file)
        if os.path.exists(self.socket_file):
            os.remove(self.socket_file)
        if os.path.exists(lockfile):
            os.remove(lockfile)

        self.socketHandler = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  # Create a socket object
        self.socketHandler.bind(self.socket_file)
        self.socketHandler.listen(1)
        htdte_logger.inform("Listening...")
        # ---Creating lock file to be used as a polling indicator for client
        htdte_logger.inform(("Openning client lock file %s...") % (lockfile))
        serverlockfile = open(lockfile, "w", 1)
        serverlockfile.close()
        # ------------------------------
        self.clientSock, addr = self.socketHandler.accept()
        htdte_logger.inform("Accepted connection...")
        htdte_logger.inform(("Server %s up and running ...") % (server_name))
        while True:
            data = self.clientSock.recv(4096)
            if not data:
                break
            else:
                if (self.debug_mode):
                    htdte_logger.inform(("Server %s got a message: %s ...") % (server_name, data))
                if "HTD_CLOSE_SERVER" == data:
                    break
                else:
                    self.send("OK")
                    self.request_handler(data)
        htdte_logger.inform("-" * 20)
        htdte_logger.inform("Shutting down...")
        if os.path.exists(lockfile):
            os.remove(lockfile)
        time.sleep(5)
        self.socketHandler.close()
        if (os.path.isfile(self.socket_file)):
            os.remove(self.socket_file)
            # -----------------------------

    def send(self, data):
        try:
            self.clientSock.send(data)
        except socket.error as err:
            htdte_logger.error(("Server%s:Fail send a message to client: %s...") % (self.server_name, err))
        if (self.debug_mode):
            htdte_logger.inform(("Server%s: message:  %s :Sent to client.") % (self.server_name, data))

    # ----------------------------
    def request_handler(self, data):
        htdte_logger.error("Should be overwritten by inheritance hierarchy object...")

# -------------------------------------------


class htd_unix_socket_client(object):
    def __init__(self, wait_for_server_delay_in_sec=180, socketLogHndl=None, pooling_server_boot_file=False):
        if ('HTD_SOCKET_FILE' not in list(os.environ.keys())):
            htdte_logger.error("Missing unix env[HTD_SOCKET_FILE] used for socket file name specification")

        self.socket_file = os.environ['HTD_SOCKET_FILE']
        self.socketHandler = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  # Create a socket object
        self.socketLogHndl = socketLogHndl

        lockfile = ("%s_sboot") % (self.socket_file)
        self.server_connected = False
        # wait for the server to open
        if (not pooling_server_boot_file):
            for try_i in range(1, wait_for_server_delay_in_sec):
                time.sleep(1)
                htdte_logger.inform(("Connecting to Server by socket: %s") % (self.socket_file))
                try:
                    self.socketHandler.connect(self.socket_file)  # Connect to socket
                    htdte_logger.inform(("Connected to  server."))
                    self.server_connected = True
                    break
                except socket.error:
                    pass
        else:
            time_out_cnt = 60
            while (not os.path.isfile(lockfile) and time_out_cnt > 0):
                htdte_logger.inform(("Waiting for server boot on file: %s (%d)") % (lockfile, time_out_cnt))
                time_out_cnt -= 1
                time.sleep(10)
            if (time_out_cnt > 0):
                htdte_logger.inform(("Server boot file (%s) found :%d...") % (lockfile, time_out_cnt))
                htdte_logger.inform(("Connecting to Server by socket: %s") % (self.socket_file))
                self.socketHandler.connect(self.socket_file)  # Connect to socket
                htdte_logger.inform(("Connected to  server."))
                self.server_connected = True
                # ----------------------------------------------------------

        self.socketHandler.settimeout(wait_for_server_delay_in_sec)  # timeout in case server stop responding
        if (not self.server_connected):
            htdte_logger.error(("Fail connecting  to DPI server after %d sec...") % (wait_for_server_delay_in_sec))

    # ----------------------------------
    def __del__(self):
        try:
            print('From Python Destructor')
            self.socketHandler.send("HTD_CLOSE_SERVER")
        except socket.error:
            pass
        # -----------------
        try:
            self.socketHandler.close()
        except NameError:
            pass
        return

    # ----------------------------------
    def send_receive_message(self, msg):
        try:
            self.socketHandler.send(msg)
        except socket.error:  # in case there's an error with sending the message
            htdte_logger.error(('Failed to send msg (%s) to socket ') % (msg))
        try:
            rcv = self.socketHandler.recv(2048)
        except socket.Timeouterror:
            print('Server request timeout')
            htdte_logger.error(('Server send msg (%s) timeout to socket ') % (msg))

        prev_timeout = self.socketHandler.gettimeout()
        self.socketHandler.settimeout(604800)
        self.socketHandler.send("OK")
        rcv = self.socketHandler.recv(
            4096)  # data is arriving in unknown package size, thus concatenating all responses and then working with it

        self.socketHandler.settimeout(prev_timeout)
        return rcv

    # -------------------------------------
    def write(self, data):
        self.socketLogHndl.write(data)
        ret_val = self.send_receive_message(data)
        self.socketLogHndl.write(("//DPI ret value:%s\n") % ret_val)
        return ret_val
# --------------------------------------------------------
#            END OF CLASS htd_unix_socket_server
# -------------------------------------------------


def receive_signal(signum, stack):
    print('Received:', signum)
# ------------------------------


class htd_info_server(object):
    def __init__(self, norun=0):
        self.socketHandler = None
        self.server_name = ""
        self.socket_file = ""
        self.server_process = None
        self.norun = norun
        self.server_retry_times = 2
        self.server_timeout = 60

    def set_server_retry(self, times): self.server_retry_times = times

    def set_server_timeout(self, timeout_in_sec): self.server_timeout = timeout_in_sec

    def StartServer(self, server_name, socket_file, server_command, wait_for_client_delay_in_sec, timeout, logtofile=1):
        self.server_name = server_name
        self.socket_file = socket_file
        self.norun = (os.environ.get('HVM_INFO_SERVER_NORUN') is not None and os.environ.get('HVM_INFO_SERVER_NORUN') in ["1", "True"])
        connected = 0
        if (os.environ.get('HVM_INFO_NO_SERVER') is not None and int(os.environ.get('HVM_INFO_NO_SERVER'))):
            htdte_logger.inform("Found UNIX environment HVM_INFO_NO_SERVER ....")
            norun = 1
            wait_for_client_delay_in_sec = int(os.environ.get('HVM_INFO_NO_SERVER'))
        if (self.norun):
            self.RunServerAndClient(server_name, socket_file, server_command, wait_for_client_delay_in_sec, timeout,
                                    logtofile, 1, self.norun)
        else:
            for i in range(1, self.server_retry_times):
                self.socket_file = ("%s_%d") % (socket_file, i)
                htdte_logger.inform(("Trial # (%d) to boot %s server....") % (i, server_name))
                connected = self.RunServerAndClient(server_name, self.socket_file, server_command,
                                                    wait_for_client_delay_in_sec, timeout, logtofile, i, self.norun)
                if (connected):
                    htdte_logger.inform(("Success connecting %s server....") % (server_name))
                    return
            htdte_logger.error(("Unable to boot Server(%s)<->Client system.") % (server_name))

    def GetServerProcessId(self): return self.server_process.pid if(self.server_process is not None) else 0

    def RunServerAndClient(self, server_name, socket_file, server_command, wait_for_client_delay_in_sec, timeout,
                           logtofile=1, retry_i=1, norun=0):
        subprocess_id = -1
        final_server_cmd = (server_command) % (socket_file)
        htdte_logger.inform(("Running %s server: %s") % (server_name, final_server_cmd))
        server_log_file = ("%s_%d.log") % (self.server_name, retry_i)
        try:
            call([("/bin/rm -rf %s") % socket_file, "-l"])
        except BaseException:
            pass
        if (not norun):
            if (logtofile):
                try:
                    call([("/bin/rm -rf %s") % ("%s.log") % ((self.server_name)), "-l"])
                except BaseException:
                    pass
                fptr = open(server_log_file, 'w')
                with open(os.devnull) as devnull:
                    self.server_process = subprocess.Popen(final_server_cmd, shell=True, stdout=fptr, stderr=fptr)
            else:
                with open(os.devnull) as devnull:
                    self.server_process = subprocess.Popen(final_server_cmd, shell=True)
            # subprocess_id.append(self.server_process.pid)
        else:
            htdte_logger.inform(("NORUN mode detected pls run the server manually."))
        # ---------
        self.socketHandler = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  # Create a socket object
        # wait for the server to open
        for try_i in range(1, wait_for_client_delay_in_sec):
            time.sleep(5)
            # --Check if server is not terminated
            if (not norun and self.server_process.poll() is not None):
                stdoutdata, stderrdata = self.server_process.communicate()
                htdte_logger.inform(
                    ('Server process has been terminated unexpetedly,(%s%s) the failure details pls see in %s ') % (
                        str(stdoutdata), str(stderrdata), server_log_file))
                return 0

            try:
                self.socketHandler.connect(socket_file)  # Connect to socket
                htdte_logger.inform(("Connected to DFX server."))
                return 1
            except socket.error:
                pass
        # ---------------------------
        if (try_i > wait_for_client_delay_in_sec - 2):
            return 0
        else:
            self.socketHandler.settimeout(self.server_timeout)  # timeout in case server stop responding
            htdte_logger.inform(("Setting Server-%s timeout to (%dsec)..") % (self.server_name, self.server_timeout))
            return 1

    # ------------------------------
    def __del__(self):
        try:
            if (not self.norun and self.server_process.poll() is not None):
                stdoutdata, stderrdata = self.server_process.communicate()
                print ('Tap info Server process  has been terminated unexpetedly')
                htdte_logger.inform((
                                    'Server process (%s) has been terminated unexpetedly,(%s%s) the failure details pls see in %s.log ') % (
                                    server_command, str(stdoutdata), str(stderrdata), self.server_name))
                return -1
            exit_message = "<server_exit>\n"
            self.socketHandler.send(exit_message)
            self.socketHandler.close()
            call([("/bin/rm -rf %s") % self.socket_file, "-l"])
            if ((self.server_process is not None) and (not self.server_process.poll() is None)):
                print(("Killing server (%s) proccess") % (self.server_name))
                htdte_logger.inform(("Killing server (%s) proccess") % (self.server_name))
                self.server_process.terminate()
        except BaseException:
            pass
        return

    # -----------------------
    def remove_last_line_from_string(self, str):
        return str[:str.rfind('\n')]

    # ---------------------------------------
    def send_receive_message(self, msg):
        # if(self.server_process==None or self.server_process.poll()==None):
        #  htdte_logger.error(( 'Server (%s) process has been disconnected. ')%(self.server_name))
        if (not self.norun and self.server_process.poll() is not None):
            stdoutdata, stderrdata = self.server_process.communicate()
            htdte_logger.inform((
                                'Server process (%s) has been terminated unexpetedly,(%s%s) the failure details pls see in %s.log ') % (
                                server_command, str(stdoutdata), str(stderrdata), self.server_name))
            return -1
        socket_in_progress = True
        signal.signal(signal.SIGUSR1, receive_signal)
        signal.signal(signal.SIGUSR2, receive_signal)
        try:
            self.socketHandler.send(msg)
        except socket.error:  # in case there's an error with sending the message
            print('Send failed')
            htdte_logger.error(('Failed to send msg (%s) to socket ') % (msg))
        rcv = ''
        while True:
            rcv += self.socketHandler.recv(
                4096)  # data is arriving in unknown package size, thus concatenating all responses and then working with it
            if (re.search(r'<\w+>\s+done', rcv)):  # server sends "<message> done" when finished
                break
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)
        socket_in_progress = False
        return self.remove_last_line_from_string(self.remove_last_line_from_string(rcv))  # removing 2 obsolete lines
