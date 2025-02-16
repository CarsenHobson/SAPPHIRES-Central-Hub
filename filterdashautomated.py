import dash
from dash import dcc, html, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import sqlite3
import pandas as pd
import plotly.graph_objs as go
import datetime
import base64
import os
import logging

###################################################
# GLOBAL CONFIGURATION & CONSTANTS
###################################################

DB_PATH = '/home/mainhubs/SAPPHIRESautomated.db'  # Adjust if needed

EXTERNAL_STYLESHEETS = [
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
]

BACKGROUND_COLOR = "#f0f2f5"
PRIMARY_COLOR = "#FFFFCB"
SUCCESS_COLOR = "#28a745"
WARNING_COLOR = "#ffc107"
DANGER_COLOR = "#dc3545"

EMOJI_PATHS = {
    "good": "/home/mainhubs/good.png",
    "moderate": "/home/mainhubs/moderate.png",
    "unhealthy_sensitive": "/home/mainhubs/unhealthy_sensitive.png",
    "unhealthy": "/home/mainhubs/unhealthy.png",
    "very_unhealthy": "/home/mainhubs/very_unhealthy.png",
    "hazardous": "/home/mainhubs/hazardous.png"
}

# Enhanced Logging Config
logging.basicConfig(
    filename='enhanced_app.log',   # or another log file path
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logging.debug("Starting application with enhanced error handling.")


###################################################
# HELPER FUNCTIONS WITH ERROR HANDLING
###################################################

def get_db_connection():
    """Safely returns a connection to the SQLite DB or logs an error."""
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database at {DB_PATH}: {e}")
        return None


def encode_image(image_path):
    """
    Encode an image at a given path into base64 for embedding in the dashboard.
    Returns a placeholder if file not found or error occurs.
    """
    if not os.path.exists(image_path):
        logging.warning(f"File not found: {image_path}")
        return ""
    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception as e:
        logging.error(f"Error encoding image {image_path}: {e}")
        return ""

def get_aqi_emoji(aqi):
    """
    Return a corresponding emoji image based on AQI value.
    """
    try:
        if aqi <= 25:
            return encode_image(EMOJI_PATHS["good"])
        elif 26 <= aqi <= 50:
            return encode_image(EMOJI_PATHS["moderate"])
        elif 51 <= aqi <= 75:
            return encode_image(EMOJI_PATHS["unhealthy_sensitive"])
        elif 76 <= aqi <= 100:
            return encode_image(EMOJI_PATHS["unhealthy"])
        elif 101 <= aqi <= 125:
            return encode_image(EMOJI_PATHS["very_unhealthy"])
        else:
            return encode_image(EMOJI_PATHS["hazardous"])
    except Exception as e:
        logging.exception(f"Error selecting emoji for AQI {aqi}: {e}")
        return ""

def get_gauge_color(aqi):
    """
    Determine the gauge bar color based on AQI level.
    """
    if aqi <= 25:
        return "green"
    elif 26 <= aqi <= 50:
        return "yellow"
    elif 51 <= aqi <= 75:
        return "orange"
    elif 76 <= aqi <= 100:
        return "#ff6600"
    elif 101 <= aqi <= 125:
        return "red"
    else:
        return "#8b0000"

def get_last_fan_state():
    """
    Retrieve the last known fan state from the database: 'ON' or 'OFF'.
    Defaults to 'OFF' if no data or an error occurs.
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            logging.error("get_last_fan_state: No DB connection, returning 'OFF' as default.")
            return "OFF"
        cursor = conn.cursor()
        cursor.execute("SELECT user_input FROM user_control ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else "OFF"
    except Exception as e:
        logging.exception(f"Error fetching last fan state: {e}")
        return "OFF"
    finally:
        if conn:
            conn.close()

def update_fan_state(state):
    """
    Update the fan state in the user_control table with 'ON' or 'OFF'.
    """
    conn = None
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = get_db_connection()
        if not conn:
            logging.error(f"update_fan_state({state}): No DB connection, cannot update.")
            return
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO user_control (timestamp, user_input) VALUES (?, ?)',
            (timestamp, state)
        )
        conn.commit()
        logging.info(f"Fan state updated to {state}.")
    except Exception as e:
        logging.exception(f"Error updating fan state to {state}: {e}")
    finally:
        if conn:
            conn.close()

def get_spacing(aqi, delta):
    """
    Dynamically spaces the AQI & delta text and arrow.
    """
    aqi_digits = len(str(abs(aqi)))
    delta_digits = len(str(abs(int(delta))))

    if delta == 0:
        spacing_values = {
            (1, 1): {"aqi_x_coord": 0.45, "delta_x_coord": 0.73, "arrow_coord": 0.654, "aqi_font": 30, "delta_font": 20,"arrow_size": 30},
            (2, 1): {"aqi_x_coord": 0.45, "delta_x_coord": 0.76, "arrow_coord": 0.724, "aqi_font": 30, "delta_font": 20,"arrow_size": 30},
            (3, 1): {"aqi_x_coord": 0.445, "delta_x_coord": 0.78, "arrow_coord": 0.755, "aqi_font": 30, "delta_font": 20,"arrow_size": 30},
            (4, 1): {"aqi_x_coord": 0.445, "delta_x_coord": 0.81, "arrow_coord": 0.775, "aqi_font": 30,"delta_font": 20, "arrow_size": 30},
        }
    else:
        spacing_values = {
            (1, 1): {"aqi_x_coord": 0.43, "delta_x_coord": 0.73, "arrow_coord": 0.61, "aqi_font": 30, "delta_font": 20, "arrow_size": 30},
            (1, 2): {"aqi_x_coord": 0.42, "delta_x_coord": 0.74,"arrow_coord": 0.6, "aqi_font": 30, "delta_font": 20, "arrow_size": 30},
            (1, 3): {"aqi_x_coord": 0.4, "delta_x_coord": 0.775, "arrow_coord": 0.58, "aqi_font": 30, "delta_font": 20, "arrow_size": 30},
            (1, 4): {"aqi_x_coord": 0.375, "delta_x_coord": 0.79, "arrow_coord": 0.56, "aqi_font": 30, "delta_font": 20, "arrow_size": 30},
            (2, 1): {"aqi_x_coord": 0.43, "delta_x_coord": 0.76, "arrow_coord": 0.69, "aqi_font": 30, "delta_font": 20, "arrow_size": 30},
            (2, 2): {"aqi_x_coord": 0.415, "delta_x_coord": 0.775, "arrow_coord": 0.67, "aqi_font": 30, "delta_font": 20, "arrow_size": 30},
            (2, 3): {"aqi_x_coord": 0.4, "delta_x_coord": 0.8, "arrow_coord": 0.605, "aqi_font": 30, "delta_font": 20, "arrow_size": 30},
            (2, 4): {"aqi_x_coord": 0.38, "delta_x_coord": 0.81, "arrow_coord": 0.57, "aqi_font": 27, "delta_font": 20, "arrow_size": 29},
            (3, 1): {"aqi_x_coord": 0.42, "delta_x_coord": 0.78, "arrow_coord": 0.71, "aqi_font": 30, "delta_font": 20, "arrow_size": 30},
            (3, 2): {"aqi_x_coord": 0.41, "delta_x_coord": 0.81, "arrow_coord": 0.7, "aqi_font": 30, "delta_font": 20, "arrow_size": 30},
            (3, 3): {"aqi_x_coord": 0.395, "delta_x_coord": 0.802, "arrow_coord": 0.608, "aqi_font": 27, "delta_font": 20, "arrow_size": 29},
            (3, 4): {"aqi_x_coord": 0.37, "delta_x_coord": 0.82, "arrow_coord": 0.58, "aqi_font": 27, "delta_font": 20, "arrow_size": 29},
            (4, 1): {"aqi_x_coord": 0.415, "delta_x_coord": 0.81, "arrow_coord": 0.735, "aqi_font": 30, "delta_font": 20, "arrow_size": 30},
            (4, 2): {"aqi_x_coord": 0.4, "delta_x_coord": 0.83, "arrow_coord": 0.72, "aqi_font": 30, "delta_font": 20, "arrow_size": 30},
            (4, 3): {"aqi_x_coord": 0.38, "delta_x_coord": 0.83, "arrow_coord": 0.63, "aqi_font": 27, "delta_font": 20, "arrow_size": 29},
            (4, 4): {"aqi_x_coord": 0.37, "delta_x_coord": 0.84, "arrow_coord": 0.6, "aqi_font": 26, "delta_font": 20, "arrow_size": 28},
        }

    key = (aqi_digits, delta_digits)
    if key in spacing_values:
        v = spacing_values[key]
        return (
            v["aqi_x_coord"],
            v["delta_x_coord"],
            v["arrow_coord"],
            v["aqi_font"],
            v["delta_font"],
            v["arrow_size"]
        )
    else:
        raise ValueError(
            f"Invalid combination of aqi_length ({aqi_digits}) and delta_length ({delta_digits})."
        )

def get_fallback_gauge():
    """Return a minimal gauge figure if DB queries fail or data is missing."""
    fig = go.Figure()
    fig.add_annotation(text="Data Unavailable", x=0.5, y=0.5, showarrow=False, font=dict(size=16))
    fig.update_layout(height=300, margin=dict(t=0, b=50, l=50, r=50))
    return fig


###################################################
# PAGE LAYOUTS
###################################################

def dashboard_layout():
    """
    Constructs the main dashboard layout with all modals/buttons.
    """
    last_state = get_last_fan_state()
    button_text = "Enable Fan" if last_state == "OFF" else "Disable Fan"

    return dbc.Container([
        # Title row with embedded button
        dbc.Row([
            dbc.Col(
                html.Div(
                    [
                        # The title itself
                        html.H1(
                            "CURRENT CONDITIONS",
                            className="text-center mb-0",
                            style={
                                "font-family": "Roboto, sans-serif",
                                "font-weight": "700",
                                "color": "black",
                                "font-size": "2.5rem",
                                "margin": "0"
                            },
                        ),
                        # The smaller, grey button in the top-right corner
                        html.Div(
                            dcc.Link(
                                dbc.Button(
                                    "View Historical",
                                    size="sm",  # make it smaller
                                    style={
                                        "background-color": "#6e6e6d",
                                        "color": "white",
                                        "border": "#6e6e6d"
                                    },
                                ),
                                href="/historical",
                            ),
                            style={
                                "position": "absolute",
                                "top": "10px",
                                "right": "10px",
                            },
                        ),
                    ],
                    style={
                        "position": "relative",
                        "background-color": PRIMARY_COLOR,
                        "border": "2px solid black",
                        "border-radius": "10px 10px 0 0",
                    }
                ),
                width=12
            )
        ], className="g-0"),

        # Main content row with indoor and outdoor cards
        dbc.Row([
            # Indoor card
            dbc.Col(dbc.Card([
                dbc.CardHeader("INSIDE", className="text-center mb-0",
                               style={
                                   "font-size": "1.5rem",
                                   "font-weight": "700",
                                   "color": "black",
                                   "background": "white",
                                   "border-bottom": "2px solid black",
                                   "border-right": "2px solid black",
                                   "border-left": "2px solid black"
                               }),
                html.Div([
                    # AQI gauge
                    html.Div([
                        dcc.Graph(id="indoor-gauge", config={"displayModeBar": False})
                    ], style={
                        "padding": "0",
                        "border": "2px solid black",
                        "border-top": "none",
                        "border-bottom": "none",
                        "height": "115px"
                    }),
                    # Temperature box
                    html.Div([
                        html.Div([
                            html.Div(
                                "Temperature",
                                className="text-center",
                                style={
                                    "font-size": "1.25rem",
                                    "font-weight": "bold",
                                    "padding-top": "10px",
                                    "color": "black"
                                }
                            ),
                            html.Div(
                                id="indoor-temp-display",
                                className="d-flex justify-content-center align-items-center",
                                style={
                                    "font-size": "1.5rem",
                                    "color": "black",
                                    "text-align": "center",
                                    "margin-top": "2px"
                                }
                            )
                        ], style={
                            "width": "200px",
                            "height": "75px",
                            "border": "2px solid black",
                            "position": "absolute",
                            "bottom": "0",
                            "left": "0",
                            "background-color": "#D2B48C",
                            "border-radius": "5px 7px 5px 0",
                            "display": "flex",
                            "flex-direction": "column",
                            "justify-content": "center",
                            "align-items": "center"
                        })
                    ], style={
                        "padding": "30px",
                        "border-left": "2px solid black",
                        "border-right": "2px solid black",
                        "border-bottom": "2px solid black",
                        "height": "227px",
                        "background-color": "transparent"
                    })
                ])
            ]), width=6, className="p-0"),

            # Outdoor card
            dbc.Col(dbc.Card([
                dbc.CardHeader("OUTSIDE", className="text-center mb-0",
                               style={
                                   "font-size": "1.5rem",
                                   "font-weight": "700",
                                   "color": "black",
                                   "background": "white",
                                   "border-bottom": "2px solid black",
                                   "border-right": "2px solid black",
                                   "border-left": "2px solid black"
                               }),
                html.Div([
                    html.Div([
                        dcc.Graph(id="outdoor-gauge", config={"displayModeBar": False})
                    ], style={
                        "padding": "0",
                        "border": "2px solid black",
                        "border-top": "none",
                        "border-bottom": "none",
                        "height": "115px"
                    }),
                    html.Div([
                        html.Div([
                            html.Div(
                                "Temperature",
                                className="text-center",
                                style={
                                    "font-size": "1.25rem",
                                    "font-weight": "bold",
                                    "padding-top": "10px",
                                    "color": "black"
                                }
                            ),
                            html.Div(
                                id="outdoor-temp-display",
                                className="d-flex justify-content-center align-items-center",
                                style={
                                    "font-size": "1.5rem",
                                    "color": "black",
                                    "text-align": "center",
                                    "margin-top": "2px"
                                }
                            )
                        ], style={
                            "width": "200px",
                            "height": "75px",
                            "border": "2px solid black",
                            "position": "absolute",
                            "bottom": "0",
                            "right": "0",
                            "background-color": "#7BC8F6",
                            "border-radius": "7px 5px 5px 0",
                            "display": "flex",
                            "flex-direction": "column",
                            "justify-content": "center",
                            "align-items": "center"
                        })
                    ], style={
                        "padding": "30px",
                        "border-left": "2px solid black",
                        "border-right": "2px solid black",
                        "border-bottom": "2px solid black",
                        "height": "227px",
                        "background-color": "transparent"
                    })
                ])
            ]), width=6, className="p-0")
        ]),

        # Fan Control Button & modals
        dbc.Row([
            html.Div(
                html.Button(
                    button_text,
                    id="disable-fan",
                    className="btn btn-danger btn-lg",
                    style={
                        "width": "100px",
                        "height": "65px",
                        "border-radius": "100px",
                        "font-size": "1.2rem",
                        "color": "Yellow",
                        "backgroundColor": "green" if button_text == "Enable Fan" else "red",
                        "border": "2px solid green" if button_text == "Enable Fan" else "2px solid red"
                    }
                ),
                style={
                    "border": "2px solid black",
                    "padding": "5px",
                    "width": "150px",
                    "height": "100px",
                    "position": "absolute",
                    "left": "50%",
                    "transform": "translateX(-50%)",
                    "bottom": "683px",
                    "display": "flex",
                    "align-items": "center",
                    "justify-content": "center",
                    "text-align": "center",
                    "box-sizing": "border-box",
                    "background-color": "black",
                    "border-radius": "3.5px"
                }
            )
        ], style={"position": "relative", "height": "682px"}, className="g-0"),

        dcc.Store(id='modal-state-store',
                  data={'modal_confirm': False, 'modal_warning': False, 'modal_notification': False}),

        # Confirmation Modal
        dbc.Modal([
            dbc.ModalHeader("Confirm Action", close_button=False),
            dbc.ModalBody("Are you sure you want to disable the fan?"),
            dbc.ModalFooter([
                dbc.Button("Yes", id="confirm-yes", className="btn btn-primary"),
                dbc.Button("No", id="confirm-no", className="btn btn-secondary")
            ])
        ], id="modal-confirm", is_open=False, backdrop="static", centered=True),

        # Warning Modal
        dbc.Modal([
            dbc.ModalHeader("Warning", style={'color': 'red'}, close_button=False),
            dbc.ModalBody("Disabling the fan may affect air quality. Do you want to proceed?"),
            dbc.ModalFooter([
                dbc.Button("Proceed", id="warning-yes", className="btn btn-danger"),
                dbc.Button("Cancel", id="warning-no", className="btn btn-secondary")
            ])
        ], id="modal-warning", is_open=False, backdrop="static", centered=True),

        # Notification Modal (Fan Enabled)
        dbc.Modal([
            dbc.ModalHeader("Fan Enabled", close_button=False),
            dbc.ModalBody(
                "You have enabled the fan. The fan will start filtering the air and improving air quality. "
                "You may now close this window."
            ),
            dbc.ModalFooter(dbc.Button("Close", id="close-notification", className="btn btn-secondary"))
        ], id="modal-notification", is_open=False, backdrop="static", centered=True),

        dcc.Interval(id='interval-component', interval=10 * 1000, n_intervals=0),
        dcc.Store(id='workflow-state', data={'stage': 'initial'})
    ], fluid=True, className="p-4")


def historical_conditions_layout():
    """
    Constructs the historical conditions layout.
    """
    conn = None
    try:
        conn = get_db_connection()
        indoor_data = pd.read_sql("SELECT timestamp, pm25 FROM Indoor ORDER BY timestamp DESC LIMIT 100;", conn)
        outdoor_data = pd.read_sql("SELECT timestamp, pm25 FROM Outdoor ORDER BY timestamp DESC LIMIT 100;", conn)
    except Exception as e:
        logging.exception(f"Error retrieving historical data: {e}")
        indoor_data = pd.DataFrame(columns=["timestamp", "pm25"])
        outdoor_data = pd.DataFrame(columns=["timestamp", "pm25"])
    finally:
        if conn:
            conn.close()

    if not indoor_data.empty:
        indoor_data['timestamp'] = pd.to_datetime(indoor_data['timestamp'])
    else:
        logging.warning("No indoor data found for historical layout.")

    if not outdoor_data.empty:
        outdoor_data['timestamp'] = pd.to_datetime(outdoor_data['timestamp'])
    else:
        logging.warning("No outdoor data found for historical layout.")

    fig = go.Figure()
    if not indoor_data.empty:
        fig.add_trace(go.Scatter(
            x=indoor_data['timestamp'],
            y=indoor_data['pm25'],
            mode='lines',
            name='Indoor PM',
            line=dict(color='red', width=2, shape='spline'),
            hoverinfo='x+y',
        ))
    if not outdoor_data.empty:
        fig.add_trace(go.Scatter(
            x=outdoor_data['timestamp'],
            y=outdoor_data['pm25'],
            mode='lines',
            name='Outdoor PM',
            line=dict(color='blue', width=2, shape='spline'),
            hoverinfo='x+y',
        ))

    fig.update_layout(
        xaxis=dict(
            title="Time",
            showgrid=True,
            gridcolor='lightgrey',
            titlefont=dict(size=14, family="Roboto, sans-serif"),
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            title="AQI",
            showgrid=True,
            gridcolor='lightgrey',
            titlefont=dict(size=14, family="Roboto, sans-serif"),
            tickfont=dict(size=12)
        ),
        template="plotly_white",
        legend=dict(
            orientation="h",
            x=0.5,
            y=-.05,
            xanchor="center",
            font=dict(size=12, family="Roboto, sans-serif")
        ),
        height=300,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    return dbc.Container([
        dbc.Row([
            dbc.Col(
                dcc.Link(
                    dbc.Button("View Current Conditions", size="sm",
                               style={"color": "white", "background-color": "#6e6e6d", "border": "#6e6e6d"}),
                    href="/"
                ),
                width="auto"
            )
        ], style={"margin-top": "10px"}),

        dbc.Row(dbc.Col(html.H1("Historical Conditions", className="text-center mb-4"))),
        dbc.Row(dbc.Col(dcc.Graph(figure=fig, config={"displayModeBar": False}))),
    ], fluid=True, className="p-4")

###################################################
# APP INITIALIZATION
###################################################

app = dash.Dash(
    __name__,
    external_stylesheets=EXTERNAL_STYLESHEETS,
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

app.layout = html.Div(
    style={"overflow": "hidden", "height": "100vh"},
    children=[
        dcc.Location(id='url', refresh=False),
        dcc.Store(id="page-store", data="dashboard"),
        html.Div(id='page-content', style={"outline": "none"})
    ]
)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                margin: 0;
                overflow: hidden;
                font-family: "Roboto", sans-serif;
            }
        </style>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    </head>
    <body>
        {%app_entry%}
        <script>
            let startX = 0, endX = 0;
            document.addEventListener('touchstart', function(e) {
                startX = e.changedTouches[0].screenX;
            }, false);
            document.addEventListener('touchend', function(e) {
                endX = e.changedTouches[0].screenX;
                handleSwipe();
            }, false);
            function handleSwipe() {
                const deltaX = endX - startX;
                if (deltaX > 50) {
                    // Swipe Right
                    window.history.pushState({}, '', '/');
                    window.dispatchEvent(new PopStateEvent('popstate'));
                } else if (deltaX < -50) {
                    // Swipe Left
                    window.history.pushState({}, '', '/historical');
                    window.dispatchEvent(new PopStateEvent('popstate'));
                }
            }
        </script>
        {%config%}
        {%scripts%}
        {%renderer%}
    </body>
</html>
'''

###################################################
# CALLBACKS
###################################################

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
)
def display_page(pathname):
    """Switches between dashboard and historical layout."""
    if pathname == '/':
        return dashboard_layout()
    elif pathname == '/historical':
        return historical_conditions_layout()
    else:
        return html.Div("Page not found", className="text-center")


@app.callback(
    [
        Output('indoor-gauge', 'figure'),
        Output('outdoor-gauge', 'figure'),
        Output('indoor-temp-display', 'children'),
        Output('outdoor-temp-display', 'children')
    ],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """
    Periodically fetches the latest indoor/outdoor data from the database,
    updates the gauge figures and temp displays.
    """
    try:
        conn = get_db_connection()
    except Exception as e:
        logging.exception(f"update_dashboard: DB connection failed: {e}")
        return get_fallback_gauge(), get_fallback_gauge(), "N/A", "N/A"

    if conn is None:
        logging.error("update_dashboard: Could not get DB connection (conn is None).")
        return get_fallback_gauge(), get_fallback_gauge(), "N/A", "N/A"

    try:
        # Initialize output variables with default values
        indoor_temp_df = None
        indoor_pm = None
        outdoor_pm = 0  # Ensure it's always initialized
        outdoor_temp_df = 0  # Ensure it's always initialized
        indoor_temp_df = pd.read_sql("SELECT temperature FROM Indoor ORDER BY timestamp DESC LIMIT 60;", conn)
        indoor_pm = pd.read_sql("SELECT pm25 FROM Indoor ORDER BY timestamp DESC LIMIT 60;", conn)
        # Query Outdoor PM data
        outdoor_pm_values = []
        for i in ["One", "Two", "Three", "Four"]:
            outdoor_pm_df = pd.read_sql(f"SELECT pm25 FROM Outdoor_{i} ORDER BY timestamp DESC LIMIT 60;", conn)
            if not outdoor_pm_df.empty:
                outdoor_pm_values.append(outdoor_pm_df['pm25'].mean())

        if outdoor_pm_values:
            outdoor_pm = sum(outdoor_pm_values) / len(outdoor_pm_values)
        else:
            outdoor_pm = 0  # Default value if no PM data is available

        # Query Outdoor Temperature data
        outdoor_temp_values = []
        for i in ["One", "Two", "Three", "Four"]:
            outdoor_temp_df = pd.read_sql(f"SELECT temperature FROM Outdoor_{i} ORDER BY timestamp DESC LIMIT 1;", conn)
            if not outdoor_temp_df.empty:
                outdoor_temp_values.append(outdoor_temp_df['temperature'].iloc[0])

        if outdoor_temp_values:
            outdoor_temp_df = sum(outdoor_temp_values) / len(outdoor_temp_values)
        else:
            outdoor_temp_df = 0  # Default value if no temperature data is available

        conn.close()

        # Display results
        #print(f"Outdoor PM2.5 Average: {outdoor_pm}")
        #print(f"Outdoor Temperature Average: {outdoor_temp_df}")

        # Defaults
        indoor_aqi = 0
        outdoor_aqi = 0
        indoor_temp_text = "N/A"
        outdoor_temp_text = "N/A"
        indoor_delta = 0
        outdoor_delta = 0
        indoor_arrow = "--"
        outdoor_arrow = "--"
        indoor_arrow_color = "grey"
        outdoor_arrow_color = "grey"
        indoor_delta_text = "0"
        outdoor_delta_text = "0"

        # Indoor
        if not indoor_pm is None:
            indoor_aqi = round(indoor_pm['pm25'].iloc[0])
            if len(indoor_pm) > 30:
                indoor_delta = indoor_aqi - round(indoor_pm['pm25'].iloc[30:].mean())
            indoor_delta_text = f"+{indoor_delta}" if indoor_delta > 0 else str(indoor_delta)
            if indoor_delta > 0:
                indoor_arrow = "⬆️"
                indoor_arrow_color = "red"
            elif indoor_delta < 0:
                indoor_arrow = "⬇️"
                indoor_arrow_color = "green"
            else:
                indoor_arrow = "--"
                indoor_arrow_color = "grey"

        if not indoor_temp_df.empty:
            indoor_temp_value = round(indoor_temp_df['temperature'].iloc[0], 1)
            indoor_temp_text = f"{indoor_temp_value} °F"

        # Outdoor
        if not outdoor_pm is None :
            outdoor_aqi = round(outdoor_pm)
            if len(str(outdoor_pm)) > 30:
                outdoor_delta = outdoor_aqi - round(outdoor_pm)
            outdoor_delta_text = f"+{outdoor_delta}" if outdoor_delta > 0 else str(outdoor_delta)
            if outdoor_delta > 0:
                outdoor_arrow = "⬆️"
                outdoor_arrow_color = "red"
            elif outdoor_delta < 0:
                outdoor_arrow = "⬇️"
                outdoor_arrow_color = "green"
            else:
                outdoor_arrow = "--"
                outdoor_arrow_color = "grey"

        if not outdoor_temp_df is None:
            outdoor_temp_value = round(outdoor_temp_df, 1)
            outdoor_temp_text = f"{outdoor_temp_value} °F"

        max_aqi = max(indoor_aqi, outdoor_aqi, 100)
        indoor_emoji = get_aqi_emoji(indoor_aqi)
        outdoor_emoji = get_aqi_emoji(outdoor_aqi)
        # Build Indoor gauge
        indoor_x, indoor_dx, indoor_ax, indoor_aqi_font, indoor_delta_font, indoor_arrow_size = get_spacing(indoor_aqi, indoor_delta)
        indoor_fig = go.Figure(go.Indicator(
            mode="gauge",
            value=indoor_aqi,
            gauge={
                'axis': {'range': [0, max_aqi]},
                'bar': {'color': get_gauge_color(indoor_aqi)},
                'bgcolor': "lightgray",
                'bordercolor': "black",
            },
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
        indoor_fig.update_layout(height=300, margin=dict(t=0, b=50, l=50, r=50))
        indoor_fig.add_annotation(
            x=indoor_x, y=0.25,
            text=f"<b>AQI:{indoor_aqi}</b>",
            showarrow=False,
            font=dict(size=indoor_aqi_font, color="black"),
            xanchor="center", yanchor="bottom"
        )
        indoor_fig.add_annotation(
            x=indoor_ax, y=0.24 if indoor_delta != 0 else 0.26,
            text=indoor_arrow,
            font=dict(size=indoor_arrow_size, color=indoor_arrow_color),
            showarrow=False
        )
        indoor_fig.add_layout_image(
            dict(
                source=indoor_emoji,
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                sizex=0.2, sizey=0.2,
                xanchor="center", yanchor="middle"
            )
        )
        if indoor_delta != 0:
            indoor_fig.add_annotation(
                x=indoor_dx, y=0.28,
                text=indoor_delta_text,
                font=dict(size=indoor_delta_font, color=indoor_arrow_color),
                showarrow=False
            )

        # Build Outdoor gauge
        outdoor_x, outdoor_dx, outdoor_ax, outdoor_aqi_font, outdoor_delta_font, outdoor_arrow_size = get_spacing(outdoor_aqi, outdoor_delta)
        outdoor_fig = go.Figure(go.Indicator(
            mode="gauge",
            value=outdoor_aqi,
            gauge={
                'axis': {'range': [0, max_aqi]},
                'bar': {'color': get_gauge_color(outdoor_aqi)},
                'bgcolor': "lightgray",
                'bordercolor': "black",
            },
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
        outdoor_fig.update_layout(height=300, margin=dict(t=0, b=50, l=50, r=50))
        outdoor_fig.add_annotation(
            x=outdoor_x, y=0.25,
            text=f"<b>AQI:{outdoor_aqi}</b>",
            showarrow=False,
            font=dict(size=outdoor_aqi_font, color="black"),
            xanchor="center", yanchor="bottom"
        )
        outdoor_fig.add_annotation(
            x=outdoor_ax, y=0.24 if outdoor_delta != 0 else 0.26,
            text=outdoor_arrow,
            font=dict(size=outdoor_arrow_size, color=outdoor_arrow_color),
            showarrow=False
        )
        outdoor_fig.add_layout_image(
            dict(
                source=outdoor_emoji,
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                sizex=0.2, sizey=0.2,
                xanchor="center", yanchor="middle"
            )
        )
        if outdoor_delta != 0:
            outdoor_fig.add_annotation(
                x=outdoor_dx, y=0.28,
                text=outdoor_delta_text,
                font=dict(size=outdoor_delta_font, color=outdoor_arrow_color),
                showarrow=False
            )


        return indoor_fig, outdoor_fig, indoor_temp_text, outdoor_temp_text

    except Exception as ex:
        logging.exception(f"Error in update_dashboard callback: {ex}")
        return get_fallback_gauge(), get_fallback_gauge(), "N/A", "N/A"


@app.callback(
    [
        Output('disable-fan', 'children'),
        Output('disable-fan', 'style'),
        Output('modal-confirm', 'is_open'),
        Output('modal-warning', 'is_open'),
        Output('modal-notification', 'is_open'),
        Output('modal-state-store', 'data')
    ],
    [
        Input('disable-fan', 'n_clicks'),
        Input('confirm-yes', 'n_clicks'),
        Input('confirm-no', 'n_clicks'),
        Input('warning-yes', 'n_clicks'),
        Input('warning-no', 'n_clicks'),
        Input('close-notification', 'n_clicks')
    ],
    [
        State('disable-fan', 'children'),
        State('modal-state-store', 'data')
    ],
    prevent_initial_call=True
)
def manage_fan_workflow(disable_fan_clicks, confirm_yes_clicks, confirm_no_clicks,
                        warning_yes_clicks, warning_no_clicks, close_notification_clicks,
                        button_text, modal_state):
    """
    Manages the fan enabling/disabling workflow and modal states.
    """
    try:
        triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0] if callback_context.triggered else None

        modal_confirm = modal_state.get('modal_confirm', False)
        modal_warning = modal_state.get('modal_warning', False)
        modal_notification = modal_state.get('modal_notification', False)

        is_fan_on = (button_text == "Disable Fan")

        # Default button style
        button_style = {
            "width": "100px",
            "height": "65px",
            "border-radius": "100px",
            "font-size": "1.2rem",
            "color": "Yellow",
            "backgroundColor": "red" if is_fan_on else "green",
            "border": "2px solid red" if is_fan_on else "2px solid green"
        }

        if triggered_id == 'disable-fan' and is_fan_on:
            # Fan is ON, user wants to disable -> confirm
            modal_confirm = True

        elif triggered_id == 'confirm-yes':
            # Show warning
            modal_confirm = False
            modal_warning = True

        elif triggered_id == 'confirm-no':
            # Cancel confirm
            modal_confirm = False

        elif triggered_id == 'warning-yes':
            # User proceeds with disabling -> disable fan
            modal_warning = False
            update_fan_state("OFF")
            button_text = "Enable Fan"
            button_style["backgroundColor"] = "green"
            button_style["border"] = "2px solid green"

        elif triggered_id == 'warning-no':
            modal_warning = False

        elif triggered_id == 'disable-fan' and not is_fan_on:
            # User clicks Enable Fan -> turn fan ON
            update_fan_state("ON")
            modal_notification = True
            button_text = "Disable Fan"
            button_style["backgroundColor"] = "red"
            button_style["border"] = "2px solid red"

        elif triggered_id == 'close-notification':
            modal_notification = False

        updated_state = {
            'modal_confirm': modal_confirm,
            'modal_warning': modal_warning,
            'modal_notification': modal_notification
        }

        return button_text, button_style, modal_confirm, modal_warning, modal_notification, updated_state

    except Exception as ex:
        logging.exception(f"Error in manage_fan_workflow callback: {ex}")
        # On error, revert to current states so we don't break UI
        return (
            button_text,
            {
                "width": "100px",
                "height": "65px",
                "border-radius": "100px",
                "font-size": "1.2rem",
                "color": "Yellow",
                "backgroundColor": "red" if (button_text == "Disable Fan") else "green",
                "border": "2px solid red" if (button_text == "Disable Fan") else "2px solid green"
            },
            modal_state.get('modal_confirm', False),
            modal_state.get('modal_warning', False),
            modal_state.get('modal_notification', False),
            modal_state
        )

###################################################
# MAIN
###################################################

if __name__ == '__main__':
    app.run_server(debug=False)
