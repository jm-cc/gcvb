import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    print("Warning pyaml : CLoader not avalaible. Slower Python Loader is used instead...")
    from yaml import Loader, Dumper
import gzip
import shutil
import io
import hashlib
import pickle

def hash_file(filename):
    with open(filename,"rb") as f:
        b = f.read() # read entire file as bytes
        readable_hash = hashlib.sha256(b).hexdigest()
        return readable_hash

def pickle_obj_to_binary(obj):
    """ return bytes from a python object"""
    with io.BytesIO() as f:
        pickle.dump(obj, f)
        f.seek(0)
        return f.read()

def pickle_binary_to_obj(binary):
    with io.BytesIO(binary) as f:
        return pickle.load(f)



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