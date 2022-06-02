#include <sys/socket.h>
#include <sys/un.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <signal.h>
#include <errno.h>
#define PORT     0x1234
#define BUFFSIZE 4096
#define ReadBufferSize 4096

fd_set readset;
int listfd;
int htd_hpl_socket;
pid_t ChildPid;
/* dpi_execute_single_request is an exported funtion, written in SV. */ 
/* extern char* htd_dpi_execute_single_request( const char* msg ); */
extern void htd_dpi_execute_single_request(const char* msg);
extern char* htd_get_dpi_result();


void killzombies() {
   kill(ChildPid, SIGKILL);
   close(htd_hpl_socket);
   remove(getenv("HTD_SOCKET_FILE"));
}
void handle_sig(int sig) {
    killzombies();
    exit(0);
}
/* ------------------------ */
int socket_read(char* buf){
  int result;
  int i;
  
  do{ FD_ZERO(&readset);
   FD_SET(htd_hpl_socket, &readset);
   result = select(htd_hpl_socket+1, &readset, NULL, NULL, NULL);
  } while (result == -1 && errno == EINTR);
  if (result > 0) {
     if (FD_ISSET(htd_hpl_socket, &readset)) {
  	/* The socket_fd has data available to be read */
  	result = recv(htd_hpl_socket, buf, ReadBufferSize, 0);
  	if (result == 0) {
  	 return -1;
  	}
	for(i=result;i<ReadBufferSize;i++){
	 buf[i]='\0';
	};
     }
  }
  else if (result < 0) {
     /* An error ocurred, just print it to stdout */
     printf("Error on select(): %s", strerror(errno));
  }
return 0;
}

void htd_start_server(const char *serverName){

    struct sockaddr_un addr,remote;
    char BUFF[ReadBufferSize];
    char BUFF_OUT[ReadBufferSize];
    unsigned int t=sizeof(remote);
    struct timeval tv;
    FILE* sfile;
    char     server_status_file[ReadBufferSize];
    char *socketFile=getenv("HTD_SOCKET_FILE");
    tv.tv_sec =10;
    tv.tv_usec = 0 ;
    if(getenv("HTD_SOCKET_FILE")==NULL){
      perror("ERROR:Missing unix env[\"HTD_SOCKET_FILE\"] required for socket file specification..");
      return;
    }
   
    /*--Client will pool this file to sync a server boot status --*/
    sprintf(server_status_file,"%s_sboot",socketFile);
    if( access( server_status_file , F_OK ) != -1 ){
      remove(server_status_file);   
    } 
    /*---------------------*/
    /*
    if(getenv("HTD_TE_CMD")==NULL){
      perror("ERROR:Missing unix env[\"HTD_TE_CMD\"] used as CMD to invoke client process..");
      return;
    } 
    
    ChildPid = fork();
    if (ChildPid  >= 0)
    { 
	if (ChildPid  == 0){
	
            printf("Running Client: %s",getenv("HTD_TE_CMD"));	    
	    if(system(getenv("HTD_TE_CMD"))){
	      killzombies();
	    };
            return;
	} else 
	{
*/
            /*-----------parent  process-----------------*/
	 /*   printf("Client Process PID:%d\n",ChildPid);
	    atexit(killzombies);*/
	    /*-------------*/
	    listfd = socket(AF_UNIX, SOCK_STREAM, 0);
	    if(listfd == -1){
        	perror("Create htd socket");
        	exit(-1); 
	    }	
	    memset(&addr, 0, sizeof(struct sockaddr_un));
	    addr.sun_family = AF_UNIX;
	    strncpy(addr.sun_path,socketFile ,sizeof(addr.sun_path)-1);
	    unlink(addr.sun_path);
	    sleep(1);
            if (bind(listfd , (struct sockaddr *) &addr, sizeof(struct sockaddr_un))!=0){
	      printf("bind htd_socket unsuccessful\n");
	    }
	    else{
	      printf("bind htd_socket successful\n");
	    }
	    listen(listfd, 1);

	    fflush(stdout);
	    printf("Running on htd socket: %s...\n",socketFile);
	    /* ------Create server boot file indicate that server boot done --- */
	  
            printf("Creating server boot file: %s...\n",server_status_file);
	    if ((sfile = fopen(server_status_file, "w"))){
                fprintf(sfile,"OK");
                fclose(sfile);
  	    }

	   /*
	    * Listen for connections
	    * and send random phrase on accept
	    */

	    htd_hpl_socket  = accept(listfd,(struct sockaddr *)&remote, &t);
	    if(htd_hpl_socket==-1) {
	      perror("Failing accepting the htd client connection..");
	      exit(1);
	    };

	    if (setsockopt (htd_hpl_socket, SOL_SOCKET, SO_RCVTIMEO, (char *)&tv, sizeof tv))
	       perror("htd socket setsockopt error");
	    /* Call select() */	  
             /*-----------------------------*/
	    while(1){
		if(socket_read(BUFF)) { 
		  break;		 
		};
               
		if( strncmp(BUFF,"HTD_CLOSE_SERVER",16)==0){ 
                   printf("Htd Server %s shutdown ...\n",serverName);
                   sleep(2);
                   break;
                } else {
         	write(htd_hpl_socket,"OK", 3);
                htd_dpi_execute_single_request(BUFF);               
	  	if(socket_read(BUFF)) { 
		  break;		 
		};
		/*printf("Accessing Server Server results\n");*/
		strncpy(BUFF_OUT, htd_get_dpi_result(),sizeof(BUFF_OUT)-1);
                /*printf("Server to socket msg-%s\n",BUFF_OUT);*/
		write(htd_hpl_socket,BUFF_OUT, strlen(BUFF_OUT));
                /*printf("Server to socket msg Sent -%s\n",BUFF_OUT);*/
	      }
	    }
	    close(htd_hpl_socket);
	    sleep(1);
	    /*--Remove server boot file --*/
	    if( access( server_status_file , F_OK ) != -1 ){
	      remove(server_status_file);	
	    } 
	    return;
/*	  };*/
/*  
} else{
       //--- fork failed ---
        perror("fork() failed!\n");
        return;
   };*/
}

int find_substr(char* input_str, char* substr)
{
  int pos;
  /*printf("input_str is: %s\n",input_str);
  printf("substr is: %s\n", substr);
  printf("found string is: %s\n", strstr(input_str, substr));*/
  pos = (int)(strstr(input_str,substr) - input_str);
  return pos;
}

char* get_envvar (char* varname)
{
  char* value = getenv(varname);
  printf ("In htd_unix_socket_server - %s = %s.\n", varname, value);
  return value;
}
int envvar_defined(char* varname)
{
   printf ("In htd_unix_socket_server - checking if envvar [%s] defined\n", varname);
   if(getenv(varname)!=NULL){
       return 1;
   } else {
       printf ("In htd_unix_socket_server - envvar [%s] is not defined\n", varname);
       return 0;
   }
}


/* must get full path */
int file_exists(char* filename)
{
   printf ("In htd_unix_socket_server - checking if file [%s] exists\n", filename);
   if( access( filename, F_OK ) != -1 ) {
       printf ("In htd_unix_socket_server - file [%s] exists\n", filename);
       return 1;
   } else {
       printf ("In htd_unix_socket_server - file [%s] does not exist\n", filename);
       return 0;
   }
}


/*GetArgVal_DPI( const char */
/*This function reads an environment variable (envvar) and seraches for an argument: argtofind */
/* If envar isn't found, it returns NULL. If argtofind isn't found, it returns NULL*/ 
const char* GetArgVal_DPI(const char *envvar, const char *argtofind)
{
    char *commandline=NULL;
    char *argvalue=NULL;
  /*Read the environment-string: envvar. (will be mostly: TEST_CMDLINE) */
    commandline= getenv(envvar);
  /* If envvar is NULL, return NULL. */
    if (commandline == NULL){
        return NULL;
    }
  /*modelvalue holds "-model <value> ... <End-Of-command-line>"*/
    commandline = strstr(commandline,argtofind);
    if(commandline == NULL){
        return (NULL);
    }
    /*printf("after strstr: %s\n", commandline); */
    argvalue = strtok(commandline," "); /*pointsto -model*/
    /*printf("modelvalue points to %s\n", modelvalue); */
    argvalue = strtok(NULL, " ");       /*Now points to <model-value>*/
    /*printf( "Now modelvalue points to %s\n", modelvalue); */
    return (argvalue);
}

void dpi_server(const char *serverName){
        char     serverrecv_arr[BUFFSIZE];
        char     serversend_arr[BUFFSIZE];
        char    *socket_path ="./dpisocket";
	struct   sockaddr_un addr;
	int 	 fd, fd_current, j;


        for(j=0;j<BUFFSIZE;j++){
            serverrecv_arr[j] = '\0';                                         
            serversend_arr[j] = '\0';
        }
        
	/* SERVER: try to get a UNIX  domain socket */
	if ((fd = socket(AF_UNIX, SOCK_STREAM, 0)) == -1) {
		perror("socket Error");
		exit(1);
	}

	/* SERVER: completes the socket structure */
	memset(&addr, 0, sizeof(addr));
        addr.sun_family = AF_UNIX;
        strncpy(addr.sun_path, socket_path, sizeof(addr.sun_path));

	/* SERVER: bind the socket to the port number */
        /* Unlink socket if exist */
        unlink(socket_path);
	if (bind(fd, (struct sockaddr *) &addr, sizeof(addr)) == -1) {
		perror("bind error");
		exit(1);
	}

        /* SERVER: Listen */
	if (listen(fd, 5) == -1) {
		perror("listen Error");
		exit(1);
	}


	if ((fd_current = accept(fd, NULL, NULL)) == -1) {
		perror("accept error");
		exit(1);
	}

        while(1){
	          
	          if (read(fd_current, serverrecv_arr, sizeof(serverrecv_arr)) == -1) {
		           perror("read error");
		           exit(1);
	          }
                /*Call The SVTB module:  send the command-line that the server has recieved*/
                  htd_dpi_execute_single_request(serverrecv_arr); 
                /*Read the result of this command execution in the SVTB and Copy the resulted-string returned by htd_get_dpi_result() */  
                  strcpy( serversend_arr, (char*)htd_get_dpi_result());
                /*Send the result back to client using  htd_get_dpi_results()*/
	          if (write(fd_current, serversend_arr, strlen(serversend_arr)) == -1) {
		           perror("Write Error");
		           exit(1);
	          }


                 /* printf("SERVER: Response message %s\n", "OK");
	          printf("SERVER: acknowledge the message, reply with OK\n");
	          if (send(sd_current, "OK", strlen("OK"), 0) == -1) {
		           perror("send");
		           exit(1);
	          }*/
                 /*close socket If End-Of-Transmition */
                  if(strcmp("HTD_CLOSE_SERVER\n\0",serverrecv_arr)==0){
                             printf("SERVER: close up both sockets\n");
	                     close(fd_current); close(fd);
                             printf("SERVER: give client a chance to properly shutdown\n");
                             sleep(2);
	                     printf("SERVER: Finish!\n");
                             close(fd_current);
                             close(fd);
                             return;
                  }
                 /*reset buffers arrays to '\0' */
                  for(j=0;j<BUFFSIZE;j++){
                      serversend_arr[j] = '\0';                                         
                      serverrecv_arr[j] = '\0';
                  }
          }
}/*End dpi_server*/
