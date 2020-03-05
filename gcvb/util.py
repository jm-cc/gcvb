import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    print("Warning pyaml : CLoader not avalaible. Slower Python Loader is used instead...")
    from yaml import Loader, Dumper
import gzip
import shutil

def open_yaml(filename):
    with open(filename,'r') as stream:
        res=yaml.load(stream, Loader=Loader)
    return res

def write_yaml(struct,filename):
    with open(filename,'w') as f:
        f.write(yaml.dump(struct,Dumper=Dumper,sort_keys=False))

def uncompress(file_in,file_out):
    with gzip.open(file_in, 'rb') as f_in:
        with open(file_out, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

def file_to_compressed_binary(file_in):
    with open(file_in,"rb") as f:
        content = f.read()
    return gzip.compress(content)