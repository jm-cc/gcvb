def relative_change(new_value,reference):
    return abs((new_value-reference)/reference)

class Report:
    def __init__(self, validation_base, run_base, configuration=None):
        self.run_base = run_base
        self.validation_base = {}
        for p in validation_base["Packs"]:
            for t in p["Tests"]:
                self.validation_base[t["id"]]={}
                for ta in t["Tasks"]:
                    for v in ta.get("Validations",[]):
                        d={}
                        self.validation_base[t["id"]][v["id"]]=d
                        for k in ["id","tolerance","type","reference"]:
                            if k in v:
                                d[k]=v[k]
        self.success={}
        self.failure={}
        self.missing_validations={}
        for test_id,test in self.run_base.items():
            for validation_metric,valid in self.validation_base[test_id].items():
                if validation_metric not in test:
                    self.missing_validations.setdefault(test_id,[]).append(validation_metric)
                    continue
                validation_type=valid.get("type","file_comparison")
                if validation_type=="file_comparison":
                    t=float(test[validation_metric])
                    self.__within_tolerance(t,test_id,valid)
                elif validation_type=="configuration_independent":
                    rel_change=relative_change(float(test[validation_metric]),float(valid["reference"]))
                    t=abs(rel_change)
                    self.__within_tolerance(t,test_id,valid)
                elif validation_type=="configuration_dependent":
                    if configuration in valid["reference"]:
                        rel_change=relative_change(float(test[validation_metric]),float(valid["reference"][configuration]))
                        t=abs(rel_change)
                        self.__within_tolerance(t,test_id,valid)
                else:
                    raise ValueError("Unknown validation type \"%s\". Should be in (file_comparison,configuration_independent,configuration_dependent)" % validation_type)

    def __within_tolerance(self,test_value,test_id,valid):
        res={"id" : valid["id"], "tolerance" : valid["tolerance"], "distance" : test_value}
        if (test_value<=float(valid["tolerance"])):
            self.success.setdefault(test_id,[]).append(res)
        else:
            self.failure.setdefault(test_id,[]).append(res)

    def is_success(self):
        return not(self.missing_validations or self.failure)

    def get_failed_tests(self):
        return self.failure.keys()

    def get_successful_tests(self):
        return list(set(self.success.keys()).difference(set(self.failure.keys())))


