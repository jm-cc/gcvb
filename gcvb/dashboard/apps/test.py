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
    tmp=db.retrieve_test(run,test_id)
    return str(tmp)

#Page
layout = html.Div(id="test-content")

@app.callback(Output('test-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    page=pathname.split("/")
    if len(page)<4:
        return '404'
    run,test_id=page[2],page[3]
    return data_preparation(run,test_id)
