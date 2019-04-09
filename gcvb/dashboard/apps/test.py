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
def summary_panel(data):
    #Lines of the table
    description_line=html.Tr([html.Th("Description"),html.Td(data["description"])])
    result_line=html.Tr([html.Th("Result"),(html.Td(data["result"]))])
    time_line=html.Tr([html.Th("Elapsed time (s)"),(html.Td(data["time"]))])

    #Table
    table=html.Table(html.Tbody([description_line,result_line,time_line]), className="table table-sm")

    #Panel
    panel_header=html.Div(html.H3("Summary",className="panel-title"),className="panel panel-heading")
    panel=html.Div([panel_header,table],className="panel panel-default")


    return dbc.Container([panel])

#Page Generator
def gen_page(run_id, test_id):
    run_summary=db.retrieve_test(run_id,test_id)
    base=yaml_input.load_yaml_from_run(run_id)

    data={}
    data["description"]="Fake description"
    data["result"]="Success!"
    data["time"]="666"
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