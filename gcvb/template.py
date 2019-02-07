def fill_current_key(e,current_key,current_dict):
    res=current_dict.copy()
    res[current_key]=e
    return res

def rec_generation(param_dict,keys,current_dict={},res=list()):
    if len(keys)==1:
        for e in param_dict[keys[0]]:
            tmp_dict=fill_current_key(e,keys[0],current_dict)
            res.append(tmp_dict)
    else:
        for e in param_dict[keys[0]]:
            tmp_dict=fill_current_key(e,keys[0],current_dict)
            rec_generation(param_dict,keys[1:],tmp_dict,res)

def generate_dict_list(param_dict):
    """Generate a list of dictionary to be used for template instantiation

    Each element of the list is a instantiation of the template.

    Keywords argument
    param_dict -- dictionary of lists used to generate all the cases. Lists can contain strings or dictionaries.
    """
    l=list(param_dict.keys())
    l.sort(key=lambda x: len(param_dict[x]),reverse=True)
    res=[]
    tmp={}
    rec_generation(param_dict,l,tmp,res)
    return res

def apply_instantiation(tpl,format_dict):
    """Apply instantiation of a template (or a struct containing template strings)

    keywords
    tpl         -- the template
    format_dict -- value replacement for keys
    """
    if isinstance(tpl,dict):
        instance={}
        for k,v in tpl.items():
            instance[k]=apply_instantiation(v,format_dict)
        return instance
    elif isinstance(tpl,list):
        instance=[]
        for e in tpl:
            instance.append(apply_instantiation(e,format_dict))
        return instance
    elif isinstance(tpl,str):
        return tpl.format(**format_dict)
    else:
        return tpl