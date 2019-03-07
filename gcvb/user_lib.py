from . import db
import os

def add_metric(name, value):
    for env in ["GCVB_RUN_ID","GCVB_TEST_ID"]:
        if env not in os.environ:
            raise Exception("Environment variable {} is not defined.".format(env))
    test_id=os.environ["GCVB_TEST_ID"] # string as in the yaml file.
    run_id=os.environ["GCVB_RUN_ID"] # integer id
    db.add_metric(run_id, test_id, name, value)
