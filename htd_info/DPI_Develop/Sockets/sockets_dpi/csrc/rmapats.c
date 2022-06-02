#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include "rmapats.h"

scalar dummyScalar;
scalar fScalarIsForced=0;
scalar fScalarIsReleased=0;
scalar fScalarHasChanged=0;
scalar fForceFromNonRoot=0;
void  hsG_0(struct dummyq_struct * I893, EBLK  * I894, U  I666);
void  hsG_0(struct dummyq_struct * I893, EBLK  * I894, U  I666)
{
    U  I1097;
    U  I1098;
    U  I1099;
    struct futq * I1100;
    I1097 = ((U )vcs_clocks) + I666;
    I1099 = I1097 & 0xfff;
    I894->I599 = (EBLK  *)(-1);
    I894->I609 = I1097;
    if (I1097 < (U )vcs_clocks) {
        I1098 = ((U  *)&vcs_clocks)[1];
        sched_millenium(I893, I894, I1098 + 1, I1097);
    }
    else if ((peblkFutQ1Head != ((void *)0)) && (I666 == 1)) {
        I894->I610 = (struct eblk *)peblkFutQ1Tail;
        peblkFutQ1Tail->I599 = I894;
        peblkFutQ1Tail = I894;
    }
    else if ((I1100 = I893->I861[I1099].I616)) {
        I894->I610 = (struct eblk *)I1100->I615;
        I1100->I615->I599 = (RP )I894;
        I1100->I615 = (RmaEblk  *)I894;
    }
    else {
        sched_hsopt(I893, I894, I1097);
    }
}
U   hsG_1(U  I906);
#ifdef __cplusplus
extern "C" {
#endif
void SinitHsimPats(void);
#ifdef __cplusplus
}
#endif
