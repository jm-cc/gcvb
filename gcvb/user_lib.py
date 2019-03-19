from . import db
import os

def add_metric(name, value):
    db.set_db("../../../gcvb.db")
    for env in ["GCVB_RUN_ID","GCVB_TEST_ID"]:
        if env not in os.environ:
            raise Exception("Environment variable {} is not defined.".format(env))
    test_id=os.environ["GCVB_TEST_ID"] # string as in the yaml file.
    run_id=os.environ["GCVB_RUN_ID"] # integer id
    db.add_metric(run_id, test_id, name, value)

def get_tests(run=None):
    if not(run):
        run=db.get_last_run()[0]
    return [row["name"] for row in db.get_tests(run)]

def get_file_list(test, run=None):
    if not(run):
        run=db.get_last_run()[0]
    return db.get_file_list(run, test)

def retrieve_file(test, filename, run=None):
    if not(run):
        run=db.get_last_run()[0]
    return db.retrieve_file(run, test, filename)