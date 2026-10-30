#include <stdio.h> 
#include <sys/types.h> 
#include <unistd.h>  
#include <stdlib.h>  
#include <sys/wait.h> 
#include <string.h> 
#include <time.h> 
#include <signal.h>
#include <sys/time.h>

//SJF implementation

/************************************************************************************************ 
		These DEFINE statements represent the workload size of each task and 
		the time quantum values for Round Robin scheduling for each task.
*************************************************************************************************/

#define WORKLOAD1 100000
#define WORKLOAD2 50000
#define WORKLOAD3 25000
#define WORKLOAD4 10000

/*
#define QUANTUM1 1000
#define QUANTUM2 1000
#define QUANTUM3 1000
#define QUANTUM4 1000
*/
/************************************************************************************************ 
					DO NOT CHANGE THE FUNCTION IMPLEMENTATION
*************************************************************************************************/
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
/************************************************************************************************/
struct job{
	pid_t pid;
	int workload;
	long response_time;
	long turnaround_time;
	long exec_time;
	int id;
};

int compare_jobs(const void *a, const void *b){
	const struct job *ja = (const struct job *)a;
	const struct job *jb = (const struct job *)b;
	return ja->workload - jb->workload;
}

long elapsed_us(struct timeval a, struct timeval b){
	return (a.tv_sec-b.tv_sec) * 1000000L + (a.tv_usec - b.tv_usec);
}

int main(int argc, char const *argv[])
{
	struct timeval t0, now, done, prev_done;
	struct job jobs[4]; 
	long overhead_us = 0;
	
	//saving workloads to jobs array and setting id's
	jobs[0].workload = WORKLOAD1;
	jobs[0].id = 1;
	jobs[1].workload = WORKLOAD2;
	jobs[1].id = 2;
	jobs[2].workload = WORKLOAD3;
	jobs[2].id = 3;
	jobs[3].workload = WORKLOAD4;
	jobs[3].id = 4;

	if(argc >= 5){
		jobs[0].workload = atoi(argv[1]);
		jobs[1].workload = atoi(argv[2]);
		jobs[2].workload = atoi(argv[3]);
		jobs[3].workload = atoi(argv[4]);

	}

	jobs[0].pid = fork();

	if (jobs[0].pid == 0){

		myfunction(jobs[0].workload);

		exit(0);
	}
	kill(jobs[0].pid, SIGSTOP);

	jobs[1].pid = fork();

	if (jobs[1].pid == 0){

		myfunction(jobs[1].workload);

		exit(0);
	}
	kill(jobs[1].pid, SIGSTOP);

	jobs[2].pid = fork();

	if (jobs[2].pid == 0){

		myfunction(jobs[2].workload);

		exit(0);
	}
	kill(jobs[2].pid, SIGSTOP);

	jobs[3].pid = fork();

	if (jobs[3].pid == 0){

		myfunction(jobs[3].workload);

		exit(0);
	}
	kill(jobs[3].pid, SIGSTOP);

	/************************************************************************************************ 
		At this point, all  newly-created child processes are stopped, and ready for scheduling.
	*************************************************************************************************/



	/************************************************************************************************
		- Scheduling code starts here
		- SJF scheduler
	************************************************************************************************/

	//sorting jobs array in ascending order
	qsort(jobs, 4, sizeof(struct job), compare_jobs);

	gettimeofday(&t0, NULL);
	prev_done = t0;

	for(int i = 0; i < 4; i++){
		gettimeofday(&now, NULL);
		overhead_us += elapsed_us(now, prev_done);
		kill(jobs[i].pid, SIGCONT);
		waitpid(jobs[i].pid, NULL, 0);

		//getting done time
		gettimeofday(&done, NULL);
		//getting response time
		jobs[i].response_time = elapsed_us(now, t0);
		//calculating turnaround_time
		jobs[i].turnaround_time = elapsed_us(done, t0);
		//calculating exec_time
		jobs[i].exec_time = elapsed_us(done, now);

		prev_done = done;
	}

	/************************************************************************************************
		- Scheduling code ends here
	************************************************************************************************/

	//putting jobs back in original order (P1-P4) using id
	struct job by_id[4];
	for(int i = 0; i < 4; i++){
		by_id[jobs[i].id - 1] = jobs[i];
	}

	//calculating average response time and total time
	long sum_rt = 0;
	long total_us = 0;
	for(int i = 0; i < 4; i++){
		sum_rt += by_id[i].response_time;
		if(by_id[i].turnaround_time > total_us){
			total_us = by_id[i].turnaround_time;
		}
	}
	double avg_rt = sum_rt / 4.0;

	//printing csv row:
	//algo,quantum,w1-w4,rt1-rt4,avg_rt,tt1-tt4,et1-et4,total_us,switches,overhead_us
	printf("SJF,0");
	for(int i = 0; i < 4; i++){
		printf(",%d", by_id[i].workload);
	}
	for(int i = 0; i < 4; i++){
		printf(",%ld", by_id[i].response_time);
	}
	printf(",%.1f", avg_rt);
	for(int i = 0; i < 4; i++){
		printf(",%ld", by_id[i].turnaround_time);
	}
	for(int i = 0; i < 4; i++){
		printf(",%ld", by_id[i].exec_time);
	}
	printf(",%ld,%d,%ld\n", total_us, 4, overhead_us);

	return 0;
}

