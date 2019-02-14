import yaml

def open_yaml(filename):
    with open(filename,'r') as stream:
        res=yaml.load(stream)
    return res