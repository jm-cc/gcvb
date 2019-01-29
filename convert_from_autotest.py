import xml.etree.ElementTree as ET
import os
import shutil
import yaml

# from data.xml create 
def convert_xml_data(old_data,new_data):
    xml_input=old_data+"/xml/data.xml"
    tree=ET.parse(xml_input)
    root=tree.getroot()
    for child in root:
        attrib=child.attrib
        target_dir=os.path.join(new_data,attrib["directory"],attrib["dataId"],"input")
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

# takes an old tests.xml and returns a dict to be dump as a "tests.yaml"
def convert_test(old_dir):
    res={}
    res["Packs"]=[]
    xml_input=old_dir+"xml/tests.xml"
    tree=ET.parse(xml_input)
    root=tree.getroot()
    for tP in root:
        if tP.tag != "TestsPack":
            continue
        testPack=tP.attrib
        current_pack={}
        res["Packs"].append(current_pack)        
        current_pack["pack_id"]=testPack["packageName"]
        current_pack["description"]=testPack["description"]
        current_pack["objective"]=testPack["objective"]
        current_pack["Tests"]=[]
        for te in tP:
            test=te.attrib
            current_test={}
            current_pack["Tests"].append(current_test)
            # Test
            current_test["id"]=test["testId"]
            current_test["description"]=test["description"]
            current_test["data"]=test["data"] #Must be modified since now the data are not organized the same way as before
            current_test["Tasks"]=[]
            for ta in te:
                task=ta.attrib
                current_task={}
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
                        current_validation={}
                        current_task["Validations"].append(current_validation)
                        current_validation["id"]=valid[0]
                        current_validation["tolerance"]=valid[1]
    return res

#dictionnary to yaml
def dictionnary_to_yaml(dic,yaml):
    
