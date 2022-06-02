#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/un.h> 
#include <sys/types.h>
#include <sys/socket.h>
#include <string.h>
#define PORT     0x1234
#define BUFFSIZE 4096


/* dpi_execute_single_request is an exported funtion, written in SV. */ 
/* extern char* htd_dpi_execute_single_request( const char* msg ); */
/* extern void htd_dpi_execute_single_request(const char* msg); */
/* extern char* htd_get_dpi_result(); */

int main(int argc, char **argv){
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
                /*htd_dpi_execute_single_request(serverrecv_arr); */
                  printf("call htd_dpi_execute_single_request() with %s\n", serverrecv_arr);
                /*Read the result of this command execution in the SVTB and Copy the resulted-string returned by htd_get_dpi_result() */  
                  strcpy( serversend_arr, "returned value from transactor for value\n ");
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
   return 0;
}/*End Main*/




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

