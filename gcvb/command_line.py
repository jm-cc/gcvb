import argparse
import yaml
import re
import os
import sys
import pprint
import time
import platform
from . import yaml_input
from . import template
from . import job
from . import util
from . import db
from . import snippet
from . import generate_refs
from . import jobrunner
from . import model
from . import report

def parse():
    parser = argparse.ArgumentParser(description="(G)enerate (C)ompute (V)alidate (B)enchmark",prog="gcvb")

    #filters options
    parser.add_argument('--filter-by-pack',metavar="regexp",help="Regexp to select packs")
    parser.add_argument('--filter-by-test-id',metavar="regexp",help="Regexp to select jobs by test-id")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--filter-by-tag',metavar="tag",help="a tag name to filter tests")
    group.add_argument('--filter-by-tag-and',metavar="tag_list",help="comma-separated list of tags to filter tests (AND operator)")
    group.add_argument('--filter-by-tag-or',metavar="tag_list",help="comma-separated list of tags to filter tests (OR operator)")
    #filter + exclude is possible.
    parser.add_argument('--exclude-tag',metavar="tag_list",help="comma-separated list of tags to filter tests. Tests containing at least one of the tags will be excluded.")
    parser.add_argument('--db-file', help="Alternative path of the gcvb.db file (experimental).", default="gcvb.db")

    subparsers = parser.add_subparsers(dest="command")
    parser_generate = subparsers.add_parser('generate', help="generate a new gcvb instance")
    parser_list = subparsers.add_parser('list', help="list tests (YAML)")
    parser_compute = subparsers.add_parser('compute', help="run tests")
    parser_db = subparsers.add_parser('db', add_help=False)
    parser_report = subparsers.add_parser('report', help="get a report regarding a gcvb run")
    parser_dashboard = subparsers.add_parser('dashboard', help="launch a Dash instance to browse results" )
    parser_dashboard.add_argument("--debug", "-d", action="store_true", help="Run Flask in debug mode")
    parser_dashboard.add_argument("--bind-to","-b", metavar="port_or_bind_address", help="change default binding", default="127.0.0.1:8050")
    parser_snippet = snippet.generate_parser(subparsers)
    parser_generate_refs = subparsers.add_parser('generate_refs', help="generate references from a base where a computation as already been executed.")
    parser_jobrunner = subparsers.add_parser("jobrunner", help="jobrunner to launch tests in parallel")

    parser_generate.add_argument('--data-root',metavar="dir",default=None)
    parser_generate.add_argument('--yaml-file', '-f', metavar="filename", default="test.yaml")
    parser_generate.add_argument('--modifier', '-m', metavar="python_module", default=None)

    parser_list.add_argument('--yaml-file', '-f', metavar="filename", default="test.yaml")
    parser_list.add_argument('--modifier', '-m', metavar="python_module", default=None)
    group = parser_list.add_mutually_exclusive_group()
    group.add_argument("--count", action="store_true", help="get number of tests (after template expansion and filtering).")
    group.add_argument("-H","--human-readable", action="store_true", help="get test list in a concise way.")

    parser_compute.add_argument("--gcvb-base",metavar="base_id",help="choose a specific base (default: last one created)", default=None)
    parser_compute.add_argument("--header", metavar="file", help="use file as header when generating job script", default=None)
    parser_compute.add_argument("--chain", action="store_true", help="stricter dependencies between tasks and validation")
    group = parser_compute.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="do not launch the job.")
    group.add_argument(
        "--with-jobrunner",
        "-j",
        metavar="num_cores",
        type=int,
        help="use a jobrunner instead of one submitted job with <num_cores>",
        default=None,
    )
    parser_compute.add_argument("--started-first", action="store_true", help="already started tests are launched with a higher priority (--with-jobrunner required)")
    parser_compute.add_argument("--quiet", action="store_true", help="Hide jobrunner execution log")
    parser_compute.add_argument("--max-concurrent", metavar="jobs", type=int, help="maxium jobs that can be executed concurrently by a jobrunner (--with-jobrunner required)", default=0)

    parser_db.add_argument("db_command", choices=["start_test","end_test","start_run","end_run","start_task","end_task"])
    parser_db.add_argument("first", type=str)
    parser_db.add_argument("second", type=str)
    parser_db.add_argument("third", type=str)

    parser_generate_refs.add_argument("--gcvb-base",metavar="base_id",help="choose a specific base (default: last one created)", default=None)
    parser_generate_refs.add_argument("reference_id",help="arbitrary string to identify how the references were generated")
    parser_generate_refs.add_argument("files", help="comma-separated list of files to be copied as references")
    parser_generate_refs.add_argument("--description", help="description to be added for each reference created", default="Generated by generate_refs command.")

    parser_jobrunner.add_argument("num_cores", metavar="num_cores", type=int, help="number of cores to be used")
    parser_jobrunner.add_argument("--started-first", action="store_true", help="already started tests are launched with a higher priority")
    parser_jobrunner.add_argument("--quiet", action="store_true", help="Hide execution log")
    parser_jobrunner.add_argument("--max-concurrent", metavar="jobs", type=int, help="maxium jobs that can be executed concurrently by a jobrunner", default=0)

    parser_report.add_argument("--polling", action="store_true", help="poll report until finished or timeout expiration")
    parser_report.add_argument("-f","--frequency", help="time between each check", type=float, default=10)
    parser_report.add_argument("--timeout", help="maximum time (in seconds) to wait for a single job to finish in polling mode", type=float, default=3600)
    parser_report.add_argument("--html", action="store_true", help="display result in html format")


    args=parser.parse_args()
    return args

def filter_tests(args,data):
    if (args.filter_by_pack):
        data["Packs"]=[p for p in data["Packs"] if re.match(args.filter_by_pack,p["pack_id"])]
    if (args.filter_by_test_id):
        for e in data["Packs"]:
            e["Tests"]=[t for t in e["Tests"] if re.match(args.filter_by_test_id,t["id"])]
    if (args.filter_by_tag):
        for e in data["Packs"]:
            e["Tests"]=[t for t in e["Tests"] if args.filter_by_tag in t.get("tags",[])]
    if (args.filter_by_tag_and):
        tags=set(args.filter_by_tag_and.split(","))
        for e in data["Packs"]:
            e["Tests"]=[t for t in e["Tests"] if (tags.intersection(set(t.get("tags",[])))==tags)]
    if (args.filter_by_tag_or):
        tags=set(args.filter_by_tag_or.split(","))
        for e in data["Packs"]:
            e["Tests"]=[t for t in e["Tests"] if (tags.intersection(set(t.get("tags",[])))!=set())]
    if (args.exclude_tag):
        tags=set(args.exclude_tag.split(","))
        for e in data["Packs"]:
            e["Tests"]=[t for t in e["Tests"] if (tags.intersection(set(t.get("tags",[])))==set())]
    return data

def get_to_gcvb_root():
    cwd = os.getcwd()
    d = cwd
    while not os.path.isfile(os.path.join(d, "config.yaml")):
        nd = os.path.dirname(d)
        if nd == d:
            print("Warning: config.yaml was not found in a parent directory."
                " Using current folder as gcvb instance root.", file=sys.stderr)
            d = cwd
            break
        else:
            d = nd
    # FIXME: remove this chdir and return the root folder. chdir is bad
    # if we want gcvb to be used as a library. It's too global.
    os.chdir(d)
    sys.path.append(d)

def report_check_terminaison(run_id):
    tests=db.get_tests(run_id)
    completed_tests=list(filter(lambda x: x["end_date"], tests))
    finished=(len(completed_tests)==len(tests))
    return completed_tests,tests,finished

def list_human_readable(packs):
  r = {"Packs" : []}
  for p in packs:
    r_tests = [{"id" : t["id"], "description" : t["description"]} for t in p["Tests"]]
    if r_tests:
      r["Packs"].append({"pack_id" : p["pack_id"], "description" : p["description"], "Tests" : r_tests})
  return r

def main():
    args=parse()
    db.set_db(args.db_file)
    if args.command not in ["db","snippet"]:
        #currently db is a special command that is supposed to be invoked only internaly by gcvb.
        get_to_gcvb_root()

    if not(os.path.isfile(db.database)):
        db.create_db()

    #Commands
    if args.command=="list":
        a=yaml_input.load_yaml(args.yaml_file, args.modifier)
        a=filter_tests(args,a)
        if not(args.count):
            if (args.human_readable):
              r = list_human_readable(a["Packs"])
              print(yaml.dump(r,sort_keys=False))
            else:
              print(yaml.dump({"Packs" : a["Packs"]}))
        else:
            print(len(a["Tests"].keys()))
    if args.command=="generate":
        data_root=os.path.join(os.getcwd(),"data")
        if (args.data_root):
            data_root=os.path.abspath(args.data_root)

        a=yaml_input.load_yaml(args.yaml_file, args.modifier)
        a=filter_tests(args,a)

        gcvb_id=db.new_gcvb_instance(' '.join(sys.argv[1:]),args.yaml_file,args.modifier)
        target_dir="./results/{}".format(str(gcvb_id))
        a["data_root"]=data_root
        job.generate(target_dir,a)

    if args.command=="compute":
        gcvb_id=args.gcvb_base
        if os.path.exists("config.yaml"):
            config = util.open_yaml("config.yaml")
        else:
            config = {
                "machine_id": platform.node(),
                "executables": {},
                "submit_command": "sh",
            }
        config_id=config.get("machine_id")
        if not(gcvb_id):
            gcvb_id=db.get_last_gcvb()
        run_id=db.add_run(gcvb_id,config_id)
        computation_dir="./results/{}".format(str(gcvb_id))
        a=yaml_input.load_yaml(os.path.join(computation_dir,"tests.yaml"))
        a=filter_tests(args,a)

        all_tests=[t for p in a["Packs"] for t in p["Tests"]]
        db.add_tests(run_id, all_tests, args.chain)
        job_file=os.path.join(computation_dir,"job.sh")
        data_root=a["data_root"]
        job.write_script(all_tests, config, data_root, gcvb_id, run_id, job_file=job_file, header=args.header)
        if not(args.dry_run) and not(args.with_jobrunner):
            job.launch(job_file,config)
        if (args.with_jobrunner):
            j = jobrunner.JobRunner(
                args.with_jobrunner,
                run_id,
                config,
                args.started_first,
                args.max_concurrent,
                not args.quiet,
                a,
            )
            j.run()

    if args.command=="jobrunner":
        run_id,gcvb_id=db.get_last_run() #run chosen should be modifiable
        config=util.open_yaml("config.yaml")
        num_cores=args.num_cores
        j=jobrunner.JobRunner(num_cores, run_id, config, args.started_first, args.max_concurrent, not args.quiet)
        j.run()



    if args.command=="db":
        if args.db_command=="start_run":
            db.start_run(args.first)
        if args.db_command=="end_run":
            db.end_run(args.first)
        if args.db_command=="start_test":
            db.set_db("../../../gcvb.db")
            db.start_test(args.first,args.second)
        if args.db_command=="end_test":
            db.set_db("../../../gcvb.db")
            db.end_test(args.first,args.second)
            a=yaml_input.load_yaml("../tests.yaml")
            t=a["Tests"][args.third]
            if "keep" in t:
                db.save_files(args.first,args.second,t["keep"])
        if args.db_command=="start_task":
            db.set_db("../../../gcvb.db")
            db.start_task(args.first, args.second)
        if args.db_command=="end_task":
            db.set_db("../../../gcvb.db")
            db.end_task(args.first, args.second, args.third)

    if args.command=="report":
        run_id,gcvb_id=db.get_last_run()
        if args.polling:
            while run_id is None:
                time.sleep(args.frequency)
                run_id, gcvb_id = db.get_last_run()
            # FIXME no need to read all tests, we just want the number of tests
            n = len(db.get_tests(run_id))
            while n == 0:
                time.sleep(args.frequency)
                n = len(db.get_tests(run_id))

        computation_dir="./results/{}".format(str(gcvb_id))

        #Is the run finished ?
        last_change = time.time()
        previous_completed_tests = -1
        completed_tests, tests, finished = report_check_terminaison(run_id)

        if args.polling:
            while not finished and time.time() - last_change < args.timeout :
                completed_tests, tests, finished = report_check_terminaison(run_id)
                if (previous_completed_tests != len(completed_tests)):
                    last_change = time.time()
                    now = time.strftime("%H:%M:%S %d/%m/%y")
                    print("Tests completed : {!s}/{!s} ({!s})".format(len(completed_tests),len(tests),now))
                    # Polling is for progress monitoring so we need flush
                    sys.stdout.flush()
                time.sleep(args.frequency)
                previous_completed_tests = len(completed_tests)

        run = model.Run(run_id)
        if (args.html):
            print(report.html_report(run))
        else:
            print(report.str_report(run))
        if not run.success:
            sys.exit(1)

    if args.command == "snippet":
        snippet.display(args)

    if args.command == "generate_refs":
        gcvb_id=args.gcvb_base
        files=args.files.split(",")
        if not(gcvb_id):
            gcvb_id=db.get_last_gcvb()
        generate_refs.generate_from_base(gcvb_id, files, args.reference_id, args.description)

    if args.command=="dashboard":
        from . import dashboard
        dashboard.run_server(debug=args.debug, bind_to=args.bind_to)

if __name__ == '__main__':
    main()
