import dash
import dash_html_components as html
import dash_bootstrap_components as dbc
import gcvb.validation as val
import gcvb.db as db
import gcvb.job as job
import gcvb.yaml_input as yaml_input
import os
if __name__ == '__main__':
    from app import app
else:
    from ..app import app
from dash.dependencies import Input, Output
from .loader import loader

#Data
def data_preparation(run, test_id):
    run_summary=db.retrieve_test(run,test_id)
    base = loader.load_base(run)

    test = base["Tests"][test_id]

    data = {}
    data["base_id"] = db.get_base_from_run(run)
    data["Tasks"] = []
    data["test_id"] = test_id
    data["description"] = test.get("description","")
    data["status"] = "success"

    for i,task in enumerate(test["Tasks"]):
        ajc = {}
        job.fill_at_job_creation_task(ajc, task, f"{test_id}_{i}", loader.config)
        d = {}
        data["Tasks"].append(d)
        d["executable"] = task["executable"]
        d["options"] = task["options"]
        d["metrics"] = []
        d["from_results"] = [{"id" : f["id"],
                              "file" : job.format_launch_command(f["file"], loader.config, ajc)}
                             for f in task.get("serve_from_results",[])]
        for validation in task.get("Validations",[]):
            job.fill_at_job_creation_validation(ajc, validation,
                                                loader.data_root,  test["data"],
                                                loader.config, loader.references)
            v = {}
            d["metrics"].append(v)
            v["id"]=validation["id"]
            v["type"]=validation.get("type","file_comparison")
            v["tolerance"]=validation["tolerance"]
            v["distance"]=run_summary["metrics"].get(v["id"],"N/A") #Todo, it's ok only for file comparison...
            if v["distance"]=="N/A":
                data["status"]="failure"
            elif float(v["distance"])>float(v["tolerance"]):
                data["status"]="failure"
            v["from_results"] = [{"id" : f["id"],
                                  "file" : job.format_launch_command(f["file"], loader.config, ajc)}
                                 for f in validation.get("serve_from_results",[])]
    return data

#Content
def metric_table(data, list_of_metrics):
    test_id = data["test_id"]

    h=[("Metric","55%"),("Type","25%"),("Distance","8%"),("Target","8%"),("H","2%")]
    header=html.Tr([html.Th(col, style={"width" : width}) for col,width in h])

    rows = []
    for m in list_of_metrics:
        row = []

        if m["from_results"]:
            l = []
            for f in m["from_results"]:
                l.append(html.A(href=f"/files/{data['base_id']}/{test_id}/{f['file']}", children=f["id"]))
                l.append(", ")
            cell = html.Td([m["id"]]+[" ("]+l[:-1]+[")"])
        else:
            cell = html.Td(m["id"])
        row.append(cell)

        for col in ["type", "distance", "tolerance"]:
            cell = html.Td(m[col])
            row.append(cell)
        #link to history
        link="/history/{}/{}".format(test_id,m["id"])
        cell = html.Td(html.A(href=link, children="H"))
        row.append(cell)

        style=""
        if (m["distance"]=="N/A"):
            style="table-warning"
        elif (float(m["distance"])>float(m["tolerance"])):
            style="table-danger"

        rows.append(html.Tr(row,className=style))
    return html.Table(html.Tbody([header]+rows,className="table table-sm table-bordered"))

def summary_panel(data):
    description_block=html.Div([html.H5("Description"),html.P(data["description"])],id="description")
    return description_block

def details_panel(data):
    el_list = []
    for c,t in enumerate(data["Tasks"], 1):
        el_list.append(html.H6("{!s} - {} {}".format(c,t["executable"],t["options"])))
        if t["from_results"]:
            l = ["Files :"]
            for f in t["from_results"]:
                l.append(" ")
                l.append(html.A(href=f"/files/{data['base_id']}/{data['test_id']}/{f['file']}", children=f["id"]))
            el_list.append(html.Span(l))
        if t["metrics"]:
            el_list.append(metric_table(data, t["metrics"]))
    return html.Div([html.H5("Details"),*el_list])

#Page Generator
def gen_page(run_id, test_id):
    run_summary=db.retrieve_test(run_id,test_id)
    base = loader.load_base(run_id)
    r=db.load_report(run_id)
    report=val.Report(base,r)
    #return dbc.Container(metric_table(report.success[test_id]))
    #return dbc.Container(str((run_summary,base["Tests"][test_id])))

    data=data_preparation(run_id,test_id)

    #Title + Badge
    status_str=html.Span("Success",className="badge badge-success")
    if data["status"]!="success":
        status_str=html.Span("Failure",className="badge badge-danger")
    title=html.H1([data["test_id"]+" ",status_str])
    res=dbc.Container([title,summary_panel(data),details_panel(data)])
    return res


#Page
layout = html.Div(id="test-content")

@app.callback(Output('test-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    page=pathname.split("/")
    if len(page)<4:
        return '404'
    run,test_id=page[2],page[3]
    return gen_page(run,test_id)