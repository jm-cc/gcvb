import argparse
import yaml
import re
import os
from . import yaml_input

def parse():
    parser = argparse.ArgumentParser(description="(G)enerate (C)ompute (V)alidate (B)enchmark",prog="gcvb")

    #filters options
    parser.add_argument('--yaml-file',metavar="filename",default="test.yaml")
    parser.add_argument('--filter-by-pack',metavar="regexp",help="Regexp to select packs")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--filter-by-tag',metavar="tag",help="a tag name to filter tests")
    group.add_argument('--filter-by-tag-and',metavar="tag_list",help="comma-separated list of tags to filter tests (AND operator)")
    group.add_argument('--filter-by-tag-or',metavar="tag_list",help="comma-separated list of tags to filter tests (OR operator)")
    
    subparsers = parser.add_subparsers(dest="command")
    parser_generate = subparsers.add_parser('generate', help="generate a new gcvb instance")
    parser_list = subparsers.add_parser('list', help="list tests (YAML)")

    args=parser.parse_args()
    return args

def main():
    args=parse()
    a=yaml_input.load_yaml(args.yaml_file)
    # Filters
    if (args.filter_by_pack):
        a["Packs"]=[p for p in a["Packs"] if re.match(args.filter_by_pack,p["pack_id"])]
    if (args.filter_by_tag):
        for e in a["Packs"]:
            e["Tests"]=[t for t in e["Tests"] if args.filter_by_tag in t.get("tags",[])]
    if (args.filter_by_tag_and):
        tags=set(args.filter_by_tag_and.split(","))
        for e in a["Packs"]:
            e["Tests"]=[t for t in e["Tests"] if (tags.intersection(set(t.get("tags",[])))==tags)]
    if (args.filter_by_tag_or):
        tags=set(args.filter_by_tag_or.split(","))
        for e in a["Packs"]:
            e["Tests"]=[t for t in e["Tests"] if (tags.intersection(set(t.get("tags",[])))!=set())]
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
                    os.symlink(os.path.join(data_path,file),os.path.join(target_dir,t["id"],file))


if __name__ == '__main__':
    main()
