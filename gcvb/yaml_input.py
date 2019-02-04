import yaml
import copy
import template
import time

def propagate_default_value(default_dict,target_dict):
    for step in ["validation","task"]:
        target_dict.setdefault(step,{})
        for k in default_dict.get(step,{}).keys():
            if k not in target_dict[step]:
                target_dict[step][k]=default_dict[step][k]

def load_yaml(yaml_file):
    """Load a yaml file and generate the corresponding gcvb dictionary

    Keyword arguments:
    yaml_file -- name of the file to load
    """
    with open(yaml_file,'r') as stream:
        original=yaml.load(stream)

    res=[]
    default_values=original.get("default_values",{})

    for pack in original["Packs"]:
        current_pack={}
        for key in pack.keys():
            if (key!="Tests"):
                current_pack[key]=pack[key]
        current_pack["Tests"]=[]

        res.append(current_pack)
        #add not-overrided default_values to default_values
        current_pack.setdefault("default_values",{})
        propagate_default_value(default_values,current_pack["default_values"])

        for test in pack["Tests"]:
            if test.get("type","simple")=="template":
                generated_tests=template.generate_dict_list(test["template_instantiation"])
                for t in generated_tests:
                    current_test=template.apply_instantiation(test,t)
                    del current_test["template_instantiation"]
                    del current_test["type"]
                    current_pack["Tests"].append(current_test)
            else:
                current_test=copy.deepcopy(test)
                current_pack["Tests"].append(current_test)
                current_test.setdefault("default_values",{})
                propagate_default_value(current_pack["default_values"],current_test["default_values"])

    return res

def filter_by_tag(tests,tag):
    """Return a list of tests filtered by a tag

    Keyword arguments:
    tests -- list of tests
    tag   -- the considered tag
    """
    return [x for x in tests if tag in x.get("tags",[])]