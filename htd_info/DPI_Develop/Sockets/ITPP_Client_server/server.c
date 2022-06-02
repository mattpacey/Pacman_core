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
//  Socket server that receives a single value from a client such as 6,
//   and returns a list of N Fibinocci numbers such as "1 1 2 3 5 8"
//

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <string.h>

#define PORT 		0x1234
#define FIBSIZE 	8192

int main()
{
        char     fib[FIBSIZE];  /* used for incomming fib name, and
					outgoing data */
        char     line_arr[1000];
	int 	 sd, sd_current, cc, fromlen, tolen, fibmax, n[1000], i, j;
	int 	 addrlen;
	struct   sockaddr_in sin;
	struct   sockaddr_in pin;

        for(j=0;j<1000;j++){
            line_arr[j] = '\0';                                         
        }
        
	printf("SERVER: get an internet domain socket\n");
	if ((sd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
		perror("socket");
		exit(1);
	}

	printf("SERVER: complete the socket structure\n");
	memset(&sin, 0, sizeof(sin));
	sin.sin_family = AF_INET;
	sin.sin_addr.s_addr = INADDR_ANY;
	sin.sin_port = htons(PORT);

	printf("SERVER: bind the socket to the port number\n");
	if (bind(sd, (struct sockaddr *) &sin, sizeof(sin)) == -1) {
		perror("bind");
		exit(1);
	}

	printf("SERVER: show that we are willing to listen\n");
	if (listen(sd, 5) == -1) {
		perror("listen");
		exit(1);
	}
	printf("SERVER: wait for a client to talk to us\n");


        addrlen = sizeof(pin); 
	if ((sd_current = accept(sd, (struct sockaddr *)  &pin, &addrlen)) == -1) {
		perror("accept");
		exit(1);
	}

        while(1){
	          printf("SERVER: get a message from the client\n");
	          if (recv(sd_current, line_arr, sizeof(line_arr), 0) == -1) {
		           perror("recv");
		           exit(1);
	          }
                  printf("SERVER: Received message %s\n", line_arr);

                  printf("SERVER: Response message %s\n", "OK");
	          printf("SERVER: acknowledge the message, reply with OK\n");
	          if (send(sd_current, "OK", strlen("OK"), 0) == -1) {
		           perror("send");
		           exit(1);
	          }
                 /*close socket */
                  if(strcmp("HTD_CLOSE_SERVER\n\0",line_arr)==0){
                             printf("SERVER: close up both sockets\n");
	                     close(sd_current); close(sd);
                             printf("SERVER: give client a chance to properly shutdown\n");
                             sleep(2);
	                     printf("SERVER: Finish!\n");
                             return 0;
                  }
                 /*reset line_arr to '\0' */
                  for(j=0;j<1000;j++){
                      line_arr[j] = '\0';                                         
                  }
          }
}
