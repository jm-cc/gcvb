import sqlite3
import os
import glob
import gzip
from collections import defaultdict
from . import util

#SCRIPTS
creation_script="""
CREATE TABLE gcvb(id            INTEGER PRIMARY KEY,
                  command_line  TEXT,
                  yaml_file     TEXT,
                  modifier      TEXT,
                  creation_date INTEGER);

CREATE TABLE run(id         INTEGER PRIMARY KEY,
                 start_date INTEGER,
                 end_date   INTEGER,
                 gcvb_id    INTEGER,
                 config_id  TEXT,
                 FOREIGN KEY(gcvb_id) REFERENCES gcvb(id));

CREATE TABLE test(id         INTEGER PRIMARY KEY,
                  name       TEXT,
                  start_date INTEGER,
                  end_date   INTEGER,
                  run_id     INTEGER,
                  FOREIGN KEY(run_id) REFERENCES run(id));

CREATE TABLE task(id         INTEGER PRIMARY KEY,
                  step       INTEGER,
                  parent     INTEGER,
                  start_date INTEGER,
                  end_date   INTEGER,
                  test_id    INTEGER,
                  status     INTEGER DEFAULT -3, -- >=0, exit_status | -1 running | -2 ready | -3 pending
                  FOREIGN KEY(test_id) REFERENCES test(id));

CREATE TABLE valid(id        INTEGER PRIMARY KEY,
                   metric    TEXT,
                   value     REAL,
                   test_id   INTEGER,
                   task_step INTEGER,
                   FOREIGN KEY(task_step) REFERENCES task(step),
                   FOREIGN KEY(test_id)   REFERENCES test(id));

CREATE TABLE files(id       INTEGER PRIMARY KEY,
                   filename TEXT,
                   file     BLOB,
                   test_id  INTEGER,
                   FOREIGN KEY(test_id) REFERENCES test(id));

CREATE TABLE yaml_cache(mtime REAL, filename TEXT, pickle BLOB);
"""

#GLOBAL
database="gcvb.db"

def set_db(db_path):
    global database
    database=db_path

def connect(file,f, *args, **kwargs):
    conn=sqlite3.connect(file, timeout=50)
    conn.row_factory=sqlite3.Row
    c=conn.cursor()
    try:
        res = f(c, *args, **kwargs) #supposed to contain execute statements.
    except:
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        conn.close()
    return res

def get_exclusive_access():
    """Returns a sqlite3.Connection with exclusive access to the db.
       Must be closed afterwards"""
    conn=sqlite3.connect(database, timeout=50)
    conn.row_factory=sqlite3.Row
    conn.isolation_level = 'EXCLUSIVE'
    conn.execute('BEGIN EXCLUSIVE')
    return conn

def with_connection(f):
    """decorator for function needing to connect to the database"""
    def with_connection_(*args, **kwargs):
        return connect(database,f, *args, **kwargs)
    return with_connection_

@with_connection
def create_db(cursor):
    cursor.executescript(creation_script)

@with_connection
def new_gcvb_instance(cursor, command_line, yaml_file, modifier):
    cursor.execute("INSERT INTO gcvb(command_line,yaml_file,modifier,creation_date) VALUES (?,?,?,CURRENT_TIMESTAMP)",[command_line,yaml_file,modifier])
    return cursor.lastrowid

@with_connection
def get_last_gcvb(cursor):
    cursor.execute("SELECT * from gcvb ORDER BY creation_date DESC LIMIT 1")
    return cursor.fetchone()["id"]

@with_connection
def get_base_from_run(cursor, run_id):
    cursor.execute("SELECT gcvb_id FROM run WHERE id=?",[run_id])
    return cursor.fetchone()["gcvb_id"]

@with_connection
def add_run(cursor, gcvb_id, config_id):
    cursor.execute("INSERT INTO run(gcvb_id,config_id) VALUES (?,?)",[gcvb_id,config_id])
    return cursor.lastrowid

@with_connection
def add_tests(cursor, run, test_list, chain):
    tests=[(t["id"],run) for t in test_list]
    for t in test_list:
        cursor.execute("INSERT INTO test(name,run_id) VALUES(?,?)",[t["id"],run])
        t["id_db"]=cursor.lastrowid
        step=0
        parent = 0
        for task in t["Tasks"]:
            step += 1
            predecessor = step - 1 if chain else parent
            status = -3 if parent else -2 #Ready (-2) if parent is 0 else Pending (-3)
            cursor.execute("INSERT INTO task(step,parent,test_id,status) VALUES(?,?,?,?)",
                           [step, predecessor, t["id_db"], status])
            parent = step
            for valid in task.get("Validations",[]):
                step += 1
                predecessor = step - 1 if chain else parent
                cursor.execute("INSERT INTO task(step,parent,test_id) VALUES (?,?,?)",
                               [step,predecessor,t["id_db"]])


@with_connection
def start_test(cursor,run,test_id):
    cursor.execute("""UPDATE test
                      SET start_date = CURRENT_TIMESTAMP
                      WHERE id = ? AND run_id = ?""",[test_id,run])

@with_connection
def end_test(cursor, run, test_id):
    cursor.execute("""UPDATE test
                      SET end_date = CURRENT_TIMESTAMP
                      WHERE id = ? AND run_id = ?""",[test_id,run])

@with_connection
def start_task(cursor, test_id, step):
    cursor.execute("""UPDATE task
                      SET start_date = CURRENT_TIMESTAMP, status = -1
                      WHERE step = ? AND test_id = ?""", [step, test_id])

@with_connection
def end_task(cursor, test_id, step, exit_status):
    cursor.execute("""UPDATE task
                      SET end_date = CURRENT_TIMESTAMP, status = ?
                      WHERE step = ? AND test_id = ?""", [exit_status, step, test_id])

@with_connection
def start_run(cursor,run):
    #update only if there is no start date already.
    #Multiple launch scripts can be started, and we might not be the first.
    cursor.execute("""UPDATE run
                      SET start_date = CURRENT_TIMESTAMP
                      WHERE id = ?
                        AND start_date IS NULL""",[run])

@with_connection
def end_run(cursor,run):
    #update only if every tests is completed.
    #multiple scripts can be launched, we might not be the last.
    cursor.execute("""SELECT count(*) FROM test
                      WHERE run_id = ?
                        AND end_date IS NULL""",[run])
    count=cursor.fetchone()["count(*)"]
    if not(count):
        cursor.execute("""UPDATE run
                          SET end_date = CURRENT_TIMESTAMP
                          WHERE id = ?""",[run])

@with_connection
def add_metric(cursor, run_id, test_id, step, name, value):
    cursor.execute("INSERT INTO valid(metric,value,test_id,task_step) VALUES (?,?,?,?)",[name,value,test_id, step])

@with_connection
def get_last_run(cursor):
    cursor.execute("SELECT * from run ORDER BY id DESC LIMIT 1")
    res=cursor.fetchone()
    return (res["id"],res["gcvb_id"])

@with_connection
def get_run_infos(cursor, run_id):
    cursor.execute("SELECT * from run WHERE id = ?", [run_id])
    return cursor.fetchone()

@with_connection
def load_report(cursor, run_id):
    a="""SELECT metric, value, name
         FROM valid
         INNER JOIN test
         ON test_id=test.id
         WHERE test.run_id=(?)"""
    cursor.execute(a,[run_id])
    res={}
    for row in cursor.fetchall():
        res.setdefault(row["name"],{})[row["metric"]]=row["value"]
    return res

@with_connection
def load_report_n(cursor, run_id):
    a="""SELECT metric, value, name, task_step
         FROM valid
         INNER JOIN test
         ON test_id=test.id
         WHERE test.run_id=(?)"""
    cursor.execute(a,[run_id])
    res = defaultdict(lambda : defaultdict(dict))
    for t in cursor.fetchall():
        res[t["name"]][t["task_step"]][t["metric"]]=t["value"]
    return res

@with_connection
def save_files(cursor, run_id, test_id, file_list):
    request="""INSERT INTO files(filename,file, test_id)
               VALUES (?,?,?)"""

    for pattern in file_list:
        for file in glob.iglob(pattern):
            content=util.file_to_compressed_binary(file)
            cursor.execute(request,[file,content,test_id])

@with_connection
def save_yaml_cache(cursor, mtime, filename, res_dict):
    req1 = "DELETE FROM yaml_cache WHERE filename = ?"
    req2 = "INSERT INTO yaml_cache(mtime, filename, pickle) VALUES (?,?,?)"
    loaded_dict = util.pickle_obj_to_binary(res_dict)
    cursor.execute(req1, (filename,))
    cursor.execute(req2, (mtime, filename, loaded_dict))
    return res_dict

@with_connection
def load_yaml_cache(cursor, filename):
    request = "SELECT mtime, pickle FROM yaml_cache WHERE filename = ?"
    cursor.execute(request, (filename, ))
    res = cursor.fetchone()
    if res is None:
        return 0, None
    else:
        return res["mtime"], util.pickle_binary_to_obj(res["pickle"])

@with_connection
def get_tests(cursor, run_id):
    request="""SELECT id, name, start_date, end_date
               FROM test
               WHERE run_id = ?"""
    cursor.execute(request, [run_id])
    return cursor.fetchall()

@with_connection
def get_file_list(cursor, run_id, test_name):
    request="""SELECT filename
               FROM files
               INNER JOIN test ON test_id=test.id
               INNER JOIN run ON test.run_id=run.id
               WHERE run.gcvb_id = ? AND test.name = ?"""
    cursor.execute(request,[run_id,test_name])
    res=cursor.fetchall()
    return [f["filename"] for f in res]

@with_connection
def retrieve_file(cursor, run_id, test_name, filename):
    request="""SELECT file
               FROM files
               INNER JOIN test ON test_id=test.id
               INNER JOIN run ON test.run_id=run.id
               WHERE run.gcvb_id = ? AND test.name = ? AND filename = ?"""
    cursor.execute(request, [run_id,test_name, filename])
    return gzip.decompress(cursor.fetchone()["file"])

@with_connection
def retrieve_input(cursor, run):
    request="""SELECT yaml_file, modifier
               FROM gcvb
               INNER JOIN run ON gcvb.id=run.gcvb_id
               WHERE run.id=?"""
    cursor.execute(request, [run])
    res=cursor.fetchone()
    return (res["yaml_file"],res["modifier"])

@with_connection
def retrieve_test(cursor, run, test_id):
    request="""SELECT id, start_date, end_date
               FROM test
               WHERE name=? AND run_id=?"""
    cursor.execute(request,[test_id,run])
    res=dict(cursor.fetchone())
    request="""SELECT metric, value
               FROM valid
               WHERE test_id=?"""
    cursor.execute(request,[res["id"]])
    metrics=cursor.fetchall()
    res["metrics"]={m["metric"]:m["value"] for m in metrics}
    return res

@with_connection
def retrieve_history(cursor, test_id, metric_id):
    request="""SELECT metric, value, test.run_id as run, test.name as test_id
               FROM valid
               INNER JOIN test ON test.id=valid.test_id
               WHERE test.name=? AND valid.metric=?"""
    cursor.execute(request,[test_id,metric_id])
    res=cursor.fetchall()
    return res

@with_connection
def get_steps(cursor, run_id):
    request="""SELECT test.name, step, task.start_date, task.end_date, status
               FROM task
               INNER JOIN test ON test.id=task.test_id
               WHERE test.run_id = ?"""
    cursor.execute(request, [run_id])
    res = defaultdict(lambda : defaultdict(dict))
    for t in cursor.fetchall():
        res[t["name"]][t["step"]]=dict(t)
    return res