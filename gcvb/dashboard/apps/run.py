import dash
import dash_html_components as html
import dash_bootstrap_components as dbc
import gcvb.validation as val
import gcvb.db as db
import gcvb.yaml_input as yaml_input
import os

# Data
def data_preparation(report):
    res={"id" : [], "description" : [], "result" : []}
    for test_id,test in sorted(report.validation_base.items()):
        if test_id not in report.status:
            continue
        res["id"].append(test_id)
        res["description"].append(a["Tests"][test_id].get("description")) # to be changed
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

run_id,gcvb_id=db.get_last_run()
computation_dir="./results/{}".format(str(gcvb_id))
a=yaml_input.load_yaml(os.path.join(computation_dir,"tests.yaml"))
r=db.load_report(run_id)

report = val.Report(a,r)
data = data_preparation(report)

layout = dbc.Container([html.H1("Run"),Table(data,["id","description","result"])])

if __name__ == '__main__':
    app.run_server(debug=True)