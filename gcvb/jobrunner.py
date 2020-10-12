#! /usr/bin/env python3

import threading
import bisect
import random
import subprocess
import os
import sys
import glob
from . import util
from . import db
from . import job as gcvb_job
from . import yaml_input

exit_success = 0

class Job(object):
    def __init__(self, run_id, test_id, test_id_db, step, launch_command, num_process, num_threads, job_type):
        self.run_id = run_id
        self.test_id = test_id
        self.test_id_db = test_id_db
        self.step = step
        self.launch_command = launch_command
        self.num_process = int(num_process)
        self.num_threads = int(num_threads)
        self.type = job_type
        self.is_first = False
        self.is_last = False
        self.is_valid = False
        self.return_code = -1
    def num_cores(self):
        return self.num_process*self.num_threads
    def run(self):
        env = dict(os.environ)
        env["GCVB_RUN_ID"] = f"{self.run_id}"
        env["GCVB_TEST_ID"] = f"{self.test_id_db}"
        env["GCVB_STEP_ID"] = f"{self.step}"
        self.return_code = subprocess.call(self.launch_command, shell=True, cwd=self.test_id, env=env)
    def name(self):
        return f"{self.test_id}_{self.num_process}x{self.num_threads}_{self.type}"
    def __repr__(self):
        return self.name()

class JobRunner(object):
    def __init__(self, num_cores, run_id, config, started_first, max_concurrent, verbose, test_yaml=None):
        self.num_cores = num_cores
        self.running_tests = {}
        self.condition = threading.Condition()
        self.available_cores = num_cores
        self.lock = threading.Lock()
        self.started_first = started_first
        self.max_concurrent = max_concurrent # 0 means unlimited
        self.verbose = verbose
        self.keep = {}
        self.run_id = run_id
        self.base_id = db.get_base_from_run(run_id)
        computation_dir = f"./results/{self.base_id}"
        self.config = config

        # Generate job list
        if test_yaml is None:
            test_yaml = yaml_input.load_yaml(os.path.join(computation_dir,"tests.yaml"))
        test_informations = test_yaml["Tests"]
        tests_for_current_run = db.get_tests(self.run_id)

        data_root = test_yaml["data_root"]
        self.tests = {t["name"] : {} for t in tests_for_current_run}
        test_id_in_db = {t["name"] : t["id"] for t in tests_for_current_run}
        test_list = list(self.tests.keys())
        ref_valid = yaml_input.get_references([test_informations[n] for n in test_list],data_root)
        for test,tasks in self.tests.items():
            current_test = test_informations[test]
            if 'keep' in current_test:
                self.keep[current_test['id']] = current_test['keep']
            step = 0
            for c, task in enumerate(current_test["Tasks"]):
                step += 1
                at_job_creation = {}
                gcvb_job.fill_at_job_creation_task(at_job_creation, task, f"{current_test['id']}_{c}", self.config)
                launch_command = gcvb_job.format_launch_command(task["launch_command"],
                                                                self.config, at_job_creation)
                j=Job(self.run_id, test, test_id_in_db[test], step, launch_command,
                          at_job_creation["nprocs"], at_job_creation["nthreads"], "task")
                tasks[step] = j
                for d, val in enumerate(task.get("Validations",[])):
                    step += 1
                    gcvb_job.fill_at_job_creation_validation(at_job_creation, val,
                                                             data_root, current_test["data"], config, ref_valid)
                    launch_command = gcvb_job.format_launch_command(val["launch_command"],
                                                                    self.config, at_job_creation)
                    j = Job(self.run_id, test, test_id_in_db[test], step, launch_command,
                            at_job_creation["nprocs"], at_job_creation["nthreads"], "validation")
                    j.is_valid = True
                    tasks[step] = j
            tasks[1].is_first = True
            tasks[step].is_last = True


        # Go to the right directory
        os.chdir(computation_dir)
        # Then choose the right location for the db
        db.set_db(os.path.abspath("../../gcvb.db"))

    def _run_job(self, job):
        self.print(f"[{job.test_id}][Step {job.step}] Started")
        self.print(f"[{job.test_id}][Step {job.step}] cmd : {job.launch_command}")
        job.run()
        self.print(f"[{job.test_id}][Step {job.step}] Completed (return code : {job.return_code})")
        # A test is stopped only if a Task fails (Validation failures do not matter)
        stopped_by_error = job.return_code != exit_success if not(job.is_valid) else False
        with self.lock:
            self.available_cores += job.num_cores()
            del self.running_tests[(job.test_id,job.step)]

            conn = db.get_exclusive_access()
            with conn:
                cursor = conn.cursor()
                req = """UPDATE task
                         SET end_date = CURRENT_TIMESTAMP, status = ?
                         WHERE step = ? and test_id = ?"""
                cursor.execute(req, [job.return_code, job.step, job.test_id_db])
                if job.is_last or stopped_by_error:
                    req = """UPDATE test
                             SET end_date = CURRENT_TIMESTAMP
                             WHERE id = ? and run_id = ?"""
                    cursor.execute(req,[job.test_id_db,job.run_id])
                    self.print(f"[{job.test_id}] Completed (Last return code : {job.return_code})")
                if not(stopped_by_error):
                    # Children are now ready
                    req = """UPDATE task
                             SET status = -2
                             WHERE parent = ? and test_id = ?"""
                    cursor.execute(req,[job.step, job.test_id_db])
            conn.close()
        if job.is_last or stopped_by_error:
            self.__save_files(job)
        with self.condition:
            self.condition.notify()

    def __save_files(self, job):
        # Read and compress without locking the db
        tosave = []
        for pattern in self.keep[job.test_id]:
            for filename in glob.iglob(os.path.join(job.test_id, pattern)):
                content=util.file_to_compressed_binary(filename)
                tosave.append((os.path.basename(filename), content, job.test_id_db,))
        # Now lock the DB and save
        db.save_blobs(tosave)

    def run(self):
        """  Run all submited jobs and block until finished. """

        db.start_run(self.run_id)
        job = self._nextjob()
        while job is not None or len(self.running_tests) > 0:
            if job is None:
                with self.condition:
                    self.condition.wait()
            else:
                with self.lock:
                    self.available_cores -= job.num_cores()
                    t = threading.Thread(name = job.name(), target = lambda: self._run_job(job))
                    self.running_tests[(job.test_id,job.step)] = t
                t.start()
            job = self._nextjob()
        db.end_run(self.run_id)

    def elect_job(self, queue):
        """
        Choose a job to run. Hack this function to change the strategy.

        queue -- iterable of available jobs
        """
        queue = sorted(queue, key = lambda x: x.num_cores())
        if len(self.running_tests) == 0:
            # begin with a small job to detect errors early
            return queue[0] if len(queue) else None
        else:
            # fill large jobs first to avoid starvation at the end
            i = bisect.bisect([x.num_cores() for x in queue], self.available_cores) - 1
            return queue[i] if i >= 0 else None



    def _nextjob(self):
        with self.lock:
            # We don't take a job if we reached the max_concurrent limit
            if self.max_concurrent and self.max_concurrent <= len(self.running_tests):
                return None

            # if we take elect an unstarted job, we must mark it as started while the database is locked for us.
            # the elect process must be done with the lock on the database.
            conn = db.get_exclusive_access()
            with conn:
                cursor = conn.cursor()
                # Get ready tasks (status -2)
                req = """SELECT step, test_id, name FROM task
                         INNER JOIN test ON task.test_id=test.id
                         INNER JOIN run ON run.id = test.run_id
                         WHERE task.status = -2 AND run.id = ?"""
                cursor.execute(req,[self.run_id])
                available_jobs = [self.tests[test["name"]][test["step"]] for test in cursor.fetchall()]
                if (self.started_first):
                  available_started_jobs = [j for j in available_jobs if j.step!=1]
                  available_jobs = available_started_jobs if available_started_jobs else available_jobs
                to_be_run = self.elect_job(available_jobs)
                if to_be_run and to_be_run.is_first: #was elected from database
                    req = """UPDATE test SET start_date = CURRENT_TIMESTAMP
                             WHERE id = ? and run_id = ?"""
                    cursor.execute(req,[to_be_run.test_id_db,to_be_run.run_id])
                if to_be_run:
                    req = """UPDATE task
                             SET start_date = CURRENT_TIMESTAMP, status = -1
                             WHERE step = ? AND test_id = ?"""
                    cursor.execute(req,[to_be_run.step, to_be_run.test_id_db])
            conn.close()
            return to_be_run

    def print(self, *objects, sep=' ', end='\n', file=sys.stdout, flush=False):
        if self.verbose:
          print(*objects, sep=sep, end=end, file=file, flush=flush)
