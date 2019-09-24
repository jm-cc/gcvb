import dash
import dash_html_components as html
import dash_bootstrap_components as dbc
import gcvb.validation as val
import gcvb.db as db
import gcvb.yaml_input as yaml_input
import os
if __name__ == '__main__':
    from app import app
else:
    from ..app import app
from dash.dependencies import Input, Output

#Data
def data_preparation(run, test_id):
    run_summary=db.retrieve_test(run,test_id)
    base=yaml_input.load_yaml_from_run(run)

    data = {}
    data["Tasks"] = []
    data["test_id"] = test_id
    data["description"] = base["Tests"][test_id].get("description","")
    data["status"] = "success"

    for task in base["Tests"][test_id]["Tasks"]:
        d = {}
        data["Tasks"].append(d)
        d["executable"] = task["executable"]
        d["options"] = task["options"]
        d["metrics"] = []
        for validation in task.get("Validations",[]):
            v = {}
            d["metrics"].append(v)
            v["id"]=validation["id"]
            v["type"]=validation.get("type","file_comparison")
            v["tolerance"]=validation["tolerance"]
            v["distance"]=run_summary["metrics"].get(v["id"],"N/A") #Todo, it's ok only for file comparison...
            if v["distance"]=="N/A" and data["status"]!="failure":
                data["status"]="missing_validation"
            elif float(v["distance"])>float(v["tolerance"]):
                data["status"]="failure"
    return data

#Content
def metric_table(test_id,list_of_metrics):
    h=[("Metric","55%"),("Type","25%"),("Distance","8%"),("Target","8%"),("H","2%")]
    header=html.Tr([html.Th(col, style={"width" : width}) for col,width in h])

    rows = []
    for m in list_of_metrics:
        row = []
        for col in ["id", "type", "distance", "tolerance"]:
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
        if t["metrics"]:
            el_list.append(metric_table(data["test_id"],t["metrics"]))
    return html.Div([html.H5("Details"),*el_list])

#Page Generator
def gen_page(run_id, test_id):
    run_summary=db.retrieve_test(run_id,test_id)
    base=yaml_input.load_yaml_from_run(run_id)
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