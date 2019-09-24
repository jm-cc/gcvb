import dash
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
if __name__ == '__main__':
    from app import app
else:
    from ..app import app
from dash.dependencies import Input, Output
import gcvb.db as db

def gen_page(test_id, metric_id):
    #Data
    res=db.retrieve_history(test_id,metric_id)
    x=[a["run"] for a in res]
    y=[a["value"] for a in res]
    graph = dcc.Graph(figure={"data" : [{"x" : x, "y" : y}] })

    #Style
    title=html.H1("History for {} ({})".format(metric_id,test_id))

    return dbc.Container([title,graph])

#Page
layout = html.Div(id="history-content")

@app.callback(Output('history-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    page=pathname.split("/")
    if len(page)<4:
        return '404'
    test_id,metric_id=page[2],page[3]
    return gen_page(test_id,metric_id)
