import dash
import dash_html_components as html
import dash_bootstrap_components as dbc
import gcvb.db as db
import gcvb.yaml_input as yaml_input
import os
from gcvb.loader import loader as loader
import gcvb.model as model
import dash_defer_js_import as dji

if __name__ == '__main__':
    from app import app
else:
    from ..app import app
from dash.dependencies import Input, Output

# Data
def data_preparation(run_id):
    run = model.Run(run_id)
    res={"id" : [], "description" : [], "result" : [], "cpu time (s)": []}
    for test_id,test in run.Tests.items():
        res["id"].append(test_id)
        res["description"].append(test.raw_dict.get("description", ""))
        res["result"].append(test.hr_result())
        res["cpu time (s)"].append(test.cpu_time())
    return res

# View
def Table(report, run_id, columns=None):
    rows = []
    if not columns:
        columns = report.keys()
    for i in range(len(report["id"])):
        row = []
        for col in columns:
            value = report[col][i]
            if col == 'id':
                cell = html.Td(html.A(href="/test/"+str(run_id)+"/"+value, children=value))
            else:
                cell = html.Td(children=value)
            row.append(cell)
        rows.append(html.Tr(row))
    rows = [html.Tbody(rows)]
    head = html.Thead([html.Tr([html.Th(col) for col in columns])])
    return html.Table([head] + rows, className="table table-hover table-bordered table-sm")

#Page Generator
def gen_page(run_id, gcvb_id):
    computation_dir="./results/{}".format(str(gcvb_id))
    run_id,gcvb_id=db.get_last_run()
    data = data_preparation(run_id)
    layout = dbc.Container(
        [
            dji.Import(src="/assets/sortable.js"),
            html.H1("Run"),
            Table(data, run_id, data.keys()),
        ]
    )
    return layout

layout = html.Div(id="run-content")
@app.callback(Output('run-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if not pathname:
        return 'Bonjour'
    page=pathname.split("/")
    run_id,gcvb_id=db.get_last_run() # Problem when multiple gcvb base exists. TODO
    if len(page)>2:
        run_id=int(page[2])
        #gcvb_id= ??? # TODO ! It is not correct
        return gen_page(run_id,gcvb_id)
    else:
        return gen_page(run_id,gcvb_id)

if __name__ == '__main__':
    app.run_server(debug=True)
