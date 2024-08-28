#include <stdio.h>
#include <unistd.h>

int main(int argc, char* argv[]) {
    FILE* fp = fopen("/home/xa/JudgeHost/log/log.txt", "a+");
    for(int i=0; i<argc; i++) {
        printf("%s\n", argv[i]);
    }
    fclose(fp);
    return 0;
}

