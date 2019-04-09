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
    return str(base["Tests"][test_id])

#Content

def metric_table(list_of_metrics):
    header=html.Tr([html.Th(col) for col in ["Metric","Type","Distance","Target"]])

    rows = []
    for m in list_of_metrics:
        row = []
        for col in ["id", "type", "distance", "tolerance"]:
            cell = html.Td(m[col])
            row.append(cell)

        style=""
        if (float(m["distance"])>float(m["tolerance"])):
            style="table-danger"

        rows.append(html.Tr(row,className=style))
    return html.Table(html.Tbody([header]+rows),className="table table-sm table-bordered")

def summary_panel(data):
    status_str=html.Span("Success",className="badge badge-success")
    if data["status"]!="success":
        status_str=html.Span("Failure",className="badge badge-danger")

    title=html.H1([data["test_id"]+" ",status_str])
    description_block=html.Div([html.H5("Description"),html.P(data["description"])],id="description")

    result_line=html.Tr([html.Th("Result"),(html.Td(data["result"]))])
    time_line=html.Tr([html.Th("Elapsed time (s)"),(html.Td(data["time"]))])

    #Table
    table=html.Table(html.Tbody([result_line,time_line]), className="table table-sm")

    #Panel
    panel_header=html.Div(html.H3("Summary",className="panel-title"),className="panel panel-heading")
    panel=html.Div([panel_header,table],className="panel panel-default")


    return dbc.Container([title,description_block])

#Page Generator
def gen_page(run_id, test_id):
    run_summary=db.retrieve_test(run_id,test_id)
    base=yaml_input.load_yaml_from_run(run_id)
    r=db.load_report(run_id)
    report=val.Report(base,r)
    return dbc.Container(metric_table(report.success[test_id]))
    #return dbc.Container(str((run_summary,base["Tests"][test_id])))

    data={}
    data["description"]="Fake description"
    data["result"]="Success!"
    data["time"]="666"
    data["test_id"]="<placeholder_testname>"
    data["status"]="missing_validation"
    return summary_panel(data)


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