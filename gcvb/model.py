from enum import IntEnum
class JobStatus(IntEnum):
    unlinked = -4
    pending = -3
    ready = -2
    running = -1

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
    def __init__(self, test_dict, config):
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
                self.Steps.append(t)