# Copyright (c) 2014, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright 2014. Los Alamos National Security, LLC. This software was 
# produced under U.S. Government contract DE-AC52-06NA25396 for Los Alamos
# National Laboratory (LANL), which is operated by Los Alamos National 
# Security, LLC for the U.S. Department of Energy. The U.S. Government has 
# rights to use, reproduce, and distribute this software.  NEITHER THE 
# GOVERNMENT NOR LOS ALAMOS NATIONAL SECURITY, LLC MAKES ANY WARRANTY, EXPRESS
# OR IMPLIED, OR ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If 
# software is modified to produce derivative works, such modified software 
# should be clearly marked, so as not to confuse it with the version available
# from LANL.
# 
# Additionally, redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
# · Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# · Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# · Neither the name of Los Alamos National Security, LLC, Los Alamos National
#   Laboratory, LANL, the U.S. Government, nor the names of its contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY LOS ALAMOS NATIONAL SECURITY, LLC AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LOS ALAMOS NATIONAL 
# SECURITY, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import shutil
import re
import subprocess
import xml.etree.ElementTree as ET
import threading
import json
import sqlite3
import time
import functools
import logging
import config_reader

logging.basicConfig(level=logging.DEBUG)

config = config_reader.Config()

MACHINE_NAME = subprocess.check_output(["hostname"])[0:2]
DEPLOYMENT_PATH = config.get_deployment(MACHINE_NAME)
SPECIAL_VARS = ['machine', 'depends']


logging.info("Matriarch started on " + MACHINE_NAME)
logging.info("Using deployment directory " + DEPLOYMENT_PATH)

class Template:
    """ Represents a template for a matriarch run, and has capabilities for submitting MOAB jobs and creating working directories for jobs """
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.variables = set()
        self.global_variables = set()
        self.files = dict()

        self.var = re.compile("%%(.+?)%%")
        try:
            with open(os.path.join(path, "var_desc.json")) as f:
                self.var_desc = json.load(f)
        except:
            logging.error("Error reading variable description file for template %s at %s", self.name, self.path)

        for i in os.listdir(os.path.join(path, "_template")):
            self.__scan_file(os.path.join(path, "_template", i))

    def __add_variable(self, variable):
        self.variables.add(variable)

    def __add_global_variable(self, variable):
        self.global_variables.add(variable)

    def __scan_file(self, f):
        fname = os.path.basename(f)
        with open(f) as source:
            self.files[fname] = source.read()

        variables = set(self.var.findall(self.files[fname]))

        # remove special variables
        def is_special_var(x):
            return x.lower() in SPECIAL_VARS

        for v in filter(lambda x: not is_special_var(x), variables):
            self.__add_variable(v)

    def __deploy(self, name, params, removePromptFunc):
        dep_dir = os.path.join(DEPLOYMENT_PATH, self.name, name)
        if os.path.isdir(dep_dir):
            result = removePromptFunc("Directory " + name + " exists. Remove it? (y/n) ")
            if result == "y":
                shutil.rmtree(dep_dir)
            elif result == "n":
                return None
            else:
                print("Invalid option entered. Exiting.")
                return None

        logging.debug("Creating deployment directory %s", dep_dir)
        os.makedirs(dep_dir)
        for f in self.files:
            toWrite = self.files[f]
            for v in params:
                toWrite = toWrite.replace("%%" + str(v).upper() + "%%", str(params[v]))

            with open(os.path.join(dep_dir, f), 'w') as dest:
                dest.write(toWrite)
                

        # find the proper deploy script
        # if file "deploy" exists, execute it with bash
        # if file "deploy.py" exists, execute it with python
        scripts = []
        scripts.append(['bash', str(os.path.join(dep_dir, "deploy"))])
        scripts.append(['python', str(os.path.join(dep_dir, "deploy.py"))])
        
        from util import first
        toR = first(lambda x: os.path.exists(x[1]), scripts)

        return toR

    def __extract(self, name):
        script_dir = os.path.join(DEPLOYMENT_PATH, self.name, name)
        result = subprocess.check_output(['python', 'extract'], cwd=script_dir)
        return json.loads(result)

    def get_extract_func_for(self, name):
        return functools.partial(self.__extract, name)

    def get_variables(self):
        return self.variables

    def get_variable_description(self, var):
        try:
            return self.var_desc[var]
        except:
            return "A description for this variable was not found in the template's var_desc.json file"

    def get_name(self):
        return self.name

    def submit_job(self, name, params, removePromptFunc=raw_input):
        params['NAME'] = name
        script = self.__deploy(name, params, removePromptFunc)

        if not script:
            return None
        logging.debug("Deploying job %s by running script %s", name, script)

        result = subprocess.check_output(script).rstrip().lstrip()
        try:
            result = int(result)
            return MatriarchJob(name, params, result, self, extractFunc=functools.partial(self.__extract, name))
        except ValueError:
            print("Expected the deployment script to return a job ID, instead got:", result)

        return None


        
class TemplateScanner:
    """ scans a given directory for templates and then makes those templates available via `get_templates()`"""
    def __init__(self):
        self.templates = []

    def __test_subdir(self, path):
        items = os.listdir(path)
        return "_template" in items

    def __process_subdir(self, path):
        if not self.__test_subdir(path): return
        logging.info("Found template at %s", path)
        t = Template(os.path.basename(path), path)
        self.templates.append(t)

    def scan(self, path):
        path = os.path.expanduser(path)

        for i in os.listdir(path):
            i = os.path.join(path, i)
            if os.path.isdir(i):
                logging.debug("Testing subdirectory for templates: %s", i)                
                self.__process_subdir(i)

    def get_templates(self):
        return self.templates

    def get_template_by_name(self, name):
        for t in self.templates:
            if t.get_name() == name:
                return t

        return None

class MOABJob:
    """ provides functionality and information about a given MOAB job """

    def __init__(self, job_id, info=None):
        self.job_id = job_id
        self.info = info
        self.info_lock = threading.RLock()
        if not info:
            self.refresh_info()
        self.complete_callbacks = []

    def refresh_info(self):
        try:
            result = subprocess.check_output(["checkjob", "--xml", str(self.job_id)])
        except subprocess.CalledProcessError:
            with self.info_lock:
                self.info['CompletionCode'] = -2
                return

        root = ET.fromstring(result)

        do_complete_hooks = False
        currently_complete = self.is_complete() or self.is_canceled()

        with self.info_lock:
            self.info = root[0].attrib
            self.info['hostname'] = subprocess.check_output(["hostname"])
            do_complete_hooks = (not currently_complete) and self.is_complete()
        

        return do_complete_hooks

    def add_complete_callback(self, func):
        self.complete_callbacks.append(func)

    def get_id(self):
        return self.job_id

    def is_complete(self):
        with self.info_lock:
            if self.info == None:
                return None
            return self.info['EState'] == "Completed"

    def is_running(self):
        with self.info_lock:
            if self.info == None:
                return None
            return self.info['EState'] == "Running"

    def is_waiting(self):
        with self.info_lock:
            if self.info == None:
                return None
            return self.info['EState'] == "Idle" or self.info['EState'] == "Deferred"

    def is_canceled(self):
        with self.info_lock:
            if self.info == None:
                return None
            return self.info['EState'] == "Removed"

    def has_error(self):
        with self.info_lock:
            if self.info == None:
                return None

            if 'CompletionCode' not in self.info:
                return False

            if self.is_canceled():
                return False

            return self.info['CompletionCode'] != 0

    def get_submission_time(self):
        with self.info_lock:
            if self.info == None:
                return None
            return self.info['SubmissionTime']

    def get_start_time(self):
        with self.info_lock:
            if self.info == None:
                return None
            if "StartTime" in self.info:
                return self.info['StartTime']
            return None

    def get_completion_time(self):
        with self.info_lock:
            if self.info == None:
                return None
            if "CompletionTime" in self.info:
                return self.info['CompletionTime']
            return None

    def get_duration(self):
        s = self.get_start_time()
        f = self.get_completion_time()
        
        if s and f:
            return int(f) - int(s)

        return None

    def get_state(self):
        with self.info_lock:
            if self.info == None:
                return None

            return self.info['EState']

    def get_user(self):
        with self.info_lock:
            if self.info == None:
                return None

            return self.info['User']

    def get_hostname(self):
        with self.info_lock:
            if self.info == None:
                return None

            return self.info['hostname']

    def json(self):
        self.info['jobid'] = self.get_id()
        return json.dumps(self.info)
          
class MatriarchJob(MOABJob):
    """ wraps MOABJob, providing additional fields for Matriarch spceific stuff, like job names and parameters """
    def __init__(self, name, params, jobid, template, info=None, extractFunc=None):
        if info:
            MOABJob.__init__(self, jobid, info=info['moab'])
        else:
            MOABJob.__init__(self, jobid)
        self.name = name
        self.params = params
        self.template = template
        self.extract_func = extractFunc
        self.orig_jobid = jobid
        self.resub_count = 0

    def extract_output(self):
        if self.extract_func:
            up_with = self.extract_func()
        else:
            up_with = self.template.get_extract_func_for(self.name)()

        self.params.update(up_with)

    def get_id(self):
        return self.orig_jobid

    def get_name(self):
        return self.name

    def get_template_name(self):
        return self.template.get_name()
    
    def get_params(self):
        return self.params

    def get_state(self):
        if self.has_error():
            return "Error (" + str(self.resub_count) + ")"

        return MOABJob.get_state(self)
                

    def has_error(self):
        with self.info_lock:

            if self.info == None:
                return None

            if 'failed' in self.params:
               return self.params['failed']
            
            if 'CompletionCode' not in self.info:
                return False

            

            return self.info['CompletionCode'] != 0

    def resubmit(self):
        if self.resub_count == 3:
            # don't resubmit
            logging.error("Job %d has failed 3 times. Won't resubmit.", self.get_id())
            return False

        self.resub_count += 1
        # TODO: resub
        return True

        

    def json(self):
        toR = {}
        toR['name'] = self.get_name()
        toR['params'] = self.get_params()
        toR['resubs'] = self.resub_count
        toR['template_name'] = self.get_template_name()
        
        return json.dumps({'matriarch': toR, 'moab': json.loads(MOABJob.json(self))})

    @staticmethod
    def from_json(d, templ_lookup):
        obj = json.loads(d)
        name = obj['matriarch']['name']
        params = obj['matriarch']['params']
        jobid = obj['moab']['jobid']
        t_name = obj['matriarch']['template_name']
        template = templ_lookup(t_name)
        j = MatriarchJob(name, params, jobid, template, info=obj)
        j.resub_count = obj['matriarch']['resubs']
        return j


class MatriarchBackend:
    """ The main backend to Matriarch. Automatically imports templates from the CWD, and makes them available. Jobs submitted via the backend are automatically monitored. Also saves completed runs into the database."""
    def __init__(self):
        self.ts = TemplateScanner()
        for td in config.get_template_dirs():
            self.ts.scan(td)

    def __enter__(self):
        self.db = Database(self.ts.get_template_by_name, MACHINE_NAME)
        self.jm = JobMonitor(self.db)
        self.prm = PrerunMonitor(self.db, self.ts.get_template_by_name)

        return self

    def __exit__(self, ty, value, traceback):
        self.jm.close()
        self.db.close()
        self.prm.close()

    def get_templates(self):
        return self.ts.get_templates()

    def get_template_index_by_name(self, name):
        for t, x in zip(self.get_templates(), range(len(self.get_templates()))):
            if t.get_name() == name:
                return x

        return None;
           
    def get_job_by_id(self, jobid):
        job = self.db.get_job_by_id(jobid)
        return job

    def submit_job(self, tmpl_name, name, params, machine=MACHINE_NAME, depends_on=[]):
        self.db.insert_prerun({'name': name, 'template': tmpl_name, 'data': params, 'machine': machine, 'depends': depends_on})

    def get_jobs(self):
        toR = []
        toR.extend(self.db.get_runs())
        toR.extend(self.db.get_jobs())
        return toR

    def delete_job_by_id(self, jobid):
        self.db.delete_job(jobid)

    def get_jobs_for_template(self, template):
        return self.db.get_jobs_for_template(template);
        
    def get_machines(self):
        return config.get_machines()


class PrerunMonitor:
    def __init__(self, db, templ_lookup):
        self.db = db;
        self.tlf = templ_lookup
        self.exitEvent = threading.Event()

        self.var = re.compile("@@(.+?)@@")

        self.t = threading.Thread(name="prerun monitor", target=self.__run_thread)
        logging.debug("Starting prerun monitor thread")
        self.t.start()

    def __run_thread(self):
        while True:
            if self.exitEvent.is_set():
                break;

            try: 
                self.__monitor_loop()
            except Exception as e:
                logging.error("Error in prerun monitor thread: " + str(e))
                import traceback
                traceback.print_exc()

    def __evaluate_depends(self, depends):
        jobs = self.db.get_jobs(limit=1000)
        jobs.extend(self.db.get_runs())
        def name_to_id(job_name):
            if job_name[0] == "#":
                # it's already a job id
                return job_name

            pr = self.db.get_prerun_by_name(job_name)
            if pr:
                logging.debug("Found prerun matching dependency name: %s", job_name)
                return job_name # job dependency is still in the prerun phase. Leave it as a name.

            for j in jobs:
                if j.get_name() == job_name:
                    return "#" + str(j.get_id())

            logging.debug("No prerun or job found for dependency: %s", job_name)
            # well, hopefully it'll show up in the future.
            return job_name

        return list(map(name_to_id, depends))


    def __monitor_loop(self):
        toSub = self.db.get_prerun()

        if toSub == None:
            return



        toSub['depends'] = self.__evaluate_depends(toSub['depends'])

        all_depends = True
        for depend in toSub['depends']:
            if depend[0] != "#":
                # still waiting on a prerun
                logging.debug("Prerun %d is still waiting on another prerun named %s", toSub['id'], depend)
                all_depends = False
                break

            # check to see if this dependency is complete
            job = self.db.get_job_by_id(depend[1:]) # cut off the leading #
            if not job.is_complete():
                logging.debug("Prerun %d is waiting on job %s", toSub['id'], depend)
                all_depends = False
                break

        # update the prerun with possible job IDs for dependencies that we found
        self.db.insert_prerun(toSub)

        if not all_depends:
            return

        logging.info("Deploying prerun %d", toSub['id'])

        template = self.tlf(toSub['template'])
        toSub['data'] = self.__replace_globals(toSub['data'])
        job = template.submit_job(toSub['name'], toSub['data'], removePromptFunc=lambda x: "y")
        self.db.delete_prerun(toSub['id'])
        self.db.insert_run(job)

    def __replace_globals(self, data):
        for k in data:
            if k.lower() in SPECIAL_VARS:
                continue 
            vars_used = self.var.findall(str(data[k]))
            if len(vars_used) == 0:
                continue
            for var in vars_used:
                value = self.db.get_global(var)
                if not value:
                    logging.error("Used global variable %s, but it is not set.", var)
                    return None

                data[k] = data[k].replace("@@" + var + "@@", value)
        return data
            

    def close(self):
        self.exitEvent.set()


class JobMonitor:
    def __init__(self, db):
        self.db = db
        self.exitEvent = threading.Event()

        self.callbacks = {}
        self.cbLock = threading.RLock()


        self.t = threading.Thread(target=self.__run_thread)
        logging.debug("Starting job monitoring thread")
        self.t.start()

    def add_callback_for_job(self, jobid, cb):
        with self.cbLock:
            if jobid not in self.callbacks:
                self.callbacks[jobid] = []
            self.callbacks[jobid].append(cb)
            

    def __run_thread(self):
        while True:
            if self.exitEvent.is_set():
                break;

            try:
                self.__monitor_loop()
            except Exception as e:
                logging.error("Error in job monitor thread: " + str(e))
                import traceback
                traceback.print_exc()

    def __monitor_loop(self):
        logging.debug("Job monitoring thread started")
        local = threading.local()

        last = 0
        last_time = 0

        while True:
            if self.exitEvent.is_set():
                break;

            job = self.db.get_last_incomplete_job()
            if job == None:
                continue

            if job.get_id() == last and (time.time() - last_time) <= 10:
                continue

            last = job.get_id()
            last_time = time.time()

            logging.debug("Checking job %d in the monitor thread", job.get_id())

            just_completed = job.refresh_info()

            # refresh the job in the DB
            self.db.insert_run(job)

            if just_completed:
                logging.debug("Doing data extraction for job %d...", job.get_id())
                job.extract_output()

                if 'MATRIARCH_SET_GLOBALS' in job.get_params():
                    logging.debug("Processing globals set by job %d...", job.get_id())
                    for k, v in job.get_params()['MATRIARCH_SET_GLOBALS'].items():
                        logging.debug("Setting global variable %s to %s", k, v)
                        self.db.insert_global(k, v)

                logging.debug("Processing callbacks for job %d...", job.get_id())
                jid = job.get_id()
                with self.cbLock:
                    cbs = []
                    if jid in self.callbacks:
                        cbs = self.callbacks[jid]
                        del self.callbacks[jid]

                for c in cbs:
                    c(job)


            if job.has_error():
                logging.info("Job %d failed. Resubmitting...", job.get_id())
                if job.resubmit():
                    self.db.insert_run(job)
                    continue
                else:
                    # won't resubmit
                    self.db.insert_job(job)
                    self.db.remove_run(job)
                    continue

            if job.is_complete() or job.is_canceled():
                logging.info("Job %d complete, removing it from runs and adding it to jobs", job.get_id())
                self.db.insert_job(job)
                self.db.remove_run(job)


    def close(self):
        self.exitEvent.set()
            
class Database:
    """ a class to take care of some database functionality. Implemented on it's own thread with very course locking """
    def __init__(self, templ_lookup, machine_name):
        self.newData = threading.Condition()
        self.toInsert = []
        self.toQuery = []
        self.toInsertRuns = []
        self.toInsertPreruns = []
        self.toInsertGlobals = []

        self.cqLock = threading.Condition()
        self.completeQueries = {}

        self.exitEvent = threading.Event()
        self.t = threading.Thread(name="db thread", target=self.__db_loop)
        self.t.start()

        self.qcLock = threading.Lock()
        self.q_count = 0

        self.tlf = templ_lookup
        self.machine = machine_name

    def close(self):
        self.exitEvent.set()

    def __db_loop(self):
        with sqlite3.connect('matriarch.db', isolation_level = None) as db:
            try:
                db.cursor().execute("SELECT * FROM job;")
            except:
                db.cursor().execute("CREATE TABLE job (id INTEGER PRIMIARY KEY, template TEXT, data TEXT);")


            try: 
                db.cursor().execute("SELECT * FROM run;")
            except:
                db.cursor().execute("CREATE TABLE run (id INTEGER PRIMARY KEY, machine TEXT, state INTEGER, data TEXT, last_checked INTEGER);")
            
            try:
                db.cursor().execute("SELECT * FROM prerun")
            except:
                db.cursor().execute("CREATE TABLE prerun (id INTEGER PRIMARY KEY AUTOINCREMENT, machine TEXT, name TEXT, template TEXT, data TEXT, depends TEXT, last_checked INTEGER)")

            try:
                db.cursor().execute("SELECT * FROM globals")
            except:
                db.cursor().execute("CREATE TABLE globals (key TEXT PRIMARY KEY, value TEXT)")

            while True:
                if self.exitEvent.is_set():
                    return;

                with self.newData as locked:
                    while len(self.toInsert) == 0 and len(self.toQuery) == 0:
                        self.newData.wait(0.5)
                        if self.exitEvent.is_set():
                            return;

                    self.__check_for_inserts(db)
                    self.__check_for_inserts_runs(db)
                    self.__check_for_inserts_prerun(db)
                    self.__check_for_inserts_globals(db)
                    self.__check_for_queries(db)

    def __check_for_inserts_globals(self, db):
        if len(self.toInsertGlobals) != 0:
            c = db.cursor()
            glob = self.toInsertGlobals.pop(0)
            c.execute("REPLACE INTO globals (key, value) VALUES(?, ?)", [glob[0], glob[1]])
            db.commit()

    def __check_for_inserts_runs(self, db):
        if len(self.toInsertRuns) != 0:
            c = db.cursor()
            run = self.toInsertRuns.pop(0)
            c.execute("REPLACE INTO run (id, state, machine, data, last_checked) VALUES(?, ?, ?, ?, ?);", 
                      [run.get_id(), run.get_state(),
                       self.machine, run.json(), int(time.time())])
            db.commit()

    def __check_for_inserts_prerun(self, db):
        if len(self.toInsertPreruns) != 0:
            c = db.cursor()
            run = self.toInsertPreruns.pop(0)
            if 'id' not in run:
                c.execute("INSERT INTO prerun (machine, name, template, data, depends, last_checked) VALUES(?, ?, ?, ?, ?, ?);",
                          [run['machine'], run['name'], run['template'], json.dumps(run['data']), json.dumps(run['depends']), int(time.time())])
            else:
                c.execute("REPLACE INTO prerun (id, machine, name, template, data, depends, last_checked) VALUES(?, ?, ?, ?, ?, ?, ?);",
                          [run['id'], run['machine'], run['name'], run['template'], json.dumps(run['data']), json.dumps(run['depends']), int(time.time())])

            db.commit()


    def __check_for_inserts(self, db):
        if len(self.toInsert) != 0:
            # data is available!
            c = db.cursor()
            job = self.toInsert.pop(0)
            c.execute("INSERT INTO job (id, template, data) VALUES (?, ?, ?);", [job.get_id(), job.get_template_name(), job.json()])
            db.commit()

    def __check_for_queries(self, db):
        if len(self.toQuery) != 0:
            # need to perform query
            c = db.cursor()
            q = self.toQuery.pop(0)

            c.execute(q['sql'], q['values'])
            results = c.fetchall()
            db.commit()

            with self.cqLock:
                self.completeQueries[q['key']] = results
                self.cqLock.notify()


    def __do_query(self, query, values):
        with self.qcLock:
            qid = self.q_count
            self.q_count += 1

        with self.newData:
            self.toQuery.append({'sql': query, 'values': values, 'key': qid})
            self.newData.notify()

        with self.cqLock:
            while qid not in self.completeQueries:
                if self.exitEvent.is_set():
                    return None

                self.cqLock.wait(1.0)
            toR = self.completeQueries[qid]
            del self.completeQueries[qid]
            return toR

    def insert_run(self, job):
        with self.newData:
            self.toInsertRuns.append(job)
            self.newData.notify()

    def insert_prerun(self, prerun):
        with self.newData:
            self.toInsertPreruns.append(prerun)
            self.newData.notify()

    def insert_job(self, job):
        with self.newData:
            self.toInsert.append(job)
            self.newData.notify()

    def insert_global(self, key, value):
        with self.newData:
            self.toInsertGlobals.append((key, value))
            self.newData.notify()

    def remove_run(self, job):
        self.__do_query("DELETE FROM run WHERE id = ?", [job.get_id()])

    def delete_job(self, jobid):
        self.__do_query("DELETE FROM run WHERE id = ?", [jobid])
        self.__do_query("DELETE FROM job WHERE id = ?", [jobid])

    def delete_prerun(self, prerunid):
        self.__do_query("DELETE FROM prerun WHERE id = ?", [prerunid])

    def get_jobs(self, limit=100):
        jobs = self.__do_query("SELECT data FROM job ORDER BY id DESC LIMIT ?", [limit])
        if jobs == None:
            return None
        jobs = map(lambda x: MatriarchJob.from_json(x[0], self.tlf), jobs)
        return jobs

    def get_job_by_id(self, jobid):
        job = self.__do_query("SELECT data FROM job WHERE id=?", [jobid])
        if job == None or len(job) == 0:
            # maybe it is a run
            job = self.__do_query("SELECT data FROM run WHERE id=?", [jobid])

            if len(job) == 0:
                return None

        job = MatriarchJob.from_json(job[0][0], self.tlf)
        return job

    def get_jobs_for_template(self, template):
        jobs = self.__do_query("SELECT data FROM job WHERE template=?", [template])
        if jobs == None:
            return None
        jobs = map(lambda x: MatriarchJob.from_json(x[0], self.tlf), jobs)
        return jobs

    def get_runs(self):
        jobs = self.__do_query("SELECT data FROM run;", [])
        if jobs == None:
            return None
        jobs = map(lambda x: MatriarchJob.from_json(x[0], self.tlf), jobs)
        return jobs

    def get_last_incomplete_job(self):
        curr_time = time.time()
        job = self.__do_query("SELECT data FROM run WHERE state != 255 AND (? - last_checked > 20) AND machine = ? ORDER BY last_checked DESC LIMIT 1;", [curr_time, self.machine])
        if job == None or len(job) == 0:
            return None
        job = MatriarchJob.from_json(job[0][0], self.tlf)
        return job

    def get_prerun_by_name(self, name):
        prerun = self.__do_query("SELECT id, template, data, depends from prerun WHERE name = ? LIMIT 1;", [name])
        if prerun == None or len(prerun) == 0:
            return None

        prerun = prerun[0]
        return {'id': prerun[0], 'name': name, 'template': prerun[1], 'data': json.loads(prerun[2]), 'depends': json.loads(prerun[3])}

    def get_prerun(self):
        prerun = self.__do_query("SELECT id, name, template, data, depends FROM prerun WHERE machine = ? AND (? - last_checked > 20) ORDER BY last_checked DESC LIMIT 1;", [self.machine, time.time()])

        if prerun == None or len(prerun) == 0:
            return None

        prerun = prerun[0]
        toR = {'id': prerun[0], 'name': prerun[1], 'template': prerun[2], 'data': json.loads(prerun[3]), 'depends': json.loads(prerun[4]), 'machine': self.machine}
        return toR

    def get_global(self, key):
        value = self.__do_query("SELECT value FROM globals WHERE key = ?;", [key])
        
        if value == None or len(value) == None:
            return None

        return value[0][0]
