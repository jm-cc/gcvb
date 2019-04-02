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


# Data
def data_preparation(report, ya):
    res={"id" : [], "description" : [], "result" : []}
    for test_id,test in sorted(report.validation_base.items()):
        if test_id not in report.status:
            continue
        res["id"].append(test_id)
        res["description"].append(ya["Tests"][test_id].get("description")) # to be changed
        res["result"].append(report.status[test_id])
    return res

# View
def Table(report, columns=None):
    rows = []
    if not columns:
        columns = report.keys()
    for i in range(len(report["id"])):
        row = []
        for col in columns:
            value = report[col][i]
            if col == 'id':
                cell = html.Td(html.A(href="/test/"+value, children=value))
            else:
                cell = html.Td(children=value)
            row.append(cell)
        rows.append(html.Tr(row))
    rows = [html.Tbody(rows)]
    return html.Table([html.Tr([html.Th(col) for col in columns])] + rows,
                      className="table table-hover table-bordered table-sm")

#Page Generator
def gen_page(run_id, gcvb_id):
    computation_dir="./results/{}".format(str(gcvb_id))
    a=yaml_input.load_yaml_from_run(run_id)
    r=db.load_report(run_id)
    report = val.Report(a,r)
    data = data_preparation(report, a)
    layout = dbc.Container([html.H1("Run"),Table(data,["id","description","result"])])
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