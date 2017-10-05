
#ifdef ENABLE_SGX
#include <stdio.h>
extern "C" {
void ocall_print(const char *str) {
    printf("%s",str);
}
}
#endif

int main() {

}

