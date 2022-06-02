#include <sys/socket.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <signal.h>
void htd_dpi_execute_single_request(const char* msg) {
    printf ("DEBUG:!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Server:Got a request data:%s\n",msg);
};
char* htd_get_dpi_result() {
    return "Response Done"; 
};
int main()
{
  htd_start_server("DpiSimServer",1);

};
