import dash
from dash import dcc, html, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import sqlite3
import datetime
import os
import base64
import pandas as pd
import plotly.graph_objs as go
import logging

###################################################
# CONFIG & SETUP
###################################################

DB_PATH = '/home/mainhubs/SAPPHIRES.db'  # Adjust as needed

EXTERNAL_STYLESHEETS = [
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
]

BACKGROUND_COLOR = "#f0f2f5"
PRIMARY_COLOR = "#FFFFCB"

EMOJI_PATHS = {
    "good": "/home/mainhubs/good.png",
    "moderate": "/home/mainhubs/moderate.png",
    "unhealthy_sensitive": "/home/mainhubs/unhealthy_sensitive.png",
    "unhealthy": "/home/mainhubs/unhealthy.png",
    "very_unhealthy": "/home/mainhubs/very_unhealthy.png",
    "hazardous": "/home/mainhubs/hazardous.png"
}

logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(message)s')
logging.debug("Starting application with extended modal workflow.")

def get_db_connection():
    return sqlite3.connect(DB_PATH, timeout=5)

def get_spacing(aqi_length, delta_length):
    # You can customize spacing for different text lengths here if desired.
    return (0, 0, 0, 0, 0, 0)

###################################################
# CREATE / UPGRADE TABLES
###################################################

def create_tables():
    """
    Ensures necessary tables exist.
    Note the updated 'processed_events' to include 'action TEXT NOT NULL'.
    """
    create_tables_script = """
    CREATE TABLE IF NOT EXISTS Indoor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        pm25 REAL,
        temperature REAL,
        humidity REAL
    );

    CREATE TABLE IF NOT EXISTS user_control (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        user_input TEXT
    );

    CREATE TABLE IF NOT EXISTS filter_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        filter_state TEXT CHECK (filter_state IN ('ON','OFF'))
    );

    CREATE TABLE IF NOT EXISTS Outdoor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        pm25_value REAL,
        temperature REAL,
        humidity REAL,
        wifi_strength REAL
    );

    /* Note the new 'action TEXT NOT NULL' column in processed_events */
    CREATE TABLE IF NOT EXISTS processed_events (
        processed_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        processed_timestamp TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS reminders (
        reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        reminder_time TEXT NOT NULL,
        reminder_type TEXT NOT NULL
    );
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executescript(create_tables_script)
    conn.commit()
    conn.close()

create_tables()

###################################################
# HELPER FUNCTIONS
###################################################

def encode_image(image_path):
    if not os.path.exists(image_path):
        return ""
    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except:
        return ""

def get_aqi_emoji(aqi):
    """ Return an emoji string based on the aqi value, or modify as needed. """
    return "😷"  # Placeholder for demonstration

def get_gauge_color(aqi):
    """ Return a color string for the gauge bar based on AQI value thresholds. """
    if aqi < 50:
        return "green"
    elif aqi < 100:
        return "yellow"
    elif aqi < 150:
        return "orange"
    else:
        return "red"

def get_last_filter_state():
    """ Returns the most recent filter_state row (id, filter_state). """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, filter_state FROM filter_state ORDER BY id DESC LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, "OFF")

def is_event_processed(event_id):
    """ Checks if there's a row in processed_events for given event_id. """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT event_id FROM processed_events WHERE event_id=?',(event_id,))
    result = cursor.fetchone()
    conn.close()
    return (result is not None)

def record_event_as_processed(event_id, action):
    """
    Inserts a row into processed_events with a user action
    (e.g. 'ON', 'OFF', 'REMIND_20', 'REMIND_60', etc.).
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO processed_events (event_id, action, processed_timestamp) VALUES (?,?,?)',
                   (event_id, action, timestamp))
    conn.commit()
    conn.close()

def add_reminder(event_id, delay_minutes, reminder_type):
    """ Insert a future reminder for the given event_id. """
    reminder_time = (datetime.datetime.now() + datetime.timedelta(minutes=delay_minutes)).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO reminders (event_id, reminder_time, reminder_type) VALUES (?,?,?)',
                   (event_id, reminder_time, reminder_type))
    conn.commit()
    conn.close()

def get_due_reminder():
    """ Return (event_id, reminder_id) if any reminder_time <= now. """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT event_id, reminder_id FROM reminders WHERE reminder_time <= ?', (current_time,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None)

def remove_reminder(reminder_id):
    """ Deletes a reminder row by ID once it's triggered or no longer needed. """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reminders WHERE reminder_id = ?', (reminder_id,))
    conn.commit()
    conn.close()

def update_user_control_decision(state):
    """
    Inserts a new row into user_control to record final user ON/OFF choice.
    Timestamp for auditing.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_control (timestamp, user_input) VALUES (?,?)', (timestamp, state))
    conn.commit()
    conn.close()

###################################################
# LAYOUTS
###################################################

def dashboard_layout():
    return dbc.Container([
        # For demonstration we add dummy dcc.Graph ID references (in callback below)
        dcc.Graph(id='indoor-gauge'),
        dcc.Graph(id='outdoor-gauge'),
        html.Div(id='indoor-temp-display'),
        html.Div(id='outdoor-temp-display'),

        dcc.Interval(id='interval-component', interval=10*1000, n_intervals=0),

        # Persistent Stores
        dcc.Store(id='on-alert-shown', data=False, storage_type='local'),
        dcc.Store(id='modal-open-state', data=False, storage_type='local'),
        dcc.Store(id='disclaimer-modal-open', data=False, storage_type='local'),
        dcc.Store(id='caution-modal-open', data=False, storage_type='local'),

        # Main Air Quality Degradation Modal
        dbc.Modal(
            [
                dbc.ModalHeader(html.H4("AIR QUALITY DEGRADATION DETECTED", style={'color':'red'}), className="bg-light"),
                dbc.ModalBody(
                    "The air quality in your home has degraded to harmful levels. Would you like to enable the fan and filter the air?",
                    style={'backgroundColor':'#f0f0f0','color':'black'}
                ),
                dbc.ModalFooter([
                    dbc.Button("Yes", id="enable-fan-filterstate", color="success", className="me-2", style={"width":"170px"}),
                    dbc.Button("No, keep fan off", id="keep-fan-off-filterstate", color="danger", className="me-2", style={"width":"170px"}),
                    dbc.Button("Remind me in 20 minutes", id="remind-me-filterstate", color="secondary"),
                    dbc.Button("Remind me in an hour", id="remind-me-hour-filterstate", color="secondary")
                ])
            ],
            id="modal-air-quality-filterstate",
            is_open=False,
            size="lg",
            centered=True,
            backdrop='static',
            keyboard=False
        ),

        # Disclaimer Modal if user chooses "No" from main modal
        dbc.Modal(
            [
                dbc.ModalHeader(html.H4("DISCLAIMER", style={'color':'red'}), className="bg-light"),
                dbc.ModalBody(
                    "Proceeding without enabling the fan may result in harmful or hazardous conditions. Are you sure you want to keep the fan disabled?",
                    style={'backgroundColor':'#f0f0f0','color':'black'}
                ),
                dbc.ModalFooter([
                    dbc.Button("Yes (not recommended)", id="disclaimer-yes", color="danger", className="me-2", style={"width":"180px"}),
                    dbc.Button("No (Enable Fan)", id="disclaimer-no", color="secondary", style={"width":"180px"})
                ])
            ],
            id="modal-disclaimer",
            is_open=False,
            size="lg",
            centered=True,
            backdrop='static',
            keyboard=False
        ),

        # Caution Modal if user insists on keeping fan off after disclaimer
        dbc.Modal(
            [
                dbc.ModalHeader(html.H4("CAUTION", style={'color':'red'}), className="bg-light"),
                dbc.ModalBody(
                    "The fan is currently turned off. Please note that you may be exposed to poor air quality. To enable the fan later, please come back to this dashboard and select the Enable Fan option when prompted.",
                    style={'backgroundColor':'#f0f0f0','color':'black'}
                ),
                dbc.ModalFooter([
                    dbc.Button("Close", id="caution-close", color="secondary", style={"width":"100px"})
                ])
            ],
            id="modal-caution",
            is_open=False,
            size="lg",
            centered=True,
            backdrop='static',
            keyboard=False
        ),

        html.Div(id='relay-status', className="text-center mt-4")
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
# INITIALIZE DASH APP
###################################################

app = dash.Dash(
    __name__,
    external_stylesheets=EXTERNAL_STYLESHEETS,
    suppress_callback_exceptions=True,
    meta_tags=[{"name":"viewport","content":"width=device-width,initial-scale=1"}]
)

app.layout = html.Div(
    style={"overflow": "hidden", "height": "100vh"},
    children=[
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content', style={"outline": "none"})
    ]
)

# Set custom index string
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
                margin:0;
                overflow:hidden;
                font-family:"Roboto",sans-serif;
            }
        </style>
        <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
    </head>
    <body>
        {%app_entry%}
        <script>
            let startX=0,endX=0;
            document.addEventListener('touchstart',function(e){startX=e.changedTouches[0].screenX;},false);
            document.addEventListener('touchend',function(e){endX=e.changedTouches[0].screenX;handleSwipe();},false);
            function handleSwipe(){
                const deltaX=endX-startX;
                if(deltaX>50){
                    window.history.pushState({},"","/");
                    window.dispatchEvent(new PopStateEvent('popstate'));
                }else if(deltaX<-50){
                    window.history.pushState({},"","/historical");
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
# PAGE ROUTING
###################################################

@app.callback(
    Output('page-content','children'),
    Input('url','pathname')
)
def display_page(pathname):
    if pathname == '/':
        return dashboard_layout()
    elif pathname == '/historical':
        return historical_conditions_layout()
    else:
        return html.Div("Page not found", className="text-center")

###################################################
# DASHBOARD UPDATE CALLBACK
###################################################
@app.callback(
    [
        Output('indoor-gauge','figure'),
        Output('outdoor-gauge','figure'),
        Output('indoor-temp-display','children'),
        Output('outdoor-temp-display','children')
    ],
    [Input('interval-component','n_intervals')]
)
def update_dashboard(n):
    """
    Periodically fetches the latest indoor/outdoor data from the database and updates:
    - Indoor/Outdoor AQI gauges
    - Indoor/Outdoor temperature displays
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
        # Fetch last 60 indoor/outdoor values
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

    def get_x_positions(aqi, delta_text, base_x=0.45, char_spacing=0.02):
        """
        Compute relative x positions for AQI value, arrow, and delta based on text length.
        """
        aqi_length = len(str(aqi))
        delta_length = len(delta_text)
        # You can refine logic for text alignment here as needed
        adjusted_base_x = base_x - (aqi_length * char_spacing)

        aqi_x = adjusted_base_x
        arrow_x = aqi_x + (aqi_length * char_spacing * 1.5)
        delta_x = aqi_x + (aqi_length * char_spacing * 2)
        return aqi_x, arrow_x, delta_x

    indoor_emoji = get_aqi_emoji(indoor_aqi)
    outdoor_emoji = get_aqi_emoji(outdoor_aqi)

    # Indoor Gauge
    aqi_x, arrow_x, delta_x = get_x_positions(indoor_aqi, indoor_delta_text)
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
        x=aqi_x, y=0.25,
        text=f"<b>AQI:{indoor_aqi}</b>",
        showarrow=False,
        font=dict(size=30, color="black"),
        xanchor="center", yanchor="bottom"
    )
    indoor_gauge.add_annotation(
        x=arrow_x, y=0.24,
        text=indoor_arrow,
        font=dict(size=30, color=indoor_arrow_color),
        showarrow=False
    )
    indoor_gauge.add_annotation(
        x=delta_x, y=0.28,
        text=indoor_delta_text,
        font=dict(size=20, color=indoor_arrow_color),
        showarrow=False
    )

    # Outdoor Gauge
    aqi_x, arrow_x, delta_x = get_x_positions(outdoor_aqi, outdoor_delta_text)
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
        x=aqi_x, y=0.25,
        text=f"<b>AQI:{outdoor_aqi}</b>",
        showarrow=False,
        font=dict(size=30, color="black"),
        xanchor="center", yanchor="bottom"
    )
    outdoor_gauge.add_annotation(
        x=arrow_x, y=0.24,
        text=outdoor_arrow,
        font=dict(size=30, color=outdoor_arrow_color),
        showarrow=False
    )
    outdoor_gauge.add_annotation(
        x=delta_x, y=0.28,
        text=outdoor_delta_text,
        font=dict(size=20, color=outdoor_arrow_color),
        showarrow=False
    )

    return indoor_gauge, outdoor_gauge, indoor_temp_text, outdoor_temp_text

###################################################
# MODAL HANDLING CALLBACK
###################################################
@app.callback(
    [
        Output("modal-air-quality-filterstate", "is_open"),
        Output("on-alert-shown", "data"),
        Output("relay-status", "children"),
        Output("modal-disclaimer", "is_open"),
        Output("modal-caution", "is_open"),
        Output("modal-open-state", "data"),
        Output("disclaimer-modal-open", "data"),
        Output("caution-modal-open", "data")
    ],
    [
        Input("interval-component", "n_intervals"),
        Input("enable-fan-filterstate", "n_clicks"),
        Input("keep-fan-off-filterstate", "n_clicks"),
        Input("remind-me-filterstate", "n_clicks"),
        Input("remind-me-hour-filterstate", "n_clicks"),
        Input("disclaimer-yes", "n_clicks"),
        Input("disclaimer-no", "n_clicks"),
        Input("caution-close", "n_clicks")
    ],
    [
        State("on-alert-shown", "data"),
        State("modal-open-state", "data"),
        State("disclaimer-modal-open", "data"),
        State("caution-modal-open", "data")
    ]
)
def handle_filter_state_event(n_intervals,
                              enable_clicks,
                              keep_off_clicks,
                              remind_me_clicks,
                              remind_me_hour_clicks,
                              disclaimer_yes_clicks,
                              disclaimer_no_clicks,
                              caution_close_clicks,
                              alert_shown,
                              modal_open_state,
                              disclaimer_open_state,
                              caution_open_state):
    """
    Handles filter-state ON event, user actions in modal, disclaimers, and reminders.
    """
    triggered_id = callback_context.triggered[0]["prop_id"].split(".")[0]

    # Start from stored states
    modal_open = modal_open_state
    disclaimer_open = disclaimer_open_state
    caution_open = caution_open_state

    status_message = "Monitoring filter state..."
    updated_alert_shown = alert_shown

    last_event_id, last_state = get_last_filter_state()
    due_reminder_event_id, reminder_id = get_due_reminder()

    # Check if a reminder is due
    if due_reminder_event_id and (due_reminder_event_id == last_event_id) and (last_state == "ON"):
        # Show modal again
        modal_open = True
        disclaimer_open = False
        caution_open = False
        updated_alert_shown = True
        remove_reminder(reminder_id)
        status_message = "Reminder due. Showing modal."

    # If interval triggered and filter_state=ON for a new event
    elif triggered_id == "interval-component" and last_state == "ON" and last_event_id:
        # Only show if not processed
        if not is_event_processed(last_event_id):
            modal_open = True
            disclaimer_open = False
            caution_open = False
            updated_alert_shown = True
            status_message = f"Filter ON detected. Event {last_event_id}. User attention required."

            # Option A: Record a "SHOWING_MODAL" action now (optional).
            record_event_as_processed(last_event_id, "SHOWING_MODAL")

    # Handle user clicks:

    if triggered_id == "enable-fan-filterstate":
        # User chooses yes → ON
        update_user_control_decision("ON")
        modal_open = False
        disclaimer_open = False
        caution_open = False
        status_message = "Fan enabled by user choice."

        if last_event_id:
            record_event_as_processed(last_event_id, "ON")

    elif triggered_id == "keep-fan-off-filterstate":
        # User chooses no in main modal → show disclaimer
        modal_open = False
        disclaimer_open = True
        caution_open = False
        status_message = "User chose to keep fan off"

    elif triggered_id == "remind-me-filterstate":
        # User wants 20-min reminder
        modal_open = False
        disclaimer_open = False
        caution_open = False
        if last_event_id:
            add_reminder(last_event_id, 20, "20 minutes")
            record_event_as_processed(last_event_id, "REMIND_20")
        status_message = "Reminder set for 20 minutes."

    elif triggered_id == "remind-me-hour-filterstate":
        # User wants 1-hour reminder
        modal_open = False
        disclaimer_open = False
        caution_open = False
        if last_event_id:
            add_reminder(last_event_id, 60, "1 hour")
            record_event_as_processed(last_event_id, "REMIND_60")
        status_message = "Reminder set for 1 hour."

    elif triggered_id == "disclaimer-yes":
        # User insists on not enabling fan even after disclaimer
        modal_open = False
        disclaimer_open = False
        caution_open = True
        status_message = "User insisted on keeping fan off after disclaimer"

        # Now we finalize OFF in user_control
        update_user_control_decision("OFF")

        if last_event_id:
            record_event_as_processed(last_event_id, "OFF")

    elif triggered_id == "disclaimer-no":
        # User changes mind at disclaimer → enable fan
        update_user_control_decision("ON")
        modal_open = False
        disclaimer_open = False
        caution_open = False
        status_message = "User decided to turn fan on at disclaimer"

        if last_event_id:
            record_event_as_processed(last_event_id, "ON")

    elif triggered_id == "caution-close":
        # Caution modal closed
        modal_open = False
        disclaimer_open = False
        caution_open = False
        status_message = "Caution modal closed, user aware fan is off."

    return (
        modal_open,
        updated_alert_shown,
        status_message,
        disclaimer_open,
        caution_open,
        modal_open,
        disclaimer_open,
        caution_open
    )

if __name__ == '__main__':
    app.run_server(debug=False)
