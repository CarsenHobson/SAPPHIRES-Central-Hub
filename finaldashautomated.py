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

###################################################
# GLOBAL CONFIGURATION & CONSTANTS
###################################################

# Path to the SQLite database. Ensure this path is correct.
DB_PATH = '/home/mainhubs/SAPPHIRES.db'

# External Stylesheets (Bootstrap & Fonts)
EXTERNAL_STYLESHEETS = [
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
]

# Color constants for branding and styling
BACKGROUND_COLOR = "#f0f2f5"
PRIMARY_COLOR = "#FFFFCB"
SUCCESS_COLOR = "#28a745"
WARNING_COLOR = "#ffc107"
DANGER_COLOR = "#dc3545"

# Image paths for AQI emojis
EMOJI_PATHS = {
    "good": "/home/mainhubs/good.png",
    "moderate": "/home/mainhubs/moderate.png",
    "unhealthy_sensitive": "/home/mainhubs/unhealthy_sensitive.png",
    "unhealthy": "/home/mainhubs/unhealthy.png",
    "very_unhealthy": "/home/mainhubs/very_unhealthy.png",
    "hazardous": "/home/mainhubs/hazardous.png"
}


###################################################
# HELPER FUNCTIONS
###################################################

def create_tables():
    """
    Create the necessary tables if they do not exist.
    Ensures the environment is ready for data storage.
    """
    create_tables_script = """
    CREATE TABLE IF NOT EXISTS Indoor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        pm25 REAL,
        temperature REAL,
        humidity REAL
    );

    CREATE TABLE IF NOT EXISTS baseline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        baseline_value REAL
    );

    CREATE TABLE IF NOT EXISTS user_control (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        user_input TEXT
    );

    CREATE TABLE IF NOT EXISTS filter_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        filter_state TEXT
    );

    CREATE TABLE IF NOT EXISTS Outdoor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        pm25_value REAL,
        temperature REAL,
        humidity REAL,
        wifi_strength REAL
    );
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.executescript(create_tables_script)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating tables: {e}")


def encode_image(image_path):
    """
    Encode an image at a given path into base64 for embedding in the dashboard.

    Parameters:
        image_path (str): The full path to the image file.

    Returns:
        str: Base64 encoded image string, or a placeholder if file not found.
    """
    if not os.path.exists(image_path):
        # If the file does not exist, return a blank image or handle gracefully
        print(f"File not found: {image_path}")
        return ""

    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return ""


def get_aqi_emoji(aqi):
    """
    Return a corresponding emoji image based on AQI value.

    Parameters:
        aqi (int): AQI value.

    Returns:
        str: base64-encoded image string for the corresponding emoji.
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
        print(f"Error selecting emoji for AQI {aqi}: {e}")
        return ""


def get_gauge_color(aqi):
    """
    Determine the gauge bar color based on AQI level.

    Parameters:
        aqi (int): Current AQI value.

    Returns:
        str: Hex or color name string.
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
    Retrieve the last known fan state from the database.

    Returns:
        str: "ON" or "OFF" (defaults to "OFF" if no data found).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_input FROM user_control ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "OFF"
    except Exception as e:
        print(f"Error fetching last fan state: {e}")
        return "OFF"


def update_fan_state(state):
    """
    Update the fan state in the user_control table.

    Parameters:
        state (str): "ON" or "OFF"
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_control (timestamp, user_input) VALUES (?, ?)', (timestamp, state))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating fan state to {state}: {e}")


###################################################
# LAYOUT COMPONENTS
###################################################

def dashboard_layout():
    """
    Constructs the main dashboard layout including:
    - Current conditions header
    - Indoor and outdoor gauge cards
    - Fan control button and modals
    """
    last_state = get_last_fan_state()
    button_text = "Enable Fan" if last_state == "OFF" else "Disable Fan"

    return dbc.Container([
        # Title Row
        dbc.Row([
            dbc.Col(
                html.H1(
                    "CURRENT CONDITIONS",
                    className="text-center mb-0",
                    style={
                        "font-family": "Roboto, sans-serif",
                        "font-weight": "700",
                        "color": "black",
                        "font-size": "2.5rem",
                        "background-color": PRIMARY_COLOR,
                        "padding": "0",
                        "border": "2px solid black",
                        "border-radius": "10px 10px 0 0"
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
                    # AQI gauge section
                    html.Div([
                        dcc.Graph(id="indoor-gauge", config={"displayModeBar": False})
                    ], style={
                        "padding": "0",
                        "border": "2px solid black",
                        "border-top": "none",
                        "border-bottom": "none",
                        "height": "115px"
                    }),

                    # Bottom third with temperature box
                    html.Div([
                        html.Div([
                            html.Div("Temperature", className="text-center",
                                     style={
                                         "font-size": "1.25rem",
                                         "font-weight": "bold",
                                         "padding-top": "10px",
                                         "color": "black"
                                     }),
                            html.Div(id="indoor-temp-display",
                                     className="d-flex justify-content-center align-items-center",
                                     style={
                                         "font-size": "1.5rem",
                                         "color": "black",
                                         "text-align": "center",
                                         "margin-top": "2px"
                                     })
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
                                   "border-left": "2px solid black",
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
                            html.Div("Temperature", className="text-center",
                                     style={
                                         "font-size": "1.25rem",
                                         "font-weight": "bold",
                                         "padding-top": "10px",
                                         "color": "black"
                                     }),
                            html.Div(id="outdoor-temp-display",
                                     className="d-flex justify-content-center align-items-center",
                                     style={
                                         "font-size": "1.5rem",
                                         "color": "black",
                                         "text-align": "center",
                                         "margin-top": "2px"
                                     })
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

        # Centered Fan Control Button & associated modals
        dbc.Row([
            html.Div(
                html.Button(button_text, id="disable-fan",
                            className="btn btn-danger btn-lg",
                            style={
                                "width": "100px",
                                "height": "65px",
                                "border-radius": "100px",
                                "font-size": "1.2rem",
                                "color": "Yellow",
                                "backgroundColor": "green" if button_text == "Enable Fan" else "red",
                                "border": "2px solid green" if button_text == "Enable Fan" else "2px solid red"
                            }),
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
                "You have enabled the fan. The fan will start filtering the air and improving air quality. You may now close this window."
            ),
            dbc.ModalFooter(dbc.Button("Close", id="close-notification", className="btn btn-secondary"))
        ], id="modal-notification", is_open=False, backdrop="static", centered=True),

        dcc.Interval(id='interval-component', interval=10 * 1000, n_intervals=0),
        dcc.Store(id='workflow-state', data={'stage': 'initial'})
    ], fluid=True, className="p-4")


def historical_conditions_layout():
    """
    Constructs the historical conditions layout, showing line charts of indoor and outdoor PM readings.
    Includes basic error handling and defaults if data is unavailable.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Limit to last 500 readings
        indoor_data = pd.read_sql("SELECT timestamp, pm25 FROM Indoor ORDER BY timestamp DESC LIMIT 500;", conn)
        outdoor_data = pd.read_sql("SELECT timestamp, pm25_value FROM Outdoor ORDER BY timestamp DESC LIMIT 500;", conn)
        conn.close()
    except Exception as e:
        print(f"Error retrieving historical data: {e}")
        indoor_data = pd.DataFrame(columns=["timestamp", "pm25"])
        outdoor_data = pd.DataFrame(columns=["timestamp", "pm25_value"])

    # Convert timestamps and handle empty data gracefully
    if not indoor_data.empty:
        indoor_data['timestamp'] = pd.to_datetime(indoor_data['timestamp'])
    if not outdoor_data.empty:
        outdoor_data['timestamp'] = pd.to_datetime(outdoor_data['timestamp'])

    # Build the figure
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
            y=outdoor_data['pm25_value'],
            mode='lines',
            name='Outdoor PM',
            line=dict(color='blue', width=2, shape='spline'),
            hoverinfo='x+y',
        ))

    # Configure layout
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
        dbc.Row(dbc.Col(html.H1("Historical Conditions", className="text-center mb-4"))),
        dbc.Row(dbc.Col(dcc.Graph(figure=fig, config={"displayModeBar": False}))),
    ], fluid=True, className="p-4")


###################################################
# APP INITIALIZATION
###################################################

# Create tables if not exists
create_tables()

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
    """
    Switches between dashboard and historical layout based on the URL.
    """
    if pathname == '/':
        return dashboard_layout()
    elif pathname == '/historical':
        return historical_conditions_layout()
    else:
        return html.Div("Page not found", className="text-center")


@app.callback(
    [Output('indoor-gauge', 'figure'),
     Output('outdoor-gauge', 'figure'),
     Output('indoor-temp-display', 'children'),
     Output('outdoor-temp-display', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """
    Periodically fetches the latest indoor/outdoor data from the database and updates:
    - Indoor/Outdoor AQI gauges
    - Indoor/Outdoor temperature displays

    Gracefully handles empty or missing data.
    """
    # Default fallback values
    indoor_aqi = 0
    outdoor_aqi = 0
    indoor_temp_text = "N/A"
    outdoor_temp_text = "N/A"
    indoor_arrow = "⬇️"
    outdoor_arrow = "⬇️"
    indoor_arrow_color = "green"
    outdoor_arrow_color = "green"
    indoor_delta_text = "0"
    outdoor_delta_text = "0"

    try:
        conn = sqlite3.connect(DB_PATH)
        # Fetch last 60 indoor/outdoor values; handle empty results
        indoor_pm = pd.read_sql("SELECT pm25 FROM Indoor ORDER BY timestamp DESC LIMIT 60;", conn)
        outdoor_pm = pd.read_sql("SELECT pm25_value FROM Outdoor ORDER BY timestamp DESC LIMIT 60;", conn)

        indoor_temp_df = pd.read_sql("SELECT temperature FROM Indoor ORDER BY timestamp DESC LIMIT 1;", conn)
        outdoor_temp_df = pd.read_sql("SELECT temperature FROM Outdoor ORDER BY timestamp DESC LIMIT 1;", conn)
        conn.close()

        if not indoor_pm.empty:
            indoor_aqi = round(indoor_pm['pm25'].iloc[0])
            if len(indoor_pm) > 30:
                indoor_delta = indoor_aqi - round(indoor_pm['pm25'].iloc[30:].mean())
            else:
                indoor_delta = 0
            indoor_delta_text = f"+{indoor_delta}" if indoor_delta > 0 else str(indoor_delta)
            indoor_arrow = "⬆️" if indoor_delta > 0 else "⬇️"
            indoor_arrow_color = "red" if indoor_delta > 0 else "green"

        if not outdoor_pm.empty:
            outdoor_aqi = round(outdoor_pm['pm25_value'].iloc[0])
            if len(outdoor_pm) > 30:
                outdoor_delta = outdoor_aqi - round(outdoor_pm['pm25_value'].iloc[30:].mean())
            else:
                outdoor_delta = 0
            outdoor_delta_text = f"+{outdoor_delta}" if outdoor_delta > 0 else str(outdoor_delta)
            outdoor_arrow = "⬆️" if outdoor_delta > 0 else "⬇️"
            outdoor_arrow_color = "red" if outdoor_delta > 0 else "green"

        if not indoor_temp_df.empty:
            indoor_temp_value = round(indoor_temp_df['temperature'].iloc[0], 1)
            indoor_temp_text = f"{indoor_temp_value} °F"
        if not outdoor_temp_df.empty:
            outdoor_temp_value = round(outdoor_temp_df['temperature'].iloc[0], 1)
            outdoor_temp_text = f"{outdoor_temp_value} °F"
    except Exception as e:
        print(f"Error retrieving data in update_dashboard: {e}")

    # Prepare gauge figures
    def get_position_offset(value):
        length = len(str(value))
        if length == 1:
            return 0.45
        elif length == 2:
            return 0.42
        elif length == 3:
            return 0.41
        elif length == 4:
            return 0.38
        return 0.45

    def arrow_position_offset(value):
        length = len(str(value))
        if length == 1:
            return 0.62
        elif length == 2:
            return 0.68
        elif length == 3:
            return 0.70
        elif length == 4:
            return 0.69
        return 0.62

    def delta_position_offset(value):
        length = len(str(value))
        if length == 1:
            return 0.73
        elif length == 2:
            return 0.78
        elif length == 3:
            return 0.84
        elif length == 4:
            return 0.86
        return 0.73

    indoor_emoji = get_aqi_emoji(indoor_aqi)
    outdoor_emoji = get_aqi_emoji(outdoor_aqi)

    # Indoor Gauge
    indoor_gauge = go.Figure(go.Indicator(
        mode="gauge",
        value=indoor_aqi,
        gauge={
            'axis': {'range': [0, 150]},
            'bar': {'color': get_gauge_color(indoor_aqi)},
            'bgcolor': "lightgray",
            'bordercolor': "black",
        },
        domain={'x': [0, 1], 'y': [0, 1]}
    ))
    indoor_gauge.update_layout(height=300, margin=dict(t=0, b=50, l=50, r=50))
    indoor_gauge.add_annotation(
        x=get_position_offset(indoor_aqi),
        y=0.25,
        text=f"<b>AQI:{indoor_aqi}</b>",
        showarrow=False,
        font=dict(size=30, color="black"),
        xanchor="center",
        yanchor="bottom"
    )
    indoor_gauge.add_layout_image(
        dict(
            source=indoor_emoji,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            sizex=0.2, sizey=0.2,
            xanchor="center", yanchor="middle"
        )
    )
    indoor_gauge.add_annotation(
        x=arrow_position_offset(indoor_aqi),
        y=0.24,
        text=indoor_arrow,
        font=dict(size=30, color=indoor_arrow_color),
        showarrow=False
    )
    indoor_gauge.add_annotation(
        x=delta_position_offset(indoor_delta_text),
        y=0.28,
        text=indoor_delta_text,
        font=dict(size=20, color=indoor_arrow_color),
        showarrow=False
    )

    # Outdoor Gauge
    outdoor_gauge = go.Figure(go.Indicator(
        mode="gauge",
        value=outdoor_aqi,
        gauge={
            'axis': {'range': [0, 150]},
            'bar': {'color': get_gauge_color(outdoor_aqi)},
            'bgcolor': "lightgray",
            'bordercolor': "black",
        },
        domain={'x': [0, 1], 'y': [0, 1]}
    ))
    outdoor_gauge.update_layout(height=300, margin=dict(t=0, b=50, l=50, r=50))
    outdoor_gauge.add_annotation(
        x=get_position_offset(outdoor_aqi),
        y=0.25,
        text=f"<b>AQI:{outdoor_aqi}</b>",
        showarrow=False,
        font=dict(size=30, color="black"),
        xanchor="center",
        yanchor="bottom"
    )
    outdoor_gauge.add_layout_image(
        dict(
            source=outdoor_emoji,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            sizex=0.2, sizey=0.2,
            xanchor="center", yanchor="middle"
        )
    )
    outdoor_gauge.add_annotation(
        x=arrow_position_offset(outdoor_aqi),
        y=0.24,
        text=outdoor_arrow,
        font=dict(size=30, color=outdoor_arrow_color),
        showarrow=False
    )
    outdoor_gauge.add_annotation(
        x=delta_position_offset(outdoor_delta_text),
        y=0.28,
        text=outdoor_delta_text,
        font=dict(size=20, color=outdoor_arrow_color),
        showarrow=False
    )

    return indoor_gauge, outdoor_gauge, indoor_temp_text, outdoor_temp_text


@app.callback(
    [Output('disable-fan', 'children'),
     Output('disable-fan', 'style'),
     Output('modal-confirm', 'is_open'),
     Output('modal-warning', 'is_open'),
     Output('modal-notification', 'is_open'),
     Output('modal-state-store', 'data')],
    [Input('disable-fan', 'n_clicks'),
     Input('confirm-yes', 'n_clicks'),
     Input('confirm-no', 'n_clicks'),
     Input('warning-yes', 'n_clicks'),
     Input('warning-no', 'n_clicks'),
     Input('close-notification', 'n_clicks')],
    [State('disable-fan', 'children'),
     State('modal-state-store', 'data')],
    prevent_initial_call=True
)
def manage_fan_workflow(disable_fan_clicks, confirm_yes_clicks, confirm_no_clicks,
                        warning_yes_clicks, warning_no_clicks, close_notification_clicks,
                        button_text, modal_state):
    """
    Manages the fan enabling/disabling workflow and modal states:

    Workflow:
    - Start: Button = "Disable Fan"
    - Click "Disable Fan" -> Show Confirm Modal
    - Confirm "Yes" -> Show Warning Modal
    - Warning "Proceed" -> Disable Fan, switch button to "Enable Fan"
    - Click "Enable Fan" -> Enable Fan, show Notification Modal, switch button to "Disable Fan"
    - "No" or "Cancel" buttons close modals without changing state.
    """
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0] if callback_context.triggered else None

    # Current modal states
    modal_confirm = modal_state.get('modal_confirm', False)
    modal_warning = modal_state.get('modal_warning', False)
    modal_notification = modal_state.get('modal_notification', False)

    # Determine current fan state from button text
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

    # Modal and state logic
    if triggered_id == 'disable-fan' and is_fan_on:
        # Fan is ON, user wants to disable -> confirm action
        modal_confirm = True

    elif triggered_id == 'confirm-yes':
        # User confirmed disabling -> show warning
        modal_confirm = False
        modal_warning = True

    elif triggered_id == 'confirm-no':
        # User declined disabling -> close confirm modal
        modal_confirm = False

    elif triggered_id == 'warning-yes':
        # User proceeds with disabling -> disable fan
        modal_warning = False
        update_fan_state("OFF")
        button_text = "Enable Fan"
        button_style["backgroundColor"] = "green"
        button_style["border"] = "2px solid green"

    elif triggered_id == 'warning-no':
        # User canceled warning -> close warning modal
        modal_warning = False

    elif triggered_id == 'disable-fan' and not is_fan_on:
        # User clicks Enable Fan -> actually turn fan ON
        update_fan_state("ON")
        modal_notification = True
        button_text = "Disable Fan"
        button_style["backgroundColor"] = "red"
        button_style["border"] = "2px solid red"

    elif triggered_id == 'close-notification':
        # Close the notification modal after enabling fan
        modal_notification = False

    updated_state = {
        'modal_confirm': modal_confirm,
        'modal_warning': modal_warning,
        'modal_notification': modal_notification
    }

    return button_text, button_style, modal_confirm, modal_warning, modal_notification, updated_state


###################################################
# MAIN
###################################################

if __name__ == '__main__':
    # Run app in production mode (for development, use debug=True)
    app.run_server(debug=False)
