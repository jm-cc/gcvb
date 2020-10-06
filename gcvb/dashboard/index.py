import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import os
import io
import gcvb.db as db

import gcvb.loader as loader
if __name__ == '__main__':
    from app import app
    from apps import runs, run, test, history
else:
    from .app import app
    from .apps import runs, run, test, history
import flask

cwd = os.getcwd()

url =  dcc.Location(id='url', refresh=False)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Runs", href="/runs")),
        dbc.NavItem(dbc.NavLink("Last run", href="/run")),
        dbc.NavItem(dbc.NavLink("Data", href="/data")),

    ],
    brand="gcvb-dashboard",
    brand_href="",
    sticky="top",
)

content = html.Div(id="page-content")

app.layout=html.Div([url, navbar, content])


def _get_mimetype(base, test, filename):
    base = int(base)
    if base not in loader.loader.allowed_files:
        flask.abort(404)
    if test not in loader.loader.allowed_files[base]:
        flask.abort(404)
    if filename not in loader.loader.allowed_files[base][test]:
        flask.abort(404)
    return loader.loader.allowed_files[base][test][filename].get(
        "mimetype", "text/plain"
    )


@app.server.route("/files/<base>/<test>/<file>")
def serve_from_results(base, test, file):
    return flask.send_file(
        f"{cwd}/results/{base}/{test}/{file}", mimetype=_get_mimetype(base, test, file)
    )


@app.server.route("/dbfiles/<base>/<test>/<filename>")
def serve_from_db(base, test, filename):
    return flask.send_file(
        io.BytesIO(db.retrieve_file(int(base), test, filename)),
        mimetype=_get_mimetype(base, test, filename)
    )

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if not pathname:
        return 'Bonjour'
    page=pathname.split("/")
    if page[1] == 'runs':
        return runs.layout
    if page[1] == 'run':
        return run.layout
    if page[1] == 'test':
        return test.layout
    if page[1] == 'history':
        return history.layout
    else:
        return 'Bonjour'

def run_server(debug=False):
    app.run_server(debug=debug)

if __name__ == '__main__':
    app.run_server(debug=True)