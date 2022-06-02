/* Client.cc  is the program to launch client */

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <string.h>

#define PORT        0x1234
             /* REPLACE with your server machine name*/
#define HOST        "localhost"
#define DIRSIZE     8192

int main(argc, argv)
     int argc; char **argv;
{
        char hostname[100];
	char dir[DIRSIZE];
        char line_arr[1000];
        char ch, filename[25];
        FILE *fp;
	int	sd, i, j;
	struct sockaddr_in sin;
	struct sockaddr_in pin;
	struct hostent *hp;

        for(j=0;j<1000;j++){
            line_arr[j] = '\0';                                         
        }

 
        strcpy(filename, "htd_test_stimulus.itpp");
        printf("Open this file: %s\n",filename);
	for (i=0; i<argc; i++)
	     printf("CLIENT: argv[%d]='%s'\n", i, argv[i]);
        strcpy(hostname,HOST);
        if (argc>2)
            { strcpy(hostname,argv[2]); }

	printf("CLIENT: go find out about the desired host machine\n");
	if ((hp = gethostbyname(hostname)) == 0) {
		perror("gethostbyname");
		exit(1);
	}

	printf("CLIENT: fill in the socket structure with host information\n");
	memset(&pin, 0, sizeof(pin));
	pin.sin_family = AF_INET;
	pin.sin_addr.s_addr = ((struct in_addr *)(hp->h_addr))->s_addr;
	pin.sin_port = htons(PORT);

	printf("CLIENT: grab an Internet domain socket\n");
	if ((sd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
		/*perror("socket");*/
                /*exit(1); */
                printf("\nsd = %d, Inside poll loop\n",sd);
                printf("exit client\n");
                exit(1);
	}

        /*
	   printf("CLIENT: connect to PORT on HOST\n");
	    if (connect(sd,(struct sockaddr *)  &pin, sizeof(pin)) == -1) {
	     	perror("connect");
		exit(1);
	   }
         */

	   printf("CLIENT: connect to PORT on HOST\n");
	    while (connect(sd,(struct sockaddr *)  &pin, sizeof(pin)) == -1) {
	     	   /*perror("connect");
		     exit(1);*/
                     printf(".");
	   }
           printf("\n");



        /*Transmit The ITPP file */
        /*Open the ITPP file, read a line and transmit that. Wait for a response*/
          fp = fopen(filename,"r"); // read mode
          if( fp == NULL ){
              perror("Error while opening the file.\n");
              exit(EXIT_FAILURE);
          }
          
          i=0;
          ch = fgetc(fp);
          while (ch != EOF) {
                 if(ch != '\n'){
                    line_arr[i] = ch;
                    i++;
                 }
                 else if(ch == '\n'){
                                      line_arr[i]='\n';
                                      i++;
                                      line_arr[i]='\0';
                                      printf("%s",line_arr);

                                    /*Transmit the line;*/ 
	                              printf("CLIENT: send a message to the server PORT on machine HOST\n");
	                              if (send(sd, line_arr, strlen(line_arr), 0) == -1) {
		                                                                            perror("send");
                                                                                            exit(1);
	                              }
                                      printf("CLIENT: wait for a message to come back from the server\n");
                                      if (recv(sd, dir, DIRSIZE, 0) == -1) {
                                               perror("recv");
                                               exit(1);
                                      }
                                      printf("CLIENT: '%s'\n", dir);
                                      i=0;
                                      for(j=0;j<strlen(line_arr);j++){
                                          line_arr[j] = '\0';                                         
                                      }
                 }
                 ch = fgetc(fp);
          }
          /*Close Client connection to socket */
	  close(sd); 

                                      /*printf("%s",line_arr);

                                    Transmit the line; 
	                              printf("CLIENT: send a message to the server PORT on machine HOST\n");
	                              if (send(sd, line_arr, strlen(line_arr), 0) == -1) {
		                                                                            perror("send");
                                                                                            exit(1);
	                              }
                                      printf("CLIENT: wait for a message to come back from the server\n");
                                      if (recv(sd, dir, DIRSIZE, 0) == -1) {
                                               perror("recv");
                                               exit(1);
                                      }
                                      printf("CLIENT: '%s'\n", dir); */

          printf("CLIENT: bye!\n");
	return 0;
}
