//-----------------------------------------------------------------------------
// This code example can be shared freely as long as you keep
// this notice and give us credit. In the event of publication,
// the following notice is applicable:
//
// (C) COPYRIGHT 2011 Chris Spear.  All rights reserved
//
// It is derived from http://www.pcs.cnu.edu/~dgame/sockets/socket.html,
// which is derived from the RPC Programming Nutshell text.
// The entire notice above must be reproduced on all authorized copies.
//-----------------------------------------------------------------------------
//

program automatic top;
   import "DPI-C" function int server_dpi();
      initial begin
            #10
             $display("Launch Client");
             //$system("client&");
             $display("Right before call to server_dpi");
	     server_dpi();
             #20
	     $display("End-Of-Simulation");
            #30 $finish;
      end
endprogram : top
