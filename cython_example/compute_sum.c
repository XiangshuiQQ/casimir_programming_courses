#include <math.h>
    
double compute_sum_c(double *arr, int N)
{
    double result = 0;
    int i;
    
    for(i = 0; i < N; i++) {
        result += arr[i] * arr[i];
    }
    
    return result;
}