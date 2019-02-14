import os
from . import util

def generate(target_dir,data_root,gcvb):
    """Generate computation directories

    Keyword arguments:
    target_dir -- targeted directory
    gcvb       -- gcvb struct
    """
    os.makedirs(target_dir)
    test_file=os.path.join(target_dir,"tests.yaml")
    util.write_yaml(gcvb,test_file)
    for p in gcvb["Packs"]:
        for t in p["Tests"]:
            os.makedirs(os.path.join(target_dir,t["id"]))
            data_path=os.path.join(data_root,t["data"],"input")
            for file in os.listdir(data_path):
                extension = os.path.splitext(file)[1]
                src=os.path.join(data_path,file)
                dst=os.path.join(target_dir,t["id"],file)
                if (extension==".gz"):
                    util.uncompress(src,dst[:-3])
                else:
                    os.symlink(src,dst)
            if ("template_files" in t):
                template_path=os.path.join(data_root,t["data"],"template",t["template_files"])
                for file in os.listdir(template_path):
                    src=os.path.join(template_path,file)
                    dst=os.path.join(target_dir,t["id"],file)
                    template.apply_format_to_file(src,dst,t["template_instantiation"])

def launch(tests, config, data_root, valid, *, job_file="job.sh"):
    with open(job_file,'w') as f:
        for test in tests:
            f.write("cd {0}\n".format(test["id"]))
            for c,t in enumerate(test["Tasks"]):
                at_job_creation={}
                at_job_creation["nthreads"]=t["nthreads"]
                at_job_creation["nprocs"]=t["nprocs"]
                at_job_creation["full_id"]=test["id"]+"_"+str(c)
                at_job_creation["executable"]=t["executable"]
                if t["executable"] in config["executables"]:
                    at_job_creation["executable"]=config["executables"][t["executable"]]
                at_job_creation["options"]=t["options"]
                f.write(t["launch_command"].format(**{"@job_creation" : at_job_creation}))
                f.write("\n")
                for d,v in enumerate(t.get("Validations",[])):
                    at_job_creation["va_id"]=at_job_creation["full_id"]+"_"+v["id"]
                    at_job_creation["va_executable"]=v["executable"]
                    tmp=v["id"].split("-")
                    v_dir,v_id=tmp[0],tmp[1]
                    at_job_creation["va_filename"]=valid[test["data"]][v_dir][v_id]["file"]
                    at_job_creation["va_refdir"]=os.path.join(data_root,test["data"],"references",v_dir)
                    if v["executable"] in config["executables"]:
                        at_job_creation["va_executable"]=config["executables"][v["executable"]]
                    f.write(v["launch_command"].format(**{"@job_creation" : at_job_creation}))
                    f.write("\n")
            f.write("cd ..\n")