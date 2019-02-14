import yaml
import gzip
import shutil

def open_yaml(filename):
    with open(filename,'r') as stream:
        res=yaml.load(stream)
    return res

def write_yaml(struct,filename):
    with open(filename,'w') as f:
        f.write(yaml.dump(struct))

def uncompress(file_in,file_out):
    with gzip.open(file_in, 'rb') as f_in:
        with open(file_out, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)