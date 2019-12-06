import argparse
import os
import datetime
from shutil import copyfile
from . import yaml_input
from . import util
from collections import OrderedDict

def generate_from_base(base_id, files, reference_id, description):
    """Generate references from a base where a computation as already been executed.

    This function will copy files to the right path in the data directory. 
    Supposed to be executed inside the gcvb instance root.

    Keywords argument
    base_id      -- id of the base used for generating references 
    files        -- list of files to be copied as reference when they exists.
    reference_id -- arbitrary string to identify how the references were generated. 
                    A folder inside the <test_case>/references will be created to store the new references files.
    description  -- a description to be added for each new reference.
    """
    base_dir=os.path.join(".","results",str(base_id))
    yaml=yaml_input.load_yaml(os.path.join(base_dir,"tests.yaml"))
    data_root=yaml["data_root"]
    for test_id,test in yaml["Tests"].items():
        data_reference_dir=os.path.join(data_root,test["data"],"references",reference_id)
        result_dir=os.path.join(base_dir,test_id)
        if not os.path.exists(data_reference_dir):
            os.makedirs(data_reference_dir)
        #update reference files
        ref_file=os.path.join(data_reference_dir,"ref.yaml")
        refs=[]
        if os.path.exists(ref_file):
            refs=util.open_yaml(ref_file)
        all_ids={a["id"] for a in refs}
        for f in files:
            new_id=f"{test_id}-{f}"
            if new_id in all_ids:
                raise ValueError("ID already existing in ref.yaml!")
            all_ids.add(new_id)
            src=os.path.join(result_dir,f)
            dst=os.path.join(data_reference_dir,new_id)
            copyfile(src,dst)
            reference={"id" : new_id, "description" : description, "file" : new_id}
            refs.append(reference)
        util.write_yaml(refs,ref_file)