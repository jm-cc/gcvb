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

    def __populate_allowed_files(self, ya, mod):
        s = defaultdict(dict)
        for test_id,test in self.loaded[(ya,mod)]["Tests"].items():
            for c,task in enumerate(test["Tasks"]):
                at_job_creation = {}
                job.fill_at_job_creation_task(at_job_creation, task, f"{test_id}_{c}", self.config)
                for file in task.get("serve_from_results",[]):
                    filename = job.format_launch_command(file["file"], self.config, at_job_creation)
                    s[test_id][filename] = file
                for valid in task.get("Validations",[]):
                    job.fill_at_job_creation_validation(at_job_creation, valid, self.data_root,
                                                        test["data"], self.config, self.references)
                    for file in valid.get("serve_from_results",[]):
                        filename = job.format_launch_command(file["file"], self.config, at_job_creation)
                        s[test_id][filename] = file
        return s

loader = BaseLoader()
