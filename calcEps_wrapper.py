import argparse
import subprocess
import os
import gcvb

default_calcEps="calcEps"

def parse():
    parser = argparse.ArgumentParser(description="Autotest classical CalcEps wrapper")
    parser.add_argument('file1',metavar="first",type=str,help="first file for the comparaison")
    parser.add_argument('file2',metavar="second",type=str,help="second file for the comparaison")
    parser.add_argument('valid',metavar="valid",type=str,help="validation id")
    parser.add_argument('--calcEps',metavar="calc_eps",type=str, help="calcEps wrapped", default=default_calcEps)
    args = parser.parse_args()
    return args

def main():
    args=parse()
    subprocess.run([args.calcEps,"-first",args.file1,"-second",args.file2,"-outfile",args.valid])
    with open(args.valid,'r') as f:
        eps=f.read().strip()
    os.remove(args.valid)
    gcvb.add_metric(args.valid,float(eps))


if __name__ == '__main__':
    main()