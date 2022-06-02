
  import "DPI-C" context task htd_start_server( input string serverName );
  import "DPI-C" context task htd_simple_server(input string serverName,  input string socketFile);
  import "DPI-C" context function int find_substr(input string input_line, input string substr);
  export "DPI-C" function htd_get_dpi_result;
  export "DPI-C" task htd_dpi_execute_single_request;

//Oobsolete export functions used by hvm_dpi_lib:
//  export "DPI-C" function htd_sv_display;
//  export "DPI-C" task htd_mem_read;
//  export "DPI-C" task htd_mem_write;
//  export "DPI-C" function htd_mem_build;
//  export "DPI-C" function htd_time_print;

`ifndef SLA_RAL_DATA_WIDTH
  `define SLA_RAL_DATA_WIDTH 32
`endif
typedef logic[`SLA_RAL_DATA_WIDTH-1:0] sla_ral_data_t;


class like_parser;
        static like_parser like_parser_this;
        static string dpi_result;
        string name;
	bit check_stf = 1'b0;
	int fstream, line_num, wait_cycles=-1;
	string itpp_line, itpp_cmd;
//	itpp_tap_reset_seq tap_pwrgd_reset;
	string rem, sig, val,wait_cycles_str;
        sla_ral_data_t sla_val,peek;


        function new(string name="like_parser_obj");
            like_parser_this = this;
        endfunction: new

        static function like_parser get_this();
                        return like_parser_this;
        endfunction: get_this

        function void write_dpi_result(string status_str,  string value_str);                     
                        dpi_result = {status_str,value_str};
                        $display ("dpi_result is: %s", dpi_result);
        endfunction: write_dpi_result


        static function string read_dpi_result();
                        return (dpi_result);
        endfunction: read_dpi_result


	task automaticbody;
                $display("  ");
                $display(" Now, calling the server ");
                $system("client&"); 
                htd_start_server("RTL Simulation hvm-Dpi");
                //svtb_itpp_transactor_parser("rem: error client end of transmission", 13);
                //htd_dpi_execute_single_request("rem: error client end of transmission" );
                //$display( htd_get_dpi_result());
                //htd_dpi_execute_single_request("rem: peek_signal soc_tb.gl2pcRawPwrGoodXnnnH 0" );
                //$display( htd_get_dpi_result());
                $display("\n Return from Server\n ");

                // For regular mode with ITPP commands: svtb_itpp_transactor_parser(itpp_line,line_num);
         endtask: automaticbody



        ///////////////////////////////////////////////////////////////////////////
        // Actual ITPP format transactor
        ///////////////////////////////////////////////////////////////////////////
        task svtb_itpp_transactor_parser(input string input_line, int line_num);
                        string itpp_cmd="";
                        string status_str="No-Status|"; 
                        string value_str="Non";
                        string error_str="";
		    	sla_ral_data_t peek;
                        integer indx;
                        //value_str = sla2str(peek);
                        //value_str = $psprintf("0x%0x",peek);
                        //$display("\npeek signal is: %s\n", value_str);
                        //$display("value in hex is: 0x%x",peek); 
                        write_dpi_result(status_str,value_str);
                        $display("Inside transactor. The input-line is: %s", input_line);
                        #100ps
			// next line if this one is blank or a comment
			///////////////////////////////////////////////////////////////////////////
			if((!$sscanf(input_line, "%s", itpp_cmd)) || (input_line.substr(0, 0) == "#") || (input_line.substr(0, 1) == "//") )
                            begin
                               #10ns status_str = "No ITPP command|"; 
                               #1ns  value_str = "Non";
                               write_dpi_result(status_str,value_str);
                               return;
                            end
                        case(itpp_cmd)
                              
                              "HTD_CLOSE_SERVER": begin
                                                 $display("Client end command = PASS");
                                                 status_str = "PASS";
                                                 value_str = "End of ITPP test";
                                                 write_dpi_result(status_str,value_str);
                                                 return;
                             end
                             "rem:": begin //Scan the input-line again for all possible arguments. Missing arguments in the line will be matched by an empty string.
                                           rem = "";
                                           sig = "";
                                           val = "";
                                           wait_cycles = "";
                                           $sscanf(input_line, "rem: %s %s %s %s", rem, sig, val, wait_cycles_str);
                                           $display(" rem is: %s, sig is: %s, val is %s wait_cycles is: %s ", rem, sig,val, wait_cycles);
                                           //convert strings to values if not empty: wait_cycles is an integer with initial value of -1.
                                             if(val.len()>0) begin
                                                val = uscore(val);
                                                sla_val = str2sla(val, line_num);
                                             end
                                             if(sig.len()>0)begin
				                sig = spacify(sig);
                                             end 
                                             if(wait_cycles_str.len()>0) begin
                                                wait_cycles = wait_cycles_str.atoi();
                                             end

                                           //sort the action variable rem:          
                                             case(rem) 
                                                       //error from HPL is recieved:  Fail status,returns error message.
                                                       //////////////////////////////////////////////////////////////////////////////////
                                                       "error": begin
                                                                status_str = "FAIL|";
                                                                indx = find_substr(input_line,"error");
                                                                value_str = input_line.substr(indx, input_line.len()-1);
                                                                write_dpi_result(status_str, value_str);
                                                                $display("Error Message --> Force simulation finish");
                                                        //Add wait-time of 10000ps
                                                         $finish(2); 
                                                       end


                                                                         //signal names end with _signal: No valid signal.Fail status. returns empty string
                                                                         //////////////////////////////////////////////////////////////////////////////////   
				                                         //if (rem.substr(rem.len()-7, rem.len()-1) != "_signal") begin
                                                                         //    status_str = "FAIL|";
                                                                         //    value_str = "";
                                                                         //    write_dpi_result(status_str, value_str);
                                                                         //    return;
				                                         //end
                                               
 

                                                       // Return simulation time: How to cast $time variable ?
                                                       ///////////////////////////////////////////////////////////////////////////
				                       "model_time": begin
                                                                     #100ps;
				                                     status_str="PASS|";
                                                                     value_str="100";
                                                                     //$display("Time is: %d\n", $time);
						                     //value_str = $psprintf("%d",$time);
                                                                     write_dpi_result(status_str, value_str);
                                                                     return;
                                                       end
                                                       "check_signal": begin
                                                                       chandle handle;
                                                                       int j =0;
                                                                       for(int i=0; i<=10000; i++)
                                                                           j = j+i;
                                                                       //handle = null;
                                                                       //handle  = SLA_VPI_handle_by_name( sig);
						                       //if( handle == null ) begin 
                                                                       //    $display("handle is null");
        					                       //	   status_str = "FAIL|";
                                                                       //    value_str = "null handle";
                                                                       //    write_dpi_result(status_str, value_str);
                                                                       //    return;
					                               //end else begin
        						               status_str = "PASS|";
                                                                       value_str = "1";
                                                                       write_dpi_result(status_str, value_str);
                                                                       return;
                                                       end
				                       // signal peeking
				                       ///////////////////////////////////////////////////////////////////////////
                                                       "peek_signal": begin
                                                                     peek = 32'h12345678;
                                                                     if (val.len()==0) begin //command format is: peek_signal <sig>  
                                                                                       status_str = "PASS|";
                                                                                       value_str = sla2str(peek); 
                                                                                       write_dpi_result(status_str, value_str);
                                                                                       return;
                                                                     //command format is: peek_signal <sig> <expected-value> and expected = actual.
                                                                     end else if (val.len() > 0 && sla_val == peek) begin
                                                                                                                    //`ovm_fatal("SPF_ITPP_PARSER_ERROR", $psprintf("signal '%s' actual=0x%0x, expect=0x%0x", sig, peek, sla_val)) 
                                                                                                                    status_str = "PASS|";
                                                                                                                    value_str = sla2str(peek); 
                                                                                                                    write_dpi_result(status_str, value_str);
                                                                                                                    return;
                                                                     //command format is: peek_signal <sig> <expected-value> and expected != actual
                                                                     end else if (val.len() > 0 && sla_val !== peek) begin  
				        		                                                             //`ovm_fatal("SPF_ITPP_PARSER_ERROR", $psprintf("signal '%s' actual=0x%0x, expect=0x%0x", sig, peek, sla_val))
                                                                                                                     status_str = "FAIL|";
                                                                                                                     value_str = sla2str(peek);
                                                                                                                     write_dpi_result(status_str, value_str);
                                                                                                                     return;
                                                                     end
                                                       end
				                       // signal deposit:  signal set
				                       ///////////////////////////////////////////////////////////////////////////
                                                       "deposit_signal": begin
				        	                         status_str = "PASS|";
                                                                         value_str = sla2str(sla_val);
                                                                         write_dpi_result(status_str,value_str);
                                                                         return;
                                                                         //`ovm_info("SPF_ITPP_PARSER_INFO",$psprintf("(%0d) Depositing signal '%s' to value 0x%0x",line_num, sig, sla_val), OVM_LOW)
                                                                         //$display("Depositing signal %s to value 0x%ox", sig, sla_val);
				        	                         //if (sla_vpi_put_value_by_name(sig, sla_val) == SLA_FAIL)
				        	                         //`ovm_fatal("SPF_ITPP_PARSER_ERROR",$psprintf("Depositing signal '%s' at line %0d failed", sig, line_num))
                                                       end
				                       // signal forcing
				                       ///////////////////////////////////////////////////////////////////////////
				                       "force_signal": begin
                                                                       status_str = "PASS|";
                                                                       value_str = sla2str(sla_val);
                                                                       write_dpi_result(status_str, value_str);
                                                                       return;
                                                                       //`ovm_info("SPF_ITPP_PARSER_INFO",$psprintf("(%0d) Forcing signal '%s' to value 0x%0x", line_num, sig, sla_val), OVM_LOW)
				        	                       //if (sla_vpi_force_value_by_name(sig, sla_val) == SLA_FAIL)
				        		               //`ovm_fatal("SPF_ITPP_PARSER_ERROR", $psprintf("Forcing signal '%s' at line %0d failed", sig, line_num))
                                                       end
				                       // signal releasing
				                       ///////////////////////////////////////////////////////////////////////////
				                       "release_signal":  begin
				        	                          //`ovm_info("SPF_ITPP_PARSER_INFO", $psprintf("(%0d) Releasing signal '%s' value 0x%0x", line_num, sig, sla_val), OVM_LOW)
                                                                          status_str = "PASS|";
                                                                          value_str = sla2str(sla_val);
                                                                          write_dpi_result(status_str, value_str);
                                                                          return;
				        	                          //if (sla_vpi_release_value_by_name(sig, sla_val) == SLA_FAIL)
				        		                  //`ovm_fatal("SPF_ITPP_PARSER_ERROR", $psprintf("Release signal '%s' at line %0d failed", sig, line_num))
                                                       end
				                       // signal polling
				                       ///////////////////////////////////////////////////////////////////////////
				                       "poll_signal":  begin
                                                                       status_str = "PASS|";
                                                                       value_str = sla2str(sla_val);
                                                                       #20;
                                                                       write_dpi_result(status_str, value_str);
                                                                       return;
				        	                       //`ovm_info("SPF_ITPP_PARSER_INFO",$psprintf("(%0d) Polling signal '%s' for value 0x%0x", line_num, sig, sla_val), OVM_LOW)
				        	                       //sla_sig_polling(sig, sla_val, 1ms, 1ns);
				        	                       //aneeman: until sla_sig_polling will be fix in sla_vpi, use local sla_sig_polling_fix
				        	                       //sla_sig_polling_fix(sig, sla_val, 1ms, 1ns);
				        	                       //`ovm_info("SPF_ITPP_PARSER_INFO", $psprintf("Done polling signal '%s'", sig), OVM_LOW)
                                                       end
                                                       // command line rem:  has no valid ram command
                                                       default:  begin                                                      
                                                                 status_str = "FAIL|";
                                                                 value_str = "No valid rem command";
                                                                 write_dpi_result(status_str,value_str);
                                                                 return;
                                                       end
                                     endcase //of rem case
                             end //of rem

                             //labels
	                     ///////////////////////////////////////////////////////////////////////////
		             "label:": begin
			               string label;
				       label = chomp(input_line.substr(7, input_line.len()-1));
				       //`ovm_info("SPF_ITPP_PARSER_INFO", $psprintf("(%0d) label-> %s", line_num, label), OVM_LOW)
			     end
                             default: begin
                                      $display("No match found");
                                      write_dpi_result(status_str, value_str);
                             end
                        endcase //of itpp_cmd  
        endtask  : svtb_itpp_transactor_parser



        //////////////////////////////////////////////////////////////////////////
        function chandle sla_vpi_handle_by_name( string name);
                      chandle handle;
                      handle = null;
                      //handle  = SLA_VPI_handle_by_name( name);
                      if( handle == null ) begin
                          //`sla_error( "sla_dpi", ("sla_vpi_handle_by_name(): %s does not exist", name));

                           return( null );
                      end else begin
                           return( handle );
                      end
        endfunction : sla_vpi_handle_by_name

        // remove underscore characters from bitstreams
	///////////////////////////////////////////////////////////////////////////
	function automatic string uscore(string s);
		string ch;
		for (int i=0; i<s.len(); i++) begin
			ch = s.getc(i);
			if (ch != "_")
				uscore = {uscore, ch};
		end
	endfunction


	// replace '%20' with space character in signal names
	///////////////////////////////////////////////////////////////////////////
	function automatic string spacify(string s);
		for (int i=0; i<s.len()-2; i++)
			if (s.substr(i, i+2) == "%20") begin
				i += 2;
				spacify = {spacify, " "};
			end else
				spacify = {spacify, s[i]};
		spacify = {spacify, s.substr(s.len()-2, s.len()-1)};
	endfunction


        // convert signal string to long unsigned integer
	///////////////////////////////////////////////////////////////////////////
	function automatic sla_ral_data_t str2sla(string s, int l);
		if (s.substr(0, 1) == "0b")
			str2sla = s.substr(2, s.len()-1).atobin();
		else if (s.substr(0, 1) == "0x")
			str2sla = s.substr(2, s.len()-1).atohex();
		else if (s.substr(0, 1) == "0d")
			str2sla = s.substr(2, s.len()-1).atoi();
		else
			str2sla = s.atoi();
		// check if signal value is greater than 32 bits
		//if (str2sla > `MAX_FORCE_VAL)
		//	`ovm_fatal("SPF_ITPP_PARSER_ERROR",
		//		$psprintf("Signal val %s on line %0d is > 32 bits", s, l))
		//`ovm_info("SPF_ITPP_PARSER_DEBUG",
		//	$psprintf("Converted string value '%s' to SLA value %0d",
		//		s, str2sla), OVM_DEBUG)
	endfunction


	// chop special chars from end of string
	///////////////////////////////////////////////////////////////////////////
        function string chomp(string s);
		string last;
		last = s.getc(s.len()-1);
		while (last == ";" || last == "," || last == " " || last == "\n") begin
			s = s.substr(0, s.len()-2);
			last = s.getc(s.len()-1);
		end
		chomp = s;
	endfunction:chomp


        // sla2str: Returns the string of peek-value
        //////////////////////////////////////////////////////////////////////////////////
        function string sla2str(sla_ral_data_t peeked_signal);
                 return( $psprintf("0x%0x",peeked_signal));
        endfunction: sla2str

endclass: like_parser
//////////////////END OF CLASS like_parser//////////////////////////////////////////////////////////////////////////////////////////////



task  htd_dpi_execute_single_request(input string msg );
                    int line_num=0;
                    like_parser like_parser_hndl;
                    like_parser_hndl = like_parser::get_this();
                    like_parser_hndl.svtb_itpp_transactor_parser(msg, line_num);
                    return;
endtask: htd_dpi_execute_single_request




function string htd_get_dpi_result();
                    string dpi_result;
                    like_parser like_parser_hndl;
                    like_parser_hndl = like_parser::get_this();
                    dpi_result = like_parser_hndl.read_dpi_result();
                    return dpi_result;
endfunction: htd_get_dpi_result










