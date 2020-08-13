def relative_change(new_value,reference):
    return abs((new_value-reference)/reference)

class Report:
    def __init__(self, validation_base, run_base, configuration=None):
        self.run_base = run_base
        self.validation_base = {}
        self.status = {}
        for p in validation_base["Packs"]:
            for t in p["Tests"]:
                self.validation_base[t["id"]]={}
                for ta in t["Tasks"]:
                    for v in ta.get("Validations",[]):
                        for m in v.get("Metrics", []):
                            d={}
                            self.validation_base[t["id"]][m["id"]]=d
                            for k in ["id","tolerance","type","reference"]:
                                if k in m:
                                    d[k]=m[k]
                            d["launch_type"] = v["type"]
        self.success={}
        self.failure={}
        self.missing_validations={}
        for test_id,test in self.run_base.items():
            self.status[test_id]="success"
            for validation_metric,valid in self.validation_base[test_id].items():
                if validation_metric not in test:
                    self.missing_validations.setdefault(test_id,[]).append(validation_metric)
                    if self.status[test_id]!="failure":
                        self.status[test_id]="missing_validation"
                    continue
                validation_type=valid.setdefault("type","absolute" if valid["launch_type"]=="file_comparison" else "relative")
                if validation_type=="absolute":
                    t=float(test[validation_metric])
                    self.__within_tolerance(t,test_id,valid)
                elif validation_type=="relative":
                    if isinstance(valid["reference"],dict):
                        if configuration in valid["reference"]:
                            ref = float(valid["reference"][configuration])
                        else:
                            continue
                    else:
                        ref = float(valid["reference"])
                    rel_change=relative_change(float(test[validation_metric]),ref)
                    t=abs(rel_change)
                    self.__within_tolerance(t,test_id,valid)
                else:
                    raise ValueError("Unknown validation type \"%s\". Should be in (absolute, relative)" % validation_type)

    def __within_tolerance(self,test_value,test_id,valid):
        res={"id" : valid["id"], "tolerance" : valid["tolerance"], "distance" : test_value, "type" : valid["type"]}
        if (test_value<=float(valid["tolerance"])):
            self.success.setdefault(test_id,[]).append(res)
        else:
            self.failure.setdefault(test_id,[]).append(res)
            self.status[test_id]="failure" # failure is definitive

    def is_success(self):
        return not(self.missing_validations or self.failure)

    def get_failed_tests(self):
        return self.failure.keys()

    def get_successful_tests(self):
        return list(set(self.success.keys()).difference(set(self.failure.keys())))


