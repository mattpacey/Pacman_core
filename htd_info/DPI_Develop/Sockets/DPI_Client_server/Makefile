# SystemVerilog version
run:	simv client 
	client &
	./simv

simv:	rtl_module.sv server_dpi.c
	vcs -sverilog rtl_module.sv server_dpi.c



# Stand alone vresion
dpi:	client server
	client &
	server

client: client.c
	gcc -g client.c -o client

server: server.c
	gcc -g server.c -o server



DIR = $(shell basename `pwd`)
tar:	clean
	cd ..; tar cvf ${DIR}.tar ${DIR}

clean:
	@rm -rf *~ *.log *.vpd vc_hdrs.h .vcsmx_rebuild *.o
	@rm -rf simv* csrc* core* *.vrh *shell.v .__solver* *.key .ucli*
	@rm -rf client server fib_server
