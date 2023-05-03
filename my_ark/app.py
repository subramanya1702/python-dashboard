import datetime
import os

import pandas as pd
from dash import Dash, Input, Output, dcc, html
from dash.exceptions import PreventUpdate
from flask import Flask, send_file

import pg_connect

# Constants
factors = ["Temperature", "pH", "Distilled Oxygen", "Pressure"]
factor_unit_map = {
    "Temperature": "℃",
    "pH": "",
    "Distilled Oxygen": "％",
    "Pressure": "psi"
}
external_stylesheets = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?"
            "family=Lato:wght@400;700&display=swap"
        ),
        "rel": "stylesheet",
    },
]

# Global variables
global_factor = "Temperature"
global_start_date = datetime.datetime.now()
global_end_date = datetime.datetime.now()


# Data loader class
# Connects to the postgresDB and loads all the data from tables
class DataLoader:
    __cursor = None

    def __init__(self):
        pg_obj = pg_connect.PostgresDB()
        self.__cursor = pg_obj.get_connection_object().cursor()

    def load_data(self):
        # Temperature
        self.__cursor.execute("select * from public.\"CM_HAM_DO_AI1/Temp_value\";")
        result = self.__cursor.fetchall()
        print("Number of temperature records: " + str(len(result)))

        with open("common.csv", mode="w", encoding="utf8") as temp_csv:
            temp_csv.write("Factor,Value,Time\n")

            for record in result:
                temp_csv.write("Temperature,{0},{1}\n".format(record[1], record[0]))

        # pH
        self.__cursor.execute("select * from public.\"CM_HAM_PH_AI1/pH_value\";")
        result = self.__cursor.fetchall()
        print("Number of pH records: " + str(len(result)))

        with open("common.csv", mode="a", encoding="utf8") as ph_csv:
            for record in result:
                ph_csv.write("pH, {0},{1}\n".format(record[1], record[0]))

        # DO
        self.__cursor.execute("select * from public.\"CM_PID_DO/Process_DO\";")
        result = self.__cursor.fetchall()
        print("Number of DO records: " + str(len(result)))

        with open("common.csv", mode="a", encoding="utf8") as do_csv:
            for record in result:
                do_csv.write("Distilled Oxygen,{0},{1}\n".format(record[1], record[0]))

        # Pressure
        self.__cursor.execute("select * from public.\"CM_PRESSURE/Output\";")
        result = self.__cursor.fetchall()
        print("Number of Pressure records: " + str(len(result)))

        with open("common.csv", mode="a", encoding="utf8") as pressure_csv:
            for record in result:
                pressure_csv.write("Pressure,{0},{1}\n".format(record[1], record[0]))


# Dashboard class
# Responsible for creating the interactive dashboard
class Dashboard:
    def __init__(self):
        # Creates a pandas DataFrame object by reading the common csv file
        self.data = (
            pd.read_csv("common.csv")
            .assign(Time=lambda data: pd.to_datetime(data["Time"], format="%Y-%m-%d %H:%M:%S.%f"))
            .sort_values(by="Time")
        )

        # Initialize flask and dash apps
        # Have flask run as the server for dash
        self.flask_app = Flask(__name__)
        self.app = Dash(__name__,
                        external_stylesheets=external_stylesheets,
                        server=self.flask_app,
                        url_base_pathname="/")

        # Register callback for dash
        self.app.callback(
            Output("factor-graph", "figure"),
            Input("factor-filter", "value"),
            Input("time-filter", "value"),
            Input("date-range", "start_date"),
            Input("date-range", "end_date"),
            Input("refresh-button", "n_clicks")
        )(self.update_charts)
        self.app.title = "Ark Biotech Take Home Project!"

        # Initialize dashboard layout
        self.app.layout = html.Div(
            children=[
                html.Div(
                    children=[
                        html.P(children="☣️", className="header-emoji"),
                        html.H1(
                            children="Ark Biotech", className="header-title"
                        ),
                        html.P(
                            children=(
                                "Analyze the behavior of bioreactor temperature, pH, distilled oxygen and pressure"
                            ),
                            className="header-description",
                        ),
                    ],
                    className="header",
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.Div(children="Type", className="menu-title"),
                                dcc.Dropdown(
                                    id="factor-filter",
                                    options=[
                                        {
                                            "label": factor,
                                            "value": factor,
                                        }
                                        for factor in factors
                                    ],
                                    value="Temperature",
                                    clearable=False,
                                    searchable=False,
                                    className="dropdown",
                                ),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Div(children="Time Filter", className="menu-title"),
                                dcc.Dropdown(
                                    id="time-filter",
                                    options=[
                                        {'label': '1 hour', 'value': '1H'},
                                        {'label': '3 hours', 'value': '3H'},
                                        {'label': '6 hours', 'value': '6H'},
                                        {'label': '12 hours', 'value': '12H'},
                                        {'label': '1 day', 'value': '1D'},
                                        {'label': '3 days', 'value': '3D'},
                                        {'label': '7 days', 'value': '7D'},
                                        {'label': 'Custom Range', 'value': 'Custom'}
                                    ],
                                    value='1D'
                                )
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Div(
                                    children="Custom Date Range", className="menu-title"
                                ),
                                dcc.DatePickerRange(
                                    id="date-range",
                                    min_date_allowed=datetime.datetime.now() - datetime.timedelta(days=90),
                                    max_date_allowed=datetime.datetime.now()
                                    # start_date=datetime.datetime.now() - datetime.timedelta(days=7),
                                    # end_date=datetime.datetime.now()
                                ),
                            ]
                        )
                    ],
                    className="menu",
                ),
                html.Div([
                    html.Button("Refresh Data", id="refresh-button", n_clicks=0),
                    html.A(html.Button("Download Data", id="download-button"), href="/download")
                ]),
                html.Div(
                    children=[
                        html.Div(
                            children=dcc.Graph(
                                id="factor-graph",
                                config={"displayModeBar": False},
                            ),
                            className="card",
                        )
                    ],
                    className="wrapper",
                )
            ]
        )

    # Callback function
    # Uses the user's inputs to reload the data
    def update_charts(self, factor, time, start_date, end_date, n_clicks):
        global global_factor
        global global_start_date
        global global_end_date

        if time == "Custom" or time is None or time == "":
            if start_date is None or end_date is None:
                raise PreventUpdate
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            print(start_date)
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            print(end_date)
            end_date = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 000000)
        else:
            end_date = datetime.datetime.now()
            if time[1] == "H":
                start_date = end_date - datetime.timedelta(hours=int(time[0]))
            else:
                start_date = end_date - datetime.timedelta(days=int(time[0]))

        filtered_data = self.data.query(
            "Factor == @factor"
            " and Time >= @start_date and Time <= @end_date"
        )

        global_factor = factor
        global_start_date = start_date
        global_end_date = end_date

        factor_graph = {
            "data": [
                {
                    "x": filtered_data["Time"],
                    "y": filtered_data["Value"],
                    "type": "lines",
                    "hovertemplate": "$%{y:.2f}<extra></extra>",
                },
            ],
            "layout": {
                "title": {
                    "text": "{0} Changes".format(factor),
                    "x": 0.05,
                    "xanchor": "left",
                },
                "xaxis": {"fixedrange": True},
                "yaxis": {"tickprefix": "{0} ".format(factor_unit_map[factor]), "fixedrange": True},
                "colorway": ["#17B897"],
            },
        }

        return factor_graph

    # Function to add flask routes
    def add_endpoint(self, endpoint=None, end_point_name=None, handler=None, methods=None):
        self.flask_app.add_url_rule(endpoint, end_point_name, handler, methods=methods)

    # Function to download the data as a csv file
    def download(self):
        print("Downloading...")

        csv_path = os.getcwd() + "/csv_data.csv"
        filtered_data = self.data.query(
            "Factor == @global_factor"
            " and Time >= @global_start_date and Time <= @global_end_date"
        )
        filtered_data.to_csv(csv_path)
        if not os.path.isfile(csv_path):
            print("File not found. Unable to download")

        return send_file(csv_path, as_attachment=True, download_name="csv_data")

    # Run dash app
    def run_server(self):
        self.app.run(debug=True, host="0.0.0.0", port=8888)


# Entrypoint
def main():
    data_loader = DataLoader()
    data_loader.load_data()

    dashboard = Dashboard()
    dashboard.add_endpoint("/download", "download", dashboard.download, methods=['GET'])
    dashboard.run_server()
