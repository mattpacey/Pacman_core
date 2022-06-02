//import ovm_pkg::*;
//`include "ovm_macros.svh";
//import sla_pkg::*;
//`include "sla_macros.svh";
`include "./like_parser.svh";


class like_dnv_spf;
  string name;
  like_parser like_parser_hndl;
  function new (string name = "dnv_spf_obj");
  endfunction : new
  task automaticbody;
     like_parser_hndl = new();  //Creating the object of like_parser
     like_parser_hndl.automaticbody;
  endtask;
endclass: like_dnv_spf



class like_my_test;
    string name;
    like_dnv_spf like_dnv_spf_obj;
    function new (string name="my_test");
    endfunction : new
    task automaticbody;
          like_dnv_spf_obj = new();
          like_dnv_spf_obj.automaticbody; 
    endtask;
endclass: like_my_test



module like_reader;
    initial begin
        like_my_test my_test;
             my_test = new();
             my_test.automaticbody;
    end
endmodule: like_reader // like_reader()






