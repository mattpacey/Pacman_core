from htd_utilities import *


class hpl_tap_transactor_entry(object):
    def __init__(self, state, sequence, sequence_size=-1, tag="", bit0=-1, strobe_bit0=-1, comment="", main_tx=1, pading_left=0, padding_rigth=0, strobes=""):
        self.state = state
        self.sequence = sequence
        self.sequence_size = sequence_size
        self.tag = tag
        self.strobes = strobes
        self.pad_left = pading_left
        self.pad_rigth = padding_rigth
        self.bit0 = bit0
        self.strobe_bit0 = strobe_bit0
        self.comment = comment
        self.main_tx = main_tx
        self.mid_transaction_queue = []
        # ---------------
        if(state not in ["ir", "dr", "state", "tap_size", "pscand", "label"]):
            htdte_logger.error(("Improper tap transaction state - \"%s\", expected [\"ir\",\"dr\"]") % (state))
        if(type(sequence)in [str, str]):
            self.sequence_size = len(sequence)
            self.sequence = int(sequence, 2)
        elif(isinstance(sequence, int) or isinstance(sequence, int)):
            self.sequence_size = sequence_size
            self.sequence = sequence
            if(sequence_size < 0):
                htdte_logger.error("Sequence size expected when sequence is an integer type")
            if(self.sequence >= pow(2, sequence_size)):
                htdte_logger.error(("Sequence size of integer type exceed argument \"sequence_size\" value - 0x%x.Pls. specify proper sequence length or int value range (<0x%x)") % (self.sequence, pow(2, sequence_size)))
        else:
            htdte_logger.error(("Unsupported sequence type - %s parameter .Expected string or integer") % (type(sequence)))
        # -----------------
        if((state in ["ir", "dr"]) and (tag not in ["", "epir", "epdr", "root"])):
            htdte_logger.error((r"Improper tap transaction tag received -\%s\", Expected \"\",\"epir\",\"epdr\" or\"root\"") % (tag))
        if(tag != ""):
            if(bit0 < 0 and (state != "state" and state != "tap_size" and state != "pscand" and state != "label")):
                htdte_logger.error(("Bit0 marker missing for transaction indentified by tag - \"%s\" ") % (tag))
            else:
                self.bit0 = bit0
            self.strobe_bit0 = strobe_bit0
            # --------
            self.tag = tag
