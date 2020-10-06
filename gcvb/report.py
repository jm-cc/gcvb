from . import model
import xml.etree.ElementTree as ET
from pprint import pformat

_HTML_TEMPLATE="""
<h1>GCVB results</h1>
<ul>
<li>Status: {status}</li>
<li>Total number of tests: {num_tests}</li>
<li>Number of completed tests: {num_compl}</li>
<li>Number of failure: {num_failure}</li>
<li>Start date: {start}</li>
<li>End date: {end}</li>
</ul>
<h2>Failed tests</h2>
<ul>"""

def html_report(run):
    status = run.str_status()
    num_tests = len(run.Tests)
    num_compl = 0
    failures = run.get_failures()
    num_failure = len(failures)
    start = run.start_date
    end = run.end_date
    strfailures = []
    for testid in sorted(run.Tests.keys()):
        t = run.Tests[testid]
        if t.failed:
            strfailures.append(f"<li>{testid}: {t.hr_result()}</li>")
        if t.completed:
            num_compl += 1
    return "\n".join([_HTML_TEMPLATE.format(**locals())]+strfailures+["</ul>"])


def str_report(run):
    rl = len(run.get_running_tests())
    tt = len(run.Tests)
    res = ""
    if not run.completed:
        res += f"{rl} are still running. (Completed : {tt-rl}/{tt})"
    if run.success:
        res += "Success!"
    if run.failed:
        res += f"Failure : {len(run.get_failures())} failed.\n\n"
        res += "Details of failures :\n"
        res += pformat(run.get_failures())
    return res
