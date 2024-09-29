#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <string.h>

int main() {
    // 设置项目路径
    const char *project_dir = "MyProject";

    // 构建完整路径
    char java_path[256];
    snprintf(java_path, sizeof(java_path), "/usr/bin/java");

    char class_path[256];
    snprintf(class_path, sizeof(class_path), "/home/xa/PycharmProjects/Judger/tmp");

    char* environ[] = {"PATH=/bin", NULL};

    char *args[] = {
        "/usr/bin/java",         // java 命令的路径
        "-cp",             // class path 参数
        "/home/xa/PycharmProjects/Judger/tmp",        // class path 的值
        "Mai",            // 主类名
        NULL               // 参数列表结束标志
    };

    // 创建子进程
    pid_t pid = fork();

    if (pid == -1) {
        perror("Fork failed");
        exit(EXIT_FAILURE);
    }

    if (pid == 0) {
	FILE* input_file = NULL;
	input_file = fopen("/home/xa/PycharmProjects/Judger/tmp/input.txt", "r");
	dup2(fileno(input_file), STDIN_FILENO);
        // 子进程执行 execve
        if (execve(args[0], args, environ) == -1) {
            perror("execve");
            _exit(EXIT_FAILURE);
        }
    } else {
        // 父进程等待子进程结束
        int status;
        waitpid(pid, &status, 0);
        if (WIFEXITED(status) && WEXITSTATUS(status) != 0) {
            fprintf(stderr, "Java execution failed with status %d\n", WEXITSTATUS(status));
            exit(EXIT_FAILURE);
        } else if(WIFSIGNALED(status)) {
	    if(WTERMSIG(status) == SIGSEGV) {
	        printf("SEGMENTATION_FAULT");
	    }
	    printf("haha\n");
	}
        printf("Java code executed successfully.\n");
    }

    return 0;
}
