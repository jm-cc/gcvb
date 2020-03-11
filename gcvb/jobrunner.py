#! /usr/bin/env python3

import threading
import bisect
import random
import subprocess
import os
from . import db
from . import job as gcvb_job
from . import yaml_input

class Job(object):
    def __init__(self, run_id, test_id, test_id_db, launch_command, num_process, num_threads, job_type):
        self.run_id = run_id
        self.test_id = test_id
        self.test_id_db = test_id_db
        self.launch_command = launch_command
        self.num_process = int(num_process)
        self.num_threads = int(num_threads)
        self.type = job_type
        self.is_first = False
        self.is_last = False
    def num_cores(self):
        return self.num_process*self.num_threads
    def run(self):
        env = dict(os.environ)
        env["GCVB_RUN_ID"] = f"{self.run_id}"
        env["GCVB_TEST_ID"] = f"{self.test_id_db}"
        return subprocess.call(self.launch_command, shell=True, cwd=self.test_id, env=env)
    def name(self):
        return f"{self.test_id}_{self.num_process}x{self.num_threads}_{self.type}"
    def __repr__(self):
        return self.name()

class JobRunner(object):
    def __init__(self, num_cores, run_id, config):
        self.num_cores = num_cores
        self.running_tests = {}
        self.condition = threading.Condition()
        self.available_cores = num_cores
        self.lock = threading.Lock()

        self.run_id = run_id
        self.base_id = db.get_base_from_run(run_id)
        computation_dir = f"./results/{self.base_id}"
        self.config = config

        # Generate job list
        tmp = yaml_input.load_yaml(os.path.join(computation_dir,"tests.yaml"))
        test_informations = tmp["Tests"]
        tests_for_current_run = db.get_tests(self.run_id)

        data_root = tmp["data_root"]
        self.tests = {t["name"] : [] for t in tests_for_current_run}
        test_id_in_db = {t["name"] : t["id"] for t in tests_for_current_run}
        test_list = list(self.tests.keys())
        ref_valid = yaml_input.get_references([test_informations[n] for n in test_list],data_root)
        for test,l in self.tests.items():
            current_test = test_informations[test]
            for c, task in enumerate(current_test["Tasks"]):
                at_job_creation = {}
                gcvb_job.fill_at_job_creation_task(at_job_creation, task, f"{current_test['id']}_{c}", self.config)
                launch_command = gcvb_job.format_launch_command(task["launch_command"],
                                                                self.config, at_job_creation)
                j=Job(self.run_id, test, test_id_in_db[test], launch_command,
                          at_job_creation["nprocs"], at_job_creation["nthreads"], "task")
                l.append(j)
                for d, val in enumerate(task.get("Validations",[])):
                    gcvb_job.fill_at_job_creation_validation(at_job_creation, val,
                                                             data_root, current_test["data"], config, ref_valid)
                    launch_command = gcvb_job.format_launch_command(val["launch_command"],
                                                                    self.config, at_job_creation)
                    j = Job(self.run_id, test, test_id_in_db[test], launch_command,
                            at_job_creation["nprocs"], at_job_creation["nthreads"], "validation")
                    l.append(j)
            l[0].is_first = True
            l[-1].is_last = True

        self.started_locally = set()
        self.failed_tests = set() # set of tests for which at least one task returned something else than sys.EX_OK

        # Go to the right directory
        os.chdir(computation_dir)
        # Then choose the right location for the db
        db.set_db(os.path.abspath("../../gcvb.db"))

    def _run_job(self, job):
        return_code = job.run()
        with self.lock:
            self.available_cores += job.num_cores()
            del self.running_tests[job.test_id]
            if job.is_last or return_code!=os.EX_OK:
                conn = db.get_exclusive_access()
                with conn:
                    cursor = conn.cursor()
                    req = """UPDATE test SET end_date = CURRENT_TIMESTAMP
                             WHERE id = ? and run_id = ?"""
                    cursor.execute(req,[job.test_id_db,job.run_id])
                conn.close()
            if return_code!=os.EX_OK:
                self.failed_tests.add(job.test_id)
        with self.condition:
            self.condition.notify()

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
                    self.tests[job.test_id].pop(0)
                    self.available_cores -= job.num_cores()
                    t = threading.Thread(name = job.name(), target = lambda: self._run_job(job))
                    self.running_tests[job.test_id] = t
                    self.started_locally.add(job.test_id)
                t.start()
            job = self._nextjob()
        db.end_run(self.run_id)

    def elect_job(self, queue):
        """
        Choose a job to run. Hack this funciton to change the strategy.

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
            # Queue of ready jobs
            local_and_ready = [self.tests[test][0] for test in self.started_locally
                                                   if self.tests[test] and
                                                   test not in self.running_tests and
                                                   test not in self.failed_tests]

            # if we take elect an unstarted job, we must mark it as started while the database is locked for us.
            # the elect process must be done with the lock on the database.
            conn = db.get_exclusive_access()
            with conn:
                cursor = conn.cursor()
                req = """SELECT * FROM test
                         WHERE run_id = ?
                           AND start_date IS NULL"""
                cursor.execute(req,[self.run_id])
                available_from_db = [self.tests[test["name"]][0] for test in cursor.fetchall() if self.tests[test["name"]]]
                available_jobs = local_and_ready+available_from_db
                to_be_run = self.elect_job(available_jobs)
                if to_be_run and to_be_run.is_first: #was elected from database
                    req = """UPDATE test SET start_date = CURRENT_TIMESTAMP
                             WHERE id = ? and run_id = ?"""
                    cursor.execute(req,[to_be_run.test_id_db,to_be_run.run_id])
            conn.close()
            return to_be_run
