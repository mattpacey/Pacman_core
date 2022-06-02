CC=/usr/intel/bin/gcc
CFLAGS= -g -fPIC -Wall -pedantic -shared
OBJ1= htd_unix_socket_server.c
OBJ2= client.c

all: clean clean_client client htd_dpi_lib

clean:
	/bin/rm -f ./htd_dpi_lib.so

clean_client:
	/bin/rm -f ./client

client : ${OBJ2}
	${CC} -g -fPIC -Wall -pedantic ${OBJ2} -o ./client


htd_dpi_lib : ${OBJ1}
	${CC} ${CFLAGS} ${OBJ1} -o ./htd_dpi_lib.so


