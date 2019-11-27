import argparse
from collections import defaultdict

snippets=defaultdict(dict)

snippets[".gitignore"]["description"]="A simple .gitignore file if you would like to use version your gcvb-base through git"
snippets[".gitignore"]["file"]=\
"""\
results
gcvb.db
"""
snippets["template.yaml"]["description"]="Example yaml file to generate templated tests"
snippets["template.yaml"]["file"]=\
"""\
default_values:
  task:
    nprocs: "1"
    nthreads: "1"
    launch_command: "{@job_creation[executable]} {@job_creation[options]}"

Packs:
- pack_id : "<Pack_ID>"
  description : "Multiple tests generated via the template system"
  Tests :
  - id: "id_{templated_var}_{templated_dict[id]}"
    type : "template"
    template_files : "<template_folder>"
    data : "<data_folder>"
    template_instantiation: 
      templated_var : ["a","b"]
      templated_dict: 
      - {id: "1" ,value: "I"}
    description: "<your description here ({templated_dict[value]})>"
    Tasks:
    - executable : "echo"
      options : "{templated_var} {templated_dict[id]}"
"""

snippets["config.yaml"]["description"]="Simple config.yaml to initiate a gcvb base"
snippets["config.yaml"]["file"]=\
"""\
machine_id: myconfig
submit_command: sh
executables: {}
"""

def generate_parser(parser):
    help_string="".join(["{0:20}{1}\n".format(k, v["description"]) for k,v in snippets.items()])
    subparser = parser.add_parser("snippet", 
                                  help="print on stdout some typical example files for gcvb", 
                                  formatter_class=argparse.RawDescriptionHelpFormatter,
                                  description=help_string)

    subparser.add_argument("snippet", metavar="example-file", choices=snippets.keys())

def display(args):
    print(snippets[args.snippet]["file"], end='')

if __name__ == '__main__':
    #Test purpose only
    parser = argparse.ArgumentParser(description="Dummy test outside gcvb")
    subparsers = parser.add_subparsers(dest="command")
    generate_parser(subparsers)
    args=parser.parse_args()
    if args.command=="snippet":
        display(args)