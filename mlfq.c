#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define WORKLOAD1 100000
#define WORKLOAD2 50000
#define WORKLOAD3 25000
#define WORKLOAD4 10000
#define JOBS 4

/* Original workload function: implementation unchanged. */
void myfunction(int param){

	int i = 2;
	int j, k;

	while(i < param){
		k = i;
		for (j = 2; j <= k; j++)
		{
			if (k % j == 0){
				k = k/j;
				j--;
				if (k == 1){
					break;
				}
			}
		}

		i++;
	}
}

struct job {
    pid_t pid;
    int workload;
    long response_time;
    long turnaround_time;
    long exec_time;
    int finished;
};

static struct job jobs[JOBS];

/* Reap/stop only children belonging to this program after an error. */
static void fail(const char *message)
{
    perror(message);
    for (int i = 0; i < JOBS; i++) {
        if (jobs[i].pid > 0 && !jobs[i].finished) {
            kill(jobs[i].pid, SIGKILL);
            while (waitpid(jobs[i].pid, NULL, 0) < 0 && errno == EINTR) {}
        }
    }
    exit(EXIT_FAILURE);
}

static long now_us(void)
{
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t) < 0)
        fail("clock_gettime");
    return (long)t.tv_sec * 1000000L + t.tv_nsec / 1000;
}

static void sleep_us(long duration)
{
    struct timespec delay = {duration / 1000000L,
                             (duration % 1000000L) * 1000L};
    while (nanosleep(&delay, &delay) < 0) {
        if (errno != EINTR)
            fail("nanosleep");
    }
}

static pid_t wait_for(pid_t pid, int *status, int options)
{
    pid_t result;
    do {
        result = waitpid(pid, status, options);
    } while (result < 0 && errno == EINTR);
    if (result < 0)
        fail("waitpid");
    return result;
}

static int positive_integer(const char *text)
{
    char *end;
    errno = 0;
    long value = strtol(text, &end, 10);
    if (errno || end == text || *end || value <= 0 || value > INT_MAX) {
        fprintf(stderr, "Invalid positive integer: %s\n", text);
        exit(EXIT_FAILURE);
    }
    return (int)value;
}

static void record_finish(int i, int status, long start, long t0)
{
    long end = now_us();
    jobs[i].finished = 1;
    jobs[i].exec_time += end - start;
    jobs[i].turnaround_time = end - t0;
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        fprintf(stderr, "Process P%d did not finish successfully.\n", i + 1);
        errno = ECHILD;
        fail("child process");
    }
}

int main(int argc, char **argv)
{
    if (argc != 1 && argc != 2 && argc != 6) {
        fprintf(stderr, "Usage: %s [quantum_us [w1 w2 w3 w4]]\n", argv[0]);
        return EXIT_FAILURE;
    }

    int quantum = argc >= 2 ? positive_integer(argv[1]) : 1000;
    int workloads[JOBS] = {WORKLOAD1, WORKLOAD2, WORKLOAD3, WORKLOAD4};
    for (int i = 0; i < JOBS; i++)
        jobs[i].workload = argc == 6 ? positive_integer(argv[i + 2]) : workloads[i];

    /* Each child stops BEFORE starting its workload. */
    for (int i = 0; i < JOBS; i++) {
        pid_t pid = fork();
        if (pid < 0)
            fail("fork");
        if (pid == 0) {
            if (raise(SIGSTOP) != 0)
                _exit(EXIT_FAILURE);
            myfunction(jobs[i].workload);
            _exit(EXIT_SUCCESS);
        }
        jobs[i].pid = pid;
        int status;
        wait_for(pid, &status, WUNTRACED);
        if (!WIFSTOPPED(status)) {
            jobs[i].finished = 1;
            errno = ECHILD;
            fail("child failed to stop");
        }
    }

    long t0 = now_us();
    long previous_stop = t0;
    long overhead_us = 0;
    int dispatches = 0;

    /* Queue 1: one RR quantum per process, in creation order.
       Timed the same way as rr.c: SIGCONT, sleep the full quantum, SIGSTOP,
       then check without blocking whether the process exited during its slice. */
    for (int i = 0; i < JOBS; i++) {
        long start = now_us();
        overhead_us += start - previous_stop;
        jobs[i].response_time = start - t0;
        if (kill(jobs[i].pid, SIGCONT) < 0)
            fail("SIGCONT");
        sleep_us(quantum);
        if (kill(jobs[i].pid, SIGSTOP) < 0 && errno != ESRCH)
            fail("SIGSTOP");
        dispatches++;

        int status;
        if (wait_for(jobs[i].pid, &status, WNOHANG) == jobs[i].pid)
            record_finish(i, status, start, t0);
        else
            jobs[i].exec_time += now_us() - start;
        previous_stop = now_us();
    }

    /* Queue 2: unfinished jobs run to completion, FCFS, with no promotion. */
    for (int i = 0; i < JOBS; i++) {
        if (jobs[i].finished)
            continue;
        long start = now_us();
        overhead_us += start - previous_stop;
        if (kill(jobs[i].pid, SIGCONT) < 0)
            fail("SIGCONT");
        dispatches++;
        int status;
        wait_for(jobs[i].pid, &status, 0);
        record_finish(i, status, start, t0);
        previous_stop = now_us();
    }

    long sum_rt = 0;
    long total_us = 0;
    for (int i = 0; i < JOBS; i++) {
        sum_rt += jobs[i].response_time;
        if (jobs[i].turnaround_time > total_us)
            total_us = jobs[i].turnaround_time;
    }

    /* Same column order as rr.c; one CSV row per run. */
    printf("MLFQ,%d", quantum);
    for (int i = 0; i < JOBS; i++) printf(",%d", jobs[i].workload);
    for (int i = 0; i < JOBS; i++) printf(",%ld", jobs[i].response_time);
    printf(",%.1f", sum_rt / 4.0);
    for (int i = 0; i < JOBS; i++) printf(",%ld", jobs[i].turnaround_time);
    for (int i = 0; i < JOBS; i++) printf(",%ld", jobs[i].exec_time);
    printf(",%ld,%d,%ld\n", total_us, dispatches, overhead_us);
    return EXIT_SUCCESS;
}
