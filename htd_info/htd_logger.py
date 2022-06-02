import os
import locale
import imp
import sys
import time
import inspect
import re
import traceback
import binascii
# -----------Logger Class--------------


'''
Basic object for logging. It supports 4 types of messages: inform, warn, debug with level
and fatal that will kill halt the emulation. The TB uses multiple instances of the log
for different types of messages. Each logger can also print to the stdout if set to
'''

HTD_PRINT_LOG_ONLY = 0
HTD_PRINT_INTERFACE_ONLY = 1
HTD_PRINT_INTERFACE_AND_LOG = 2
header_buffer = []


class LOGGER_ERROR_CODES:
    DEFAULT = 257
    GROUP_CHECK = 100
    OS_CHECK = 101


class Logger(object):
    def __init__(self, fileName):
        # The stream to which we will print (flush each line)
        path = re.sub("[A-z0-9_]+$", "", fileName)
        self.phase_name = ""
        try:
            self.logStream = open(fileName, "w", 1)
        except IOError as e:
            print("\n\n\n----------ERROR:-----------\nCan't copen a file ({0}):I/O error({1}): {2}".format(fileName, e.errno, e.strerror))
            sys.exit(LOGGER_ERROR_CODES.DEFAULT)
        except BaseException:
            print("\n\n\n----------ERROR:-----------\nUnexpected error: Can't copen a file - %s", fileName)
            sys.exit(LOGGER_ERROR_CODES.DEFAULT)
        # The level of the debug messages we want to see. If the level is lower
        # then the verbosity message will be printed (higher verbose, more messages
        self.verbosity = 0
        self.logToStdout = 1
        self.interface_err_handler = None
        self.error_container = []
        self.collect_all_errors_mode = False
        self.collected_errors_prefix_message = ""
        self.enforce_callback_interface_only = -1
        self.supress_error = False
    # -------------------------------------------

    def set_supress_error(self): self.supress_error = True

    def unset_supress_error(self): self.supress_error = False

    def set_collect_all_erros_message_prefix(self, prefix): self.collected_errors_prefix_message = prefix

    def set_collect_all_errors_mode(self): self.collect_all_errors_mode = True

    def unset_collect_all_errors_mode(self): self.collect_all_errors_mode = False

    def has_collected_errors(self): return (len(self.error_container) > 0)

    def print_collected_errors(self):
        for line in self.error_container:
            self.inform(line, 0, 0, "COLLECTED_ERRORS")

    def enforce_interface_print_only(self):
        self.enforce_callback_interface_only = 1

    def setPhaseName(self, phase):
        self.phase_name = phase

    def clrPhaseName(self):
        self.phase_name = ""

    def setErrHndlrInterface(self, hndl):
        self.interface_err_handler = hndl

    def callBack_for_extensions(self, line):
        pass

    def set_message_signal(self, line_bin_val): pass

    def log(self, line):
        self.logStream.write(line)
        self.callBack_for_extensions(line)

    def add_header(self, line):
        header_buffer.append(line)

    def get_header(self):
        return header_buffer

    def inform(self, line, distribute_to_callback=0, level=0, prefix="Inform"):
        if level > self.verbosity:
            return
        if (re.search(r"^\s*\n", line)):
            lineToPrint = ("%s") % (
                line.replace("\n", ("\n [%s,phase:%s] - ") % (prefix, self.phase_name if self.phase_name != "" else "none"),
                             1)) if distribute_to_callback != HTD_PRINT_INTERFACE_ONLY else line
        else:
            lineToPrint = (" [%s,phase:%s] - %s") % (prefix, self.phase_name if self.phase_name != "" else "none",
                                                     line) if distribute_to_callback != HTD_PRINT_INTERFACE_ONLY else line
        # Write the line to the log
        if(self.enforce_callback_interface_only > 0):
            self.callBack_for_extensions(lineToPrint)
            if (distribute_to_callback == HTD_PRINT_LOG_ONLY or distribute_to_callback == HTD_PRINT_INTERFACE_AND_LOG):
                self.logStream.write(("%s\n") % (lineToPrint))
        else:
            if (
                    distribute_to_callback == HTD_PRINT_INTERFACE_ONLY or distribute_to_callback == HTD_PRINT_INTERFACE_AND_LOG):
                self.callBack_for_extensions(lineToPrint)
            if (distribute_to_callback == HTD_PRINT_LOG_ONLY or distribute_to_callback == HTD_PRINT_INTERFACE_AND_LOG):
                # If required print to stdout also
                if (self.logToStdout):
                    print(lineToPrint)
                self.logStream.write(("%s\n") % (lineToPrint))
        # --Setting message to signal
        if(distribute_to_callback == HTD_PRINT_INTERFACE_ONLY or distribute_to_callback == HTD_PRINT_INTERFACE_AND_LOG):
            MessageLine = line.replace("\n", "").replace("Start Action", "")
            newline = line[:62 if(len(MessageLine)>62) else len(line)]
            bin_val = int(bin(int(binascii.hexlify(newline.encode()), 16) << 8), 2)
            self.set_message_signal(bin_val)

    def warn(self, line):
        prf = "WARNING - "
        self.inform(line, prefix=prf)

    def error_str(self, line, prf="ERROR - "):
        # ------------------------
        self.inform("\n\n\n\n----------ERROR:-----------\n", prefix="")
        self.inform(line, prefix=prf)
        formatted_lines = traceback.format_stack()
        line = "\n----------Print Stack:-----------\n"
        self.inform(line, prefix=prf)
        # line2print+=line
        # ------------------
        line = str(formatted_lines).replace("['", "").replace("']", "").replace("\\n", "").replace("', '", "\n")
        self.inform(line, prefix=prf)

    def error(self, line, err_code=LOGGER_ERROR_CODES.DEFAULT):
        if(self.supress_error):
            return
        # ---------------------------
        prf = "FATAL ERROR - "
        if(self.collect_all_errors_mode):
            self.error_container.append(("%s->%s") % (self.collected_errors_prefix_message, line))
        # ---------------------------------
        if (self.interface_err_handler is not None):
            self.interface_err_handler.error(("[%s]  -  %s") % (prf, line))
        self.error_str(line, prf)
        self.inform("Post Error ...", "ERROR")
        if(not self.collect_all_errors_mode):
            self.inform("Exiting..", "ERROR")
            sys.exit(err_code)

    def debug(self, line, level):
        if level <= self.verbosity:
            prefix = ("Debug({}) - ").format(level)
            self.inform(line, 0, level, prefix)

    def close(self):
        self.logStream.close()

    def __del__(self):
        self.logStream.close()
