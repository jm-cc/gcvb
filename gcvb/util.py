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
import re

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

def str_to_ip(str_in, default_ip="127.0.0.1", default_port=8050):
    ip=default_ip
    port=default_port

    re_ip_and_port = '(?P<ip>[0-9]+(?:\\.[0-9]+){3}):(?P<port>[0-9]+)'
    re_ip = '(?P<ip>[0-9]+(?:\\.[0-9]+){3})'
    re_port = '(?P<port>[0-9]+)'

    is_ip_and_port = re.fullmatch(re_ip_and_port, str_in)
    is_ip = re.fullmatch(re_ip, str_in)
    is_port = re.fullmatch(re_port, str_in)

    if is_ip_and_port:
        ip = is_ip_and_port.group("ip")
        port = int(is_ip_and_port.group("port"))
    elif is_ip:
        ip = is_ip.group("ip")
    elif is_port:
        port = int(is_port.group("port"))
    else:
        raise ValueError(f"{str_in} is invalid.")

    #Last check
    max_value = (2**16-1)
    if port < 1 or port > max_value :
        raise ValueError(f"Port should be between 1 and {max_value}")
    return ip, port