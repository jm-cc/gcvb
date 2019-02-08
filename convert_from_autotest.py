import xml.etree.ElementTree as ET
import os
import shutil
from ruamel.yaml import YAML
from collections import OrderedDict

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
    for vogroup in root:
        if vogroup.tag != "vogroup":
            continue        
        attrib=vogroup.attrib
        current_data=data_new_dir[attrib["data"]]
        for vo in vogroup:
            a=vo.attrib
            if "voDir" not in a:
                continue
            dst=os.path.join(new_data,current_data,"references",a["voDir"])
            try:
                os.makedirs(dst)
            except OSError:
                print("File {} already exists !".format(target_dir))
            files=a["voFiles"].split(",")
            for f in files:
                tmp=os.path.split(current_data)[0]
                src=os.path.join(old_data,tmp,a["voDir"],f.strip())
                try:
                    shutil.copy(src,dst)
                except FileNotFoundError:
                    print ("File {} does not exists !".format(src))                
            



# takes an old tests.xml and returns a dict to be dump as a "tests.yaml"
def convert_test(old_dir):
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
            current_test["data"]=test["data"] #Must be modified since now the data are not organized the same way as before
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
                        current_validation["id"]=valid[0]
                        current_validation["tolerance"]=valid[1]
    return res

#dictionnary to yaml
def dictionnary_to_yaml(d,yaml_file):
    yaml = YAML()
    yaml.Representer.add_representer(OrderedDict, yaml.Representer.represent_dict)
    with open(yaml_file,'w') as f:
        yaml.dump(d,f)
