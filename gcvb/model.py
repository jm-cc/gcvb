from enum import IntEnum
from . import db
from . import yaml_input

class JobStatus(IntEnum):
    unlinked = -4
    pending = -3
    ready = -2
    running = -1
    exit_success = 0

class AbsoluteMetric:
    def __init__(self, reference, tolerance, unit = None):
        self.type = "absolute"
        self.reference = reference
        self.tolerance = tolerance
        self.unit = unit
    def within_tolerance(self, value):
        return abs(value - self.reference) <= self.tolerance

class RelativeMetric:
    def __init__(self, reference, tolerance):
        self.type = "relative"
        self.reference = reference
        self.tolerance = tolerance
    def within_tolerance(self, value):
        return (abs(value - self.reference) / self.reference) <= self.tolerance

class Validation:
    default_type = "relative"
    default_reference = None
    def __init__(self, valid_dict, config):
        self.raw_dict = valid_dict
        self.status = JobStatus.unlinked
        self.executable = valid_dict["executable"]
        self.type = valid_dict["type"]
        self.launch_command = valid_dict["launch_command"]
        self.recorded_metrics = {}
        self.init_metrics(config)

    def init_metrics(self, config):
        self.expected_metrics = {}
        for metric in self.raw_dict.get("Metrics", []):
            t = metric.get("type", self.default_type)
            if t not in ["relative", "absolute"]:
                raise ValueError("'type' must be 'relative' or 'absolute'.")
            #reference is either a dict or a number.
            ref = metric.get("reference", self.default_reference)
            if ref is None:
                raise ValueError("'reference' must be provided.")
            if isinstance(ref, dict):
                if config in ref:
                    if t == "relative":
                        self.expected_metrics[metric["id"]] = RelativeMetric(ref[config], metric["tolerance"])
                    else:
                        self.expected_metrics[metric["id"]] = AbsoluteMetric(ref[config], metric["tolerance"])
            else:
                if t == "relative":
                    self.expected_metrics[metric["id"]] = RelativeMetric(ref, metric["tolerance"])
                else:
                    self.expected_metrics[metric["id"]] = AbsoluteMetric(ref, metric["tolerance"])

    @property
    def missing_metrics(self):
        e_m = set(self.expected_metrics.keys())
        r_m = set(self.recorded_metrics.keys())
        if e_m.intersection(r_m) == e_m:
            return False
        return True

    @property
    def success(self):
        if self.missing_metrics:
            return False
        for metric_id, metric in self.expected_metrics.items():
            if not metric.within_tolerance(self.recorded_metrics[metric_id]):
                return False
        return True

class FileComparisonValidation(Validation):
    default_type = "absolute"
    default_reference = 0

class Task():
    def __init__(self, task_dict, config):
        self.raw_dict = task_dict
        self.status = JobStatus.unlinked
        self.exectuable = task_dict["executable"]
        self.options = task_dict.get("options", '')
        self.launch_command = task_dict["launch_command"]
        self.nprocs = task_dict["nprocs"]
        self.nthreads = task_dict["nthreads"]
        # Validations
        self.Validations = []
        for v in task_dict.get("Validations", []):
            if v["type"] == "script":
                self.Validations.append(Validation(v, config))
            else:
                self.Validations.append(FileComparisonValidation(v, config))

class Test():
    def __init__(self, test_dict, config, name=None, start_date=None, end_date=None):
        self.raw_dict = test_dict
        # Tasks
        self.Tasks = []
        for t in test_dict.get("Tasks"):
            self.Tasks.append(Task(t, config))
        # Steps
        self.Steps = []
        for t in self.Tasks:
            self.Steps.append(t)
            for v in t.Validations:
                self.Steps.append(v)
        # Infos
        self.name = name
        self.start_date = start_date
        self.end_date = end_date

    def __repr__(self):
        return f"{{id : {self.name}, status : TODO}}"

class Run():
    def __test_db_to_objects(self):
        self.db_tests = db.get_tests(self.run_id)
        self.gcvb_base = yaml_input.load_yaml_from_run(self.run_id)
        b = self.gcvb_base["Tests"]
        self.Tests = {t["name"] : Test(b[t["name"]], self.config, t["name"], t["start_date"], t["end_date"]) for t in self.db_tests}
        # Fill infos for every step
        recorded_metrics = db.load_report_n(self.run_id)
        step_info = db.get_steps(self.run_id)
        for test_id, test in self.Tests.items():
            for step, metrics in recorded_metrics[test_id].items():
                test.Steps[step-1].recorded_metrics = metrics
            for step, step_info in step_info[test_id].items():
                test.Steps[step-1].start_date = step_info["start_date"]
                test.Steps[step-1].end_date = step_info["end_date"]
                test.Steps[step-1].status = step_info["status"]

    def __init__(self, run_id):
        self.run_id = run_id

        run_infos = db.get_run_infos(run_id)
        self.start_date = run_infos["start_date"]
        self.end_date = run_infos["end_date"]
        self.config = run_infos["config_id"]
        self.gcvb_id = run_infos["gcvb_id"]

        self.__test_db_to_objects()
