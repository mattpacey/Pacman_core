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
   parameter int VALSIZE = 10;

   import "DPI-C" function void client_dpi(input int count,
					   input string hostname,
					   output int vals[VALSIZE]);
   import "DPI-C" function void server_dpi();

      int vals[VALSIZE];

      initial begin
          //fork
            #10
             $display("Launch Server");
           //$system("fib_server&");
             $display("Right before dpi");
	     client_dpi(5, "localhost", vals);
             #20
             $system("fib_server&");
	     $display("V: vals=%p", vals);
          //join
          //#30 $finish;
      end
endprogram : top
