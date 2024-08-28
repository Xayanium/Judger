#include <stdio.h>

int tmp[10000000];

int add(int a, int b) {
    return a + b;
}

int main() {
    int a, b;
//    for(int i=1; i<=10000000; i++)
//        tmp[i]=i;

    for(int i=1; i<=1000000; i++) {
//        for(int j=1; j<=1000; j++) {
//            for(int k=1; k<=1; j++) {
//                count++;
//            }
//        }
        count++;
    }
    scanf("%d%d", &a, &b);
    printf("%d", add(a, b));
    return 0;
}

