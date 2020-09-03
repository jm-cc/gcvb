class AbsoluteMetric:
    def __init__(self, reference, tolerance, unit = None):
        self.type = "absolute"
        self.reference = reference
        self.tolerance = tolerance
        self.unit = unit
    def within_tolerance(self, value):
        return abs(value - self.reference) <= self.tolerance

class RelativeMetric;
    def __init__(self, reference, tolerance):
        self.type = "relative"
        self.reference = reference
        self.tolerance = tolerance
    def within_tolerance(self, value):
        return (abs(value - self.reference) / self.reference) <= self.tolerance

class Validation:
    def __init__(self, valid_dict, config):
        self.raw_dict = valid_dict
        self.exit_code = -3
        self.executable = valid_dict["executable"]
        self.type = valid_dict["type"]
        self.launch_command = valid_dict["launch_command"]
        self.recorded_metrics = {}
        self.init_metrics(config)

    def init_metrics(self, config):
        self.expected_metrics = 

