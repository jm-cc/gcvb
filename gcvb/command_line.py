import argparse
import yaml
import re
import os
import gzip
import shutil
from . import yaml_input
from . import template

def parse():
    parser = argparse.ArgumentParser(description="(G)enerate (C)ompute (V)alidate (B)enchmark",prog="gcvb")

    #filters options
    parser.add_argument('--yaml-file',metavar="filename",default="test.yaml")
    parser.add_argument('--filter-by-pack',metavar="regexp",help="Regexp to select packs")
    parser.add_argument('--filter-by-test-id',metavar="regexp",help="Regexp to select jobs by test-id")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--filter-by-tag',metavar="tag",help="a tag name to filter tests")
    group.add_argument('--filter-by-tag-and',metavar="tag_list",help="comma-separated list of tags to filter tests (AND operator)")
    group.add_argument('--filter-by-tag-or',metavar="tag_list",help="comma-separated list of tags to filter tests (OR operator)")
    
    subparsers = parser.add_subparsers(dest="command")
    parser_generate = subparsers.add_parser('generate', help="generate a new gcvb instance")
    parser_list = subparsers.add_parser('list', help="list tests (YAML)")

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

def uncompress(file_in,file_out):
    with gzip.open(file_in, 'rb') as f_in:
        with open(file_out, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

def main():
    args=parse()
    if args.command in ["list","generate"]:
        a=yaml_input.load_yaml(args.yaml_file)
        a=filter(args,a)
    #Commands
    if args.command=="list":
        print(yaml.dump(a))
    if args.command=="generate":
        target_dir="./results/0"
        data_root=os.path.join(os.getcwd(),"data")
        os.makedirs(target_dir)
        for p in a["Packs"]:
            for t in p["Tests"]:
                os.makedirs(os.path.join(target_dir,t["id"]))
                data_path=os.path.join(data_root,t["data"],"input")
                for file in os.listdir(data_path):
                    extension = os.path.splitext(file)[1]
                    src=os.path.join(data_path,file)
                    dst=os.path.join(target_dir,t["id"],file)
                    if (extension==".gz"):
                        uncompress(src,dst[:-3])
                    else:
                        os.symlink(src,dst)
                if ("template_files" in t):
                    template_path=os.path.join(data_root,t["data"],"template",t["template_files"])
                    for file in os.listdir(template_path):
                        src=os.path.join(template_path,file)
                        dst=os.path.join(target_dir,t["id"],file)
                        template.apply_format_to_file(src,dst,t["template_instantiation"])

if __name__ == '__main__':
    main()
