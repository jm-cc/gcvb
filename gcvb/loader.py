import gcvb.yaml_input as yaml_input
import gcvb.db as db
import gcvb.job as job
from collections import defaultdict



class BaseLoader(object):
    def __init__(self):
        self.data_root = "./data"
        self.config = {"executables" : {}}
        self.loaded = {}
        self.references = {}
        self.allowed_files = {}
    def load_base(self, run_id):
        ya,mod = db.retrieve_input(run_id)
        base = db.get_base_from_run(run_id)
        if (ya,mod) not in self.loaded:
            self.loaded[(ya,mod)] = yaml_input.load_yaml(ya,mod)
            refs = yaml_input.get_references(self.loaded[(ya,mod)]["Tests"].values(),self.data_root)
            self.references.update(refs)
        if base not in self.allowed_files:
            self.allowed_files[base] = self.__populate_allowed_files(ya, mod)
        return self.loaded[(ya,mod)]

    def __populate_one_allowed(self, taskorval, allowedentry, at_job_creation):
        lr = taskorval.get("serve_from_results",[])
        ldb = taskorval.get("serve_from_db",[])
        for f in lr + ldb:
            filename = job.format_launch_command(f["file"], self.config, at_job_creation)
            allowedentry[filename] = f

    def __populate_allowed_files(self, ya, mod):
        s = defaultdict(dict)
        for test_id,test in self.loaded[(ya,mod)]["Tests"].items():
            for c,task in enumerate(test["Tasks"]):
                at_job_creation = {}
                job.fill_at_job_creation_task(at_job_creation, task, f"{test_id}_{c}", self.config)
                self.__populate_one_allowed(task, s[test_id], at_job_creation)
                for valid in task.get("Validations",[]):
                    job.fill_at_job_creation_validation(at_job_creation, valid, self.data_root,
                                                        test["data"], self.config, self.references)
                    self.__populate_one_allowed(valid, s[test_id], at_job_creation)
        return s

loader = BaseLoader()
