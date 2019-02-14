import xml.etree.ElementTree as ET
import os
import shutil
from ruamel.yaml import YAML
from collections import OrderedDict,defaultdict

# from data.xml create 
def convert_xml_data(old_data,new_data):
    data_xml=old_data+"/xml/data.xml"
    tree=ET.parse(data_xml)
    root=tree.getroot()
    data_new_dir={}    
    for child in root:
        attrib=child.attrib
        data_new_dir[attrib["dataId"]]=os.path.join(attrib["directory"],attrib["dataId"])
        target_dir=os.path.join(new_data,data_new_dir[attrib["dataId"]],"input")
        try:
            os.makedirs(target_dir)
        except OSError:
            print("File {} already exists !".format(target_dir))
        files=attrib["files"].split()
        for f in files:
            src=os.path.join(old_data,attrib["directory"],f)
            ext=os.path.splitext(src)[1]
            try:
                shutil.copy(src,target_dir)
            except IOError:
                try:
                    shutil.copy(src+".gz",target_dir)
                except:
                    print("File {} does not exist !".format(src))
                    pass
    valid_xml=old_data+"/xml/valid.xml"
    tree=ET.parse(valid_xml)
    root=tree.getroot()
    yaml_per_dir=OrderedDict()
    for vogroup in root:
        if vogroup.tag != "vogroup":
            continue        
        attrib=vogroup.attrib
        current_data=data_new_dir[attrib["data"]]
        yaml_per_dir.setdefault(current_data, default={})
        for vo in vogroup:
            a=vo.attrib
            if "voDir" not in a:
                print("{} skipped, no voDir".format(repr(a)))
                continue
            ref_dir=a["voDir"].replace("/","+")
            dst=os.path.join(new_data,current_data,"references",ref_dir)
            try:
                os.makedirs(dst)
            except OSError:
                print("File {} already exists !".format(ref_dir))
            files=a["voFiles"].split(",")
            for f in files:
                tmp=os.path.split(current_data)[0]
                src=os.path.join(old_data,tmp,a["voDir"],f.strip())
                try:
                    shutil.copy(src,dst)
                except FileNotFoundError:
                    print ("File {} does not exists !".format(src))
            tmp=OrderedDict()
            tmp["id"]=a["voId"]
            tmp["description"]=a["voDescr"]
            tmp["file"]=files[0]
            if (len(files))>1:
                print ("More than one file for id {}".format(tmp["id"]))
            yaml_per_dir[current_data].setdefault(ref_dir,[]).append(tmp)
    for directory,validations in yaml_per_dir.items():
        for refname,future_yaml in validations.items():
            dst=os.path.join(new_data,directory,"references",refname,"ref.yaml")
            dictionnary_to_yaml(future_yaml,dst)
    return data_new_dir

            

def valid_to_new_ref_id(old_dir):
    res=defaultdict(dict)
    xml_input=old_dir+"/xml/valid.xml"
    tree=ET.parse(xml_input)
    root=tree.getroot()
    for vogroup in root:
        data=vogroup.attrib["data"]
        for vo in vogroup:
            a=vo.attrib
            if "voDir" not in a:
                continue
            res[data][a["voId"]]=a["voDir"].replace("/","+")+"-"+a["voId"]
    return res


# takes an old tests.xml and returns a dict to be dump as a "tests.yaml"
def convert_test(old_dir,data={}):
    valid_d=valid_to_new_ref_id(old_dir)
    res=OrderedDict()
    res["Packs"]=[]
    xml_input=old_dir+"xml/tests.xml"
    tree=ET.parse(xml_input)
    root=tree.getroot()
    for tP in root:
        if tP.tag != "TestsPack":
            continue
        testPack=tP.attrib
        current_pack=OrderedDict()
        res["Packs"].append(current_pack)        
        current_pack["pack_id"]=testPack["packageName"]
        current_pack["description"]=testPack["description"]
        current_pack["objective"]=testPack["objective"]
        current_pack["Tests"]=[]
        for te in tP:
            test=te.attrib
            current_test=OrderedDict()
            current_pack["Tests"].append(current_test)
            # Test
            current_test["id"]=test["testId"]
            current_test["description"]=test["description"]
            if data:
                current_test["data"]=data[test["data"]]
            current_test["Tasks"]=[]
            for ta in te:
                task=ta.attrib
                current_task=OrderedDict()
                current_test["Tasks"].append(current_task)
                #Task
                current_task["executable"]=task["executable"]
                current_task["options"]=task["options"]
                if "nprocs" in task:
                    current_task["nprocs"]=task["nprocs"]
                if "nthreads" in task:
                    current_task["nthreads"]=task["nthreads"]
                #Validations
                if "validations" in task:
                    if not task["validations"]: #sometimes there is a attrib validations without value
                        continue 
                    current_task["Validations"]=[]
                    all_validations=task["validations"].split(",")
                    for va in all_validations:
                        valid=va.strip().split("+")
                        current_validation=OrderedDict()
                        current_task["Validations"].append(current_validation)
                        current_validation["id"]=valid_d[test["data"]][valid[0]]
                        current_validation["tolerance"]=valid[1]
    return res

#dictionnary to yaml
def dictionnary_to_yaml(d,yaml_file):
    yaml = YAML()
    yaml.Representer.add_representer(OrderedDict, yaml.Representer.represent_dict)
    with open(yaml_file,'w') as f:
        yaml.dump(d,f)
