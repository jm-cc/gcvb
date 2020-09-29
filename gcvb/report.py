from . import model
import xml.etree.ElementTree as ET
from pprint import pformat


def html_report(run):
    root = ET.Element("html")
    body = ET.SubElement(root, "body")
    title = ET.SubElement(body, "h1")
    title.text = "GCVB Result"
    sumary = ET.SubElement(body, "p")
    sumary.text = run.str_status()
    result_table = ET.SubElement(body, "table")

    for test_id, test in run.Tests.items():
        line = ET.Element("tr")
        test_str = ET.SubElement(line, "td")
        test_str.text = test_id
        result = ET.SubElement(line, "td")
        result.text = test.hr_result()
        result_table.append(line)

    return ET.tostring(root)

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
