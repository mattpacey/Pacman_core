#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <stdio.h>
#include <dlfcn.h>
#include "svdpi.h"

#ifdef __cplusplus
extern "C" {
#endif

#ifndef _VC_TYPES_
#define _VC_TYPES_
/* common definitions shared with DirectC.h */

typedef unsigned int U;
typedef unsigned char UB;
typedef unsigned char scalar;
typedef struct { U c; U d;} vec32;

#define scalar_0 0
#define scalar_1 1
#define scalar_z 2
#define scalar_x 3

extern long long int ConvUP2LLI(U* a);
extern void ConvLLI2UP(long long int a1, U* a2);
extern long long int GetLLIresult();
extern void StoreLLIresult(const unsigned int* data);
typedef struct VeriC_Descriptor *vc_handle;

#ifndef SV_3_COMPATIBILITY
#define SV_STRING const char*
#else
#define SV_STRING char*
#endif

#endif /* _VC_TYPES_ */


 extern void htd_start_server(/* INPUT */const char* serverName);

 extern void htd_simple_server(/* INPUT */const char* serverName, /* INPUT */const char* socketFile);

 extern int find_substr(/* INPUT */const char* input_line, /* INPUT */const char* substr);

 extern SV_STRING htd_get_dpi_result();

 extern void htd_dpi_execute_single_request(/* INPUT */const char* msg);

#ifdef __cplusplus
}
#endif

