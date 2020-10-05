import dash
import dash_html_components as html
import dash_bootstrap_components as dbc
import gcvb.db as db
import gcvb.job as job
import gcvb.yaml_input as yaml_input
import os
if __name__ == '__main__':
    from app import app
else:
    from ..app import app
from dash.dependencies import Input, Output
from gcvb.loader import loader as loader
import gcvb.model as model

def _fill_files(d, taskorval, ajc, fromtype):
    d[fromtype] = [
        {
            "id": f["id"],
            "file": job.format_launch_command(f["file"], loader.config, ajc),
        }
        for f in taskorval.get("serve_" + fromtype, [])
    ]

#Data
def data_preparation(run, test_id):
    test = run.Tests[test_id]

    data = {}
    data["base_id"] = run.base_id
    data["Tasks"] = []
    data["test_id"] = test_id
    data["description"] = test.raw_dict.get("description","")

    for i,task_obj in enumerate(test.Tasks):
        task = task_obj.raw_dict #FIXME quickway to have old behaviour
        ajc = {}
        job.fill_at_job_creation_task(ajc, task, f"{test_id}_{i}", loader.config)
        d = {}
        data["Tasks"].append(d)
        d["executable"] = task["executable"]
        d["options"] = task["options"]
        d["metrics"] = []
        _fill_files(d, task, ajc, "from_results")
        _fill_files(d, task, ajc, "from_db")
        for validation in task_obj.Validations:
            job.fill_at_job_creation_validation(ajc, validation.raw_dict,
                                                loader.data_root,  test.raw_dict["data"],
                                                loader.config, loader.references)
            for metric_id, metric in validation.expected_metrics.items():
                v = {}
                d["metrics"].append(v)
                v["id"]=metric_id
                v["type"]=metric.type
                v["tolerance"]=metric.tolerance
                if metric_id in validation.recorded_metrics:
                    v["distance"] = metric.distance(validation.recorded_metrics[v["id"]])
                else:
                    v["distance"] = "N/A (Missing metric)"
                _fill_files(v, validation.raw_dict, ajc, "from_results")
                _fill_files(v, validation.raw_dict, ajc, "from_db")
            for metric_id, recorded_value in validation.get_untracked_metrics().items():
                m = {}
                d["metrics"].append(m)
                m["id"] = metric_id
                m["type"] = "untracked"
                m["tolerance"] = "Untracked"
                m["distance"] = recorded_value
                m["from_results"]=[]
    return data


def _metrics_file_links(m, data):
    test_id = data["test_id"]
    l = []
    for t, url in [("from_results", "files"), ("from_db", "dbfiles")]:
        for f in m[t]:
            l.append(
                html.A(
                    href=f"/{url}/{data['base_id']}/{test_id}/{f['file']}",
                    children=f["id"],
                )
            )
            l.append(", ")
    return [" ("] + l[:-1] + [")"] if l else l


#Content
def metric_table(data, list_of_metrics):
    test_id = data["test_id"]

    h=[("Metric","55%"),("Type","25%"),("Distance","8%"),("Target","8%"),("H","2%")]
    header=html.Tr([html.Th(col, style={"width" : width}) for col,width in h])

    rows = []
    for m in list_of_metrics:
        row = [html.Td([m["id"]] + _metrics_file_links(m, data))]
        for col in ["type", "distance", "tolerance"]:
            cell = html.Td(m[col])
            row.append(cell)
        #link to history
        link="/history/{}/{}".format(test_id,m["id"])
        cell = html.Td(html.A(href=link, children="H"))
        row.append(cell)

        style=""
        if (m["distance"]=="N/A (Missing metric)"):
            style="table-warning"
        elif(m["tolerance"]=="Untracked"):
            style="table-info"
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
        el_list.append(html.Span(_metrics_file_links(t, data)))
        if t["metrics"]:
            el_list.append(metric_table(data, t["metrics"]))
    return html.Div([html.H5("Details"),*el_list])

def status_to_badge(run):
    if run.failed:
        return html.Span("Failure",className="badge badge-danger")
    if not(run.completed):
        return html.Span("In progress",className="badge badge-info")
    if run.success:
        return html.Span("Success",className="badge badge-success")
    raise ValueError("Unexpected")

#Page Generator
def gen_page(run_id, test_id):
    run = model.Run(run_id)
    data=data_preparation(run,test_id)

    #Title + Badge
    status_str=status_to_badge(run)

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