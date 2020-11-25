from enum import IntEnum
from . import db
from .loader import loader as loader
import datetime

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
    def distance(self, value):
        return abs(value - self.reference)
    def within_tolerance(self, value):
        return self.distance(value) <= self.tolerance

class RelativeMetric:
    def __init__(self, reference, tolerance):
        self.type = "relative"
        self.reference = reference
        self.tolerance = tolerance
    def distance(self, value):
        return (abs(value - self.reference) / self.reference)
    def within_tolerance(self, value):
        return self.distance(value) <= self.tolerance

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
        self.start_date = None
        self.end_date = None

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

    def get_missing_metrics(self):
        e_m = set(self.expected_metrics.keys())
        r_m = set(self.recorded_metrics.keys())
        return e_m.difference(r_m)

    def get_untracked_metrics(self):
        e_m = set(self.expected_metrics.keys())
        r_m = set(self.recorded_metrics.keys())
        return {m : self.recorded_metrics[m] for m in r_m.difference(e_m)}

    def get_out_of_tolerance_metrics(self):
        res = []
        for k,v in self.recorded_metrics.items():
            if k in self.expected_metrics:
                if not(self.expected_metrics[k].within_tolerance(v)):
                    res.append((k, self.expected_metrics[k], v))
        return res

    @property
    def missing_metrics(self):
        return bool(self.get_missing_metrics())

    @property
    def success(self):
        if self.missing_metrics:
            return False
        for metric_id, metric in self.expected_metrics.items():
            if not metric.within_tolerance(self.recorded_metrics[metric_id]):
                return False
        return True

    @property
    def elapsed(self):
        return self.end_date-self.start_date

class FileComparisonValidation(Validation):
    default_type = "absolute"
    default_reference = 0

class Task():
    def __init__(self, task_dict, config):
        self.raw_dict = task_dict
        self.status = JobStatus.unlinked
        self.executable = task_dict["executable"]
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
        self.start_date = None
        self.end_date = None

    @property
    def completed(self):
        return bool(self.end_date)

    @property
    def success(self):
        if not self.completed:
            return False
        if self.status != JobStatus.exit_success:
            return False
        return all([v.success for v in self.Validations])

    @property
    def elapsed(self):
        return self.end_date-self.start_date

    def get_failures(self):
        res = []
        if self.completed:
            if self.status > JobStatus.exit_success:
                res.append(ExitFailure(self.executable, self.status))
            # Missing metric is a failure only if the task is completed
            for v in self.Validations:
                missing = v.get_missing_metrics()
                for mm in missing:
                    res.append(MissingMetric(mm))
        for v in self.Validations:
            oot = v.get_out_of_tolerance_metrics()
            for m_id,m,v in oot:
                res.append(OutOfTolerance(m_id,m,v))
        return res

    def hr_result(self):
        # returns a string representing the first failure
        f = self.get_failures()
        if f:
            return f[0].hr_result()
        return "Success"

    def hr_elapsed(self):
        if self.completed:
            return str(self.elapsed)
        return "DNF" #Did not finish

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

    @property
    def completed(self):
        return bool(self.end_date)

    @property
    def success(self):
        return all([t.success for t in self.Tasks])

    @property
    def failed(self):
        #failed if a completed task failed.
        return any([bool(t.get_failures()) for t in self.Tasks if t.completed])

    @property
    def elapsed(self):
        return self.end_date-self.start_date

    def __repr__(self):
        return f"{{id : {self.name}, status : TODO}}"

    def get_failures(self):
        return [t.get_failures() for t in self.Tasks]

    def hr_result(self):
        if not(self.completed):
            return "Not completed yet"
        failures = self.get_failures()
        for k,f in enumerate(failures, 1):
            if f:
                return f"Step {k} : {f[0].hr_result()}"
        return "Success"

    def cpu_time(self):
        ct = 0
        for task in self.Tasks:
            if task.completed:
                ct += task.elapsed.total_seconds() * task.nthreads * task.nprocs
            else:
                return float('inf')
        return ct

def _strtotimestamp(s):
    # for backward compatibility with previous database format
    if isinstance(s, str):
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    else:
        return s

class Run():
    def __test_db_to_objects(self):
        self.db_tests = db.get_tests(self.run_id)
        self.base_id = db.get_base_from_run(self.run_id)
        self.gcvb_base = loader.load_base(self.run_id)
        self.references = loader.references
        b = self.gcvb_base["Tests"]
        self.Tests = {t["name"] : Test(b[t["name"]], self.config, t["name"], t["start_date"], t["end_date"]) for t in self.db_tests}
        # Fill infos for every step
        recorded_metrics = db.load_report_n(self.run_id)
        steps = db.get_steps(self.run_id)
        for test_id, test in self.Tests.items():
            for step, metrics in recorded_metrics[test_id].items():
                test.Steps[step-1].recorded_metrics = metrics
            for step, step_info in steps[test_id].items():
                test.Steps[step-1].start_date = _strtotimestamp(step_info["start_date"])
                test.Steps[step-1].end_date = _strtotimestamp(step_info["end_date"])
                test.Steps[step-1].status = step_info["status"]

    def __init__(self, run_id):
        self.run_id = run_id

        run_infos = db.get_run_infos(run_id)
        self.start_date = run_infos["start_date"]
        self.end_date = run_infos["end_date"]
        self.config = run_infos["config_id"]
        self.gcvb_id = run_infos["gcvb_id"]

        self.__test_db_to_objects()

    @property
    def completed(self):
        return bool(self.end_date)

    @property
    def success(self):
        return all([test.success for test in self.Tests.values()])

    @property
    def failed(self):
        return any([test.failed for test in self.Tests.values()])

    @property
    def elapsed(self):
        return self.end_date-self.start_date

    def get_running_tests(self):
        return [k for k,v in self.Tests.items() if not v.completed]

    def get_failures(self):
        return {test_id : test.get_failures() for test_id, test in self.Tests.items() if any(test.get_failures())}

    def str_status(self):
        if self.failed:
            return "Failed"
        if self.completed and self.success:
            return "Success"
        else:
            return "In progress"


class TaskFailure():
    def __init__(self):
        pass

    def __repr__(self):
        pass

    def __str__(self):
        pass

class ExitFailure(TaskFailure):
    def __init__(self, executable, return_code):
        self.executable = executable
        self.return_code = return_code

    def __repr__(self):
        return f"<Exit Failure (return code : {self.return_code})>"

    def __str__(self):
        return self.__repr__()

    def hr_result(self):
        return f"{self.executable} exited with code {self.return_code}"


class MissingMetric(TaskFailure):
    def __init__(self, metric_id):
        self.metric_id = metric_id

    def __repr__(self):
        return f"<Missing Metric ({self.metric_id})>"

    def __str__(self):
        return self.__repr__()

    def hr_result(self):
        return f"Metric {self.metric_id} is missing."

class OutOfTolerance(TaskFailure):
    def __init__(self, metric_id, metric, recorded):
        self.metric_id = metric_id
        self.metric = metric
        self.recorded = recorded

    def __repr__(self):
        return f"<OutOfTolerance (metric : {self.metric_id})"

    def __str__(self):
        return self.__repr__()

    def hr_result(self):
        target = self.metric.reference #FIXME
        value = self.recorded #FIXME
        return f"{self.metric.type.capitalize()} metric {self.metric_id} is out of tolerance. (target : {target}, value : {value})"
