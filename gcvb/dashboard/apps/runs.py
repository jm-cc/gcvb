import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

graph =  html.Div(dcc.Graph(figure={"data": [{"x": [1, 2, 3,5], "y": [1, 9, 9, 11]}]}),id="graph")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Markdown('''
# This is a sample page

This is *sparta*!!
                        '''),
                        dbc.Button("View details", color="secondary"),
                    ],
                ),
            ]),
        dbc.Row(        
                dbc.Col(
                    [
                        html.H1("Graph"),
                        graph,
                    ]
                ),
        ),
    ],
    className="mt-4",
)