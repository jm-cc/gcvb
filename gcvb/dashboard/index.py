import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

if __name__ == '__main__':
    from app import app
    from apps import runs
else:
    from .app import app
    from .apps import runs

url =  dcc.Location(id='url', refresh=False)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Runs", href="runs")),
        dbc.NavItem(dbc.NavLink("Data", href="data")),

    ],
    brand="gcvb-dashboard",
    brand_href="",
    sticky="top",
)

content = html.Div(id="page-content")

app.layout=html.Div([url, navbar, content])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])

def display_page(pathname):
    if pathname == '/runs':
         return runs.layout
    else:
        return 'Bonjour'

def run_server():
    app.run_server()

if __name__ == '__main__':
    app.run_server(debug=True)