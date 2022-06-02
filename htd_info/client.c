/* Client.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/un.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <fcntl.h> 
#include <unistd.h> 

#define BUFFSIZE     4096
#define HOST  "localhost"


/*client.c is an executable client. It opens "htd_test_stimulus.itpp" and reads every line.
  Each line is an ITPP command (including remarks). 
  Sends "HTC_CLOSE_SERVER" after EOF, so signal server to stop transaction */
  


int  main(int argc, char **argv){
        char hostname[100];
	char clientrecv_arr[BUFFSIZE];
        char clientsend_arr[BUFFSIZE];
        char *socket_path = "./dpisocket";
	struct sockaddr_un addr;
	int  hp, fd, i, j;
        char ch, filename[25];
        FILE *fp, *fpc;
       
      /*set arrays to zero */
        for(j=0;j<BUFFSIZE;j++){
            clientsend_arr[j] = '\0';                                         
            clientrecv_arr[j] = '\0';
        }

      /* CLIENT: name of the file to be opened. The path is current directory */ 
        strcpy(filename, "htd_test_stimulus.itpp");
        printf("Open this file: %s\n",filename);
	for (i=0; i<argc; i++)
	     printf("CLIENT: argv[%d]='%s'\n", i, argv[i]);
             strcpy(hostname,HOST);
        if (argc>2)
            { strcpy(hostname,argv[2]); }

      /* CLIENT: go find out about the desired host machine */
	if ((hp = gethostbyname(hostname)) == 0) {
		perror("gethostbyname");
		exit(1);
	}

      /* CLIENT: grab an Internet domain socket */
	if ((fd = socket(AF_UNIX, SOCK_STREAM, 0)) == -1) {
                printf("exit client\n");
                exit(1);
	}

      /* CLIENT: fill in the socket structure with host information */
	memset(&addr, 0, sizeof(addr));
	addr.sun_family = AF_UNIX;
        strncpy(addr.sun_path, socket_path, sizeof(addr.sun_path));

      /* CLIENT: connect to PORT on HOST */
	    while (connect(fd,(struct sockaddr *)&addr, sizeof(addr)) == -1) {
	     	   /*perror("connect Error");
		     exit(1);*/
                     printf(".");
	   }
           printf("\n");



        /*Transmit The ITPP file */
        /*Open the ITPP file, read a line and transmit that. Wait for a response*/
          fp = fopen(filename,"r"); /* read mode */
          if( fp == NULL ){
              perror("Error while opening the file.\n");
              exit(EXIT_FAILURE);
          }

        /*Create client.log file */
          fpc = fopen("client.log","a"); 
          if( fpc == NULL ){
              perror("Error while opening the file.\n");
              exit(EXIT_FAILURE);
          }
          
          i=0;
          ch = fgetc(fp);
          while (1) {
                 if(ch == EOF){
                                strcpy(clientsend_arr, "HTD_CLOSE_SERVER\n\0");
	                       /*CLIENT: send HTD_CLOSE_SERVER to server */
	                         if (write(fd, clientsend_arr, strlen(clientsend_arr)) == -1) {
		                           perror("send Error");
                                           exit(1);
	                          }
                                 else{ /*write to file: */
                                      fprintf(fpc, "\nCLIENT SEND: %s\n", clientsend_arr);
                                 } 
                               /* CLIENT: wait for a message to come back from the server */
                                  if (read(fd, clientrecv_arr, BUFFSIZE) == -1) {
                                           perror("recv Error");
                                           exit(1);
                                  }
                                  else{
                                        fprintf(fpc, "CLIENT RECIEVED %s\n", clientrecv_arr);
                                  }
                               /* Break out of loop */
                                  fclose(fpc);
                                  break;
                 }
                 if(ch != '\n'){
                    clientsend_arr[i] = ch;
                    i++;
                 }
                 else if(ch == '\n'){
                                     clientsend_arr[i]='\n';
                                      i++;
                                      clientsend_arr[i]='\0';
                                    /*printf("%s",clientsend_arr);*/

                                    /*Transmit the command-line;*/ 
	                            /*CLIENT: send a message to the server $PORT on machine $HOST */
	                              if (write(fd, clientsend_arr, strlen(clientsend_arr)) == -1) {
		                                perror("send Error");
                                                exit(1);
	                              }
                                      else{ /*write to file: */
                                            fprintf(fpc, "\nCLIENT SEND: %s", clientsend_arr);
                                            printf("CLIENT: send: %s\n",clientsend_arr);
                                      } 

                                    /* CLIENT: wait for a message to come back from the server */
                                      if (read(fd, clientrecv_arr, BUFFSIZE) == -1) {
                                               perror("recv Error");
                                               exit(1);
                                      }
                                      else{
                                            /*Recieved message by client*/
                                              fprintf(fpc, "CLIENT RECIEVED: %s\n", clientrecv_arr);
                                              printf("CLIENT: Recieved from server: %s\n", clientrecv_arr);
                                      }
                                      i=0;
                                      for(j=0;j<BUFFSIZE;j++){
                                          clientsend_arr[j] = '\0';                                         
                                          clientrecv_arr[j] = '\0';
                                      }
                 }
                 ch = fgetc(fp); /*Read next character */
          }
          /*sends 'HTD_CLOSE_SERVER' after EOF, to signal server to stop transaction  
            strncpy(clientrecv_arr, "HTD_CLOSE_SERVER\n", sizeof("HTD_CLOSE_SERVER\n"));
            if (write(fd, clientsend_arr, strlen(clientsend_arr)) == -1) {
	              perror("send Error");
                      exit(1);
	    }
            CLIENT: wait for a message to come back from the server 
            if (read(fd, clientrecv_arr, BUFFSIZE) == -1) { 
                     perror("recv Error");
                     exit(1);
            }  */
            
            printf("client close\n");
          /*Close Client connection to socket */
	    close(fd);
            fclose(fp);
            printf("CLIENT: bye!\n");
	    return 0; 
}
