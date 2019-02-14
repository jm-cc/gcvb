import argparse
import yaml
import re
import os
from . import yaml_input
from . import template
from . import job
from . import util

def parse():
    parser = argparse.ArgumentParser(description="(G)enerate (C)ompute (V)alidate (B)enchmark",prog="gcvb")

    #filters options
    parser.add_argument('--yaml-file',metavar="filename",default="test.yaml")
    parser.add_argument('--data-root',metavar="dir",default=os.path.join(os.getcwd(),"data"))
    parser.add_argument('--filter-by-pack',metavar="regexp",help="Regexp to select packs")
    parser.add_argument('--filter-by-test-id',metavar="regexp",help="Regexp to select jobs by test-id")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--filter-by-tag',metavar="tag",help="a tag name to filter tests")
    group.add_argument('--filter-by-tag-and',metavar="tag_list",help="comma-separated list of tags to filter tests (AND operator)")
    group.add_argument('--filter-by-tag-or',metavar="tag_list",help="comma-separated list of tags to filter tests (OR operator)")
    
    subparsers = parser.add_subparsers(dest="command")
    parser_generate = subparsers.add_parser('generate', help="generate a new gcvb instance")
    parser_list = subparsers.add_parser('list', help="list tests (YAML)")
    parser_compute = subparsers.add_parser('compute', help="run tests")

    args=parser.parse_args()
    return args

def filter(args,data):
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
    return data

def main():
    args=parse()
    data_root=os.path.abspath(args.data_root)
    if args.command in ["list","generate"]:
        a=yaml_input.load_yaml(args.yaml_file)
        a=filter(args,a)
    #Commands
    if args.command=="list":
        print(yaml.dump(a))
    if args.command=="generate":
        target_dir="./results/0"
        job.generate(target_dir,data_root,a)

    if args.command=="compute":
        computation_dir="./results/0"
        a=yaml_input.load_yaml(os.path.join(computation_dir,"tests.yaml"))
        a=filter(args,a)
        config=util.open_yaml("config.yaml")

        all_tests=[t for p in a["Packs"] for t in p["Tests"]]
        ref=yaml_input.get_references(all_tests,data_root)
        job_file=os.path.join(computation_dir,"job.sh")
        job.launch(all_tests, config, data_root, ref, job_file=job_file)

if __name__ == '__main__':
    main()