import yaml
import copy
import os
import importlib
from . import template
from . import util

def propagate_default_value(default_dict,target_dict):
    for step in ["validation","task","test"]:
        target_dict.setdefault(step,{})
        for k in default_dict.get(step,{}).keys():
            if k not in target_dict[step]:
                target_dict[step][k]=default_dict[step][k]

def set_default_value(default_dict,target_dict):
    for k,v in default_dict.items():
        if k not in target_dict:
            target_dict[k]=v

def load_yaml(yaml_file, modifier=None):
    """Load a yaml file and generate the corresponding gcvb dictionary

    Keyword arguments:
    yaml_file -- name of the file to load
    """
    original=util.open_yaml(yaml_file)

    res={}
    default_values=original.get("default_values",{})
    #res["default_values"]=default_values
    res["Packs"]=[]
    res["Tests"]={}

    for pack in original["Packs"]:
        pack.setdefault("default_values",{})
        propagate_default_value(default_values,pack["default_values"])
        for test in pack["Tests"]:
            test.setdefault("default_values",{})
            propagate_default_value(pack["default_values"],test["default_values"])
            set_default_value(test["default_values"]["test"],test)
            for t in test["Tasks"]:
                set_default_value(test["default_values"]["task"],t)
                for v in t.get("Validations",[]):
                    set_default_value(test["default_values"]["validation"],v)
            del test["default_values"]
        del pack["default_values"]

    for pack in original["Packs"]:
        current_pack={}
        for key in pack.keys():
            if (key!="Tests"):
                current_pack[key]=pack[key]
        current_pack["Tests"]=[]

        res["Packs"].append(current_pack)
        for test in pack["Tests"]:
            if test.get("type","simple")=="template":
                generated_tests=template.generate_dict_list(test["template_instantiation"])
                for t in generated_tests:
                    tmp=dict(t)
                    tmp["@job_creation"]=template.job_creation_dict()
                    current_test=template.apply_instantiation(test,tmp)
                    del current_test["template_instantiation"]
                    del current_test["type"]
                    current_test["template_instantiation"]=t
                    current_pack["Tests"].append(current_test)
            else:
                current_test=copy.deepcopy(test)
                current_pack["Tests"].append(current_test)
            res["Tests"][current_test["id"]]=current_test
    if (modifier):
        mod=importlib.import_module(modifier)
        res=mod.modify(res)
    return res

def filter_by_tag(tests,tag):
    """Return a list of tests filtered by a tag

    Keyword arguments:
    tests -- list of tests
    tag   -- the considered tag
    """
    return [x for x in tests if tag in x.get("tags",[])]

def get_references(tests_cases,data_root="./"):
    """Return a dict of references for the given testcases.

    Keyword argument:
    tests_cases -- iterable of tests_cases
    """
    data_dirs={t["data"] for t in tests_cases}
    res={}
    for d in data_dirs:
        res[d]={}
        ref_path=os.path.join(data_root,d,"references")
        subfolders = [f.name for f in os.scandir(ref_path) if f.is_dir()]
        for current_ref in subfolders:
            tmp=util.open_yaml(os.path.join(ref_path,current_ref,"ref.yaml"))
            for v in tmp:
                res[d].setdefault(current_ref,{})[v["id"]]=v
    return res