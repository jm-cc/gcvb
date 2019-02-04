import argparse
import yaml
import yaml_input

def parse():
    parser = argparse.ArgumentParser(description="(G)enerate (C)ompute (V)alidate (B)enchmark")

    #filters options
    parser.add_argument('--yaml-file',metavar="filename",default="test.yaml")
    parser.add_argument('--filter-by-pack',metavar="pack_id",help="comma-separated list of packs to filter",nargs=1,type=str)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--filter-by-tag',metavar="tag",help="a tag name to filter tests",nargs=1,type=str)
    group.add_argument('--filter-by-tag-and',metavar="tag_list",help="comma-separated list of tags to filter tests (AND operator)",nargs=1,type=str)
    group.add_argument('--filter-by-tag-or',metavar="tag_list",help="comma-separated list of tags to filter tests (OR operator)",nargs=1,type=str)
    
    subparsers = parser.add_subparsers(dest="command")
    parser_generate = subparsers.add_parser('generate', help="generate a new gcvb instance")
    parser_list = subparsers.add_parser('list', help="list tests (YAML)")

    args=parser.parse_args()
    return args

if __name__ == '__main__':
    args=parse()
    a=yaml_input.load_yaml(args.yaml_file)
    if args.command=="list":
        print(yaml.dump(a))
        

