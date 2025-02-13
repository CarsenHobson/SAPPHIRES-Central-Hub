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

DB_PATH = '/home/mainhubs/SAPPHIREStest.db'  # Adjust path if needed

BACKGROUND_COLOR = "#f0f2f5"
PRIMARY_COLOR = "#FFFFCB"
SUCCESS_COLOR = "#28a745"
WARNING_COLOR = "#ffc107"
DANGER_COLOR = "#dc3545"

EXTERNAL_STYLESHEETS = [
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
]

EMOJI_PATHS = {
    "good": "/home/emojis/mainhubs/good.png",
    "moderate": "/home/emojis/mainhubs/moderate.png",
    "unhealthy_sensitive": "/home/emojis/mainhubs/unhealthy_sensitive.png",
    "unhealthy": "/home/emojis/mainhubs/unhealthy.png",
    "very_unhealthy": "/home/emojis/mainhubs/very_unhealthy.png",
    "hazardous": "/home/emojis/mainhubs/hazardous.png"
}

logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logging.debug("Starting application with extended modal workflow and error handling.")

###################################################
# DATABASE CONNECTION WITH ERROR HANDLING
###################################################

def get_db_connection():
    """
    Attempts to open a connection to the SQLite DB.
    Logs and re-raises on error.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        raise

###################################################
# HELPER FUNCTIONS
###################################################

def encode_image(image_path):
    """
    Returns a base64-encoded string of the image at image_path.
    Logs a warning if file does not exist or can't be read.
    """
    if not os.path.exists(image_path):
        logging.warning(f"Image file not found: {image_path}")
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
        print(f"Error selecting emoji for AQI {aqi}: {e}")
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
    """
    Returns a simple fallback gauge figure to display when an error occurs
    or data is unavailable.
    """
    fig = go.Figure()
    fig.add_annotation(text="Data Unavailable", x=0.5, y=0.5, showarrow=False, font=dict(size=16))
    fig.update_layout(
        height=300,
        margin=dict(t=0, b=50, l=50, r=50),
        paper_bgcolor="lightgray"
    )
    return fig

def get_last_filter_state():
    """
    Returns (id, filter_state) of the most recent entry in filter_state.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, filter_state FROM filter_state ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        if not result:
            logging.info("No rows found in filter_state table; returning OFF as default.")
            return (None, "OFF")
        return result
    except sqlite3.Error as e:
        logging.error(f"Error fetching last_filter_state: {e}")
        return (None, "OFF")
    except Exception as ex:
        logging.exception(f"Unexpected error in get_last_filter_state: {ex}")
        return (None, "OFF")
    finally:
        if conn:
            conn.close()

def get_last_system_state():
    """
    Returns (id, system_input) of the most recent entry in system_control.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, system_input FROM system_control ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        if not result:
            logging.info("No rows found in system_control table; returning OFF as default.")
            return (None, "OFF")
        return result
    except sqlite3.Error as e:
        logging.error(f"Error fetching last_system_state: {e}")
        return (None, "OFF")
    except Exception as ex:
        logging.exception(f"Unexpected error in get_last_system_state: {ex}")
        return (None, "OFF")
    finally:
        if conn:
            conn.close()

def is_event_processed(event_id):
    """
    Checks if the event_id is recorded in processed_events.
    """
    if event_id is None:
        return True  # If there's no event_id, consider it "processed" or non-existent
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT event_id FROM processed_events WHERE event_id=?', (event_id,))
        result = cursor.fetchone()
        return (result is not None)
    except sqlite3.Error as e:
        logging.error(f"Error checking processed_events for event {event_id}: {e}")
        return False
    except Exception as ex:
        logging.exception(f"Unexpected error in is_event_processed: {ex}")
        return False
    finally:
        if conn:
            conn.close()

def record_event_as_processed(event_id, action):
    """
    Inserts a row into processed_events with the user action or event status.
    """
    if event_id is None:
        return
    conn = None
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO processed_events (event_id, action, processed_timestamp)
            VALUES (?, ?, ?)
            ''',
            (event_id, action, timestamp)
        )
        conn.commit()
        logging.info(f"Successfully recorded event {event_id} with action '{action}'")
    except sqlite3.Error as e:
        logging.error(f"Database error while recording event {event_id}: {e}")
    except Exception as ex:
        logging.exception(f"Unexpected error in record_event_as_processed for event {event_id}: {ex}")
    finally:
        if conn:
            conn.close()

def add_reminder(event_id, delay_minutes, reminder_type):
    """
    Inserts a future reminder for the given event_id.
    """
    if event_id is None:
        return
    conn = None
    try:
        reminder_time = (datetime.datetime.now() + datetime.timedelta(minutes=delay_minutes)).strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO reminders (event_id, reminder_time, reminder_type) VALUES (?,?,?)',
            (event_id, reminder_time, reminder_type)
        )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error adding reminder for event {event_id}: {e}")
    except Exception as ex:
        logging.exception(f"Unexpected error in add_reminder: {ex}")
    finally:
        if conn:
            conn.close()

def get_due_reminder():
    """
    Returns (event_id, reminder_id) if a reminder_time <= now is found.
    """
    conn = None
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        cursor = conn.cursor()
        logging.debug(f"Checking for due reminders at {current_time}")
        cursor.execute(
            '''
            SELECT event_id, reminder_id
            FROM reminders
            WHERE reminder_time <= ?
            ORDER BY reminder_time ASC
            LIMIT 1
            ''',
            (current_time,)
        )
        result = cursor.fetchone()
        logging.debug(f"Due reminder found: {result}")
        return result if result else (None, None)
    except sqlite3.Error as e:
        logging.error(f"Error in get_due_reminder: {e}")
        return (None, None)
    finally:
        if conn:
            conn.close()

def remove_reminder(reminder_id):
    """
    Deletes the reminder row by ID once triggered or no longer needed.
    """
    if reminder_id is None:
        return
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reminders WHERE reminder_id=?', (reminder_id,))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error removing reminder {reminder_id}: {e}")
    except Exception as ex:
        logging.exception(f"Unexpected error in remove_reminder: {ex}")
    finally:
        if conn:
            conn.close()

def update_user_control_decision(state):
    """
    Inserts a new row into user_control with 'ON' or 'OFF'.
    """
    conn = None
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        cursor = conn.cursor()
        # Insert the user_input (ON/OFF) in user_control table
        cursor.execute('INSERT INTO user_control (timestamp, user_input) VALUES (?,?)', (timestamp, state))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error updating user_control to {state}: {e}")
    except Exception as ex:
        logging.exception(f"Unexpected error in update_user_control_decision: {ex}")
    finally:
        if conn:
            conn.close()

###################################################
# LAYOUTS
###################################################

def dashboard_layout():
    """
    Constructs the main dashboard layout with all modals/buttons.
    """
    return dbc.Container([
        # Title row with embedded button
        dbc.Row([
            dbc.Col(
                html.Div(
                    [
                        # The title
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
                                    size="sm",  
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

        # Indoor/Outdoor Cards
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
                    }
                ),
                html.Div([
                    html.Div([
                        dcc.Graph(id="indoor-gauge", config={"displayModeBar": False})
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
                    }
                ),
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

        dbc.Row([
            html.Div(
                "Status Loading...",
                id="filter-status-text",
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
                    "background-color": "white",
                    "border-radius": "3.5px",
                    "font-size": "1.7rem",
                    "color": "yellow"
                }
            )
        ], style={"position": "relative", "height": "682px"}, className="g-0"),

        # Main Air Quality Degradation Modal
        dbc.Modal(
            [
                dbc.ModalHeader(
                    html.H4("AIR QUALITY DEGRADATION DETECTED", style={'color':'red'}),
                    className="bg-light"
                ),
                dbc.ModalBody(
                    "The air quality in your home has degraded to harmful levels. "
                    "Would you like to enable the fan and filter the air?",
                    style={'backgroundColor':'#f0f0f0','color':'black'}
                ),
                dbc.ModalFooter([
                    dbc.Button(
                        "Yes",
                        id="enable-fan-filterstate",
                        color="success",
                        className="me-2",
                        style={"width":"170px"}
                    ),
                    dbc.Button(
                        "No, keep fan off",
                        id="keep-fan-off-filterstate",
                        color="danger",
                        className="me-2",
                        style={"width":"170px"}
                    ),
                    dbc.Button(
                        "Remind me in 20 minutes",
                        id="remind-me-filterstate",
                        color="secondary"
                    ),
                    dbc.Button(
                        "Remind me in an hour",
                        id="remind-me-hour-filterstate",
                        color="secondary"
                    )
                ])
            ],
            id="modal-air-quality-filterstate",
            is_open=False,
            size="lg",
            centered=True,
            backdrop='static',
            keyboard=False
        ),

        # Disclaimer Modal
        dbc.Modal(
            [
                dbc.ModalHeader(
                    html.H4("DISCLAIMER", style={'color':'red'}),
                    className="bg-light"
                ),
                dbc.ModalBody(
                    "Proceeding without enabling the fan may result in harmful or hazardous conditions. "
                    "Are you sure you want to keep the fan disabled?",
                    style={'backgroundColor':'#f0f0f0','color':'black'}
                ),
                dbc.ModalFooter([
                    dbc.Button(
                        "Yes (not recommended)",
                        id="disclaimer-yes",
                        color="danger",
                        className="me-2",
                        style={"width":"180px"}
                    ),
                    dbc.Button(
                        "No (Enable Fan)",
                        id="disclaimer-no",
                        color="secondary",
                        style={"width":"180px"}
                    )
                ])
            ],
            id="modal-disclaimer",
            is_open=False,
            size="lg",
            centered=True,
            backdrop='static',
            keyboard=False
        ),

        # Caution Modal
        dbc.Modal(
            [
                dbc.ModalHeader(
                    html.H4("CAUTION", style={'color':'red'}),
                    className="bg-light"
                ),
                dbc.ModalBody(
                    "The fan is currently turned off. Please note that you may be exposed to poor air quality. "
                    "To enable the fan later, please come back to this dashboard and select "
                    "the Enable Fan option when prompted.",
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

        # >>> ADDED for reminder-cancelled: new modal
        dbc.Modal(
            [
                dbc.ModalHeader(
                    html.H4("REMINDER CANCELLED", style={'color': 'red'}),
                    className="bg-light"
                ),
                dbc.ModalBody(
                    "The system no longer thinks the filter should be running. "
                    "We'll discard this reminder and will not prompt you again.",
                    style={'backgroundColor': '#f0f0f0', 'color': 'black'}
                ),
                dbc.ModalFooter([
                    dbc.Button("OK", id="reminder-cancel-close", color="secondary", style={"width": "100px"})
                ])
            ],
            id="modal-reminder-cancelled",
            is_open=False,
            size="lg",
            centered=True,
            backdrop='static',
            keyboard=False
        ),
        # <<< end new modal

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
# INITIALIZE DASH APP
###################################################
app = dash.Dash(
    __name__,
    external_stylesheets=EXTERNAL_STYLESHEETS,
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width,initial-scale=1"}]
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
                // Swipe right -> Go to '/'
                if(deltaX>50){
                    window.history.pushState({},"","/");
                    window.dispatchEvent(new PopStateEvent('popstate'));
                }
                // Swipe left -> Go to '/historical'
                else if(deltaX<-50){
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

# Top-level layout with a single dcc.Interval and all the needed Stores
app.layout = html.Div(
    style={"overflow": "hidden", "height": "100vh"},
    children=[
        dcc.Location(id="url", refresh=False),
        dcc.Interval(id="interval-component", interval=60000, n_intervals=0),

        # dcc.Store components to hold states for modals
        dcc.Store(id="on-alert-shown", data=False),
        dcc.Store(id="modal-open-state", data=False),
        dcc.Store(id="disclaimer-modal-open", data=False),
        dcc.Store(id="caution-modal-open", data=False),
        # >>> ADDED for reminder-cancelled: we'll just open it from the callback, no store needed
        # but we do need an output in the callback. We'll handle that there.

        # The main page rendering container
        html.Div(id="page-content", style={"outline": "none"}),
    ]
)

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
    Input('interval-component','n_intervals')
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
        # Query PM data
        indoor_pm = pd.read_sql("SELECT pm25 FROM Indoor ORDER BY timestamp DESC LIMIT 60;", conn)
        outdoor_pm = pd.read_sql("SELECT pm25 FROM Outdoor ORDER BY timestamp DESC LIMIT 60;", conn)
        indoor_temp_df = pd.read_sql("SELECT temperature FROM Indoor ORDER BY timestamp DESC LIMIT 1;", conn)
        outdoor_temp_df = pd.read_sql("SELECT temperature FROM Outdoor ORDER BY timestamp DESC LIMIT 1;", conn)
        conn.close()

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
        if not indoor_pm.empty:
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
        if not outdoor_pm.empty:
            outdoor_aqi = round(outdoor_pm['pm25'].iloc[0])
            if len(outdoor_pm) > 30:
                outdoor_delta = outdoor_aqi - round(outdoor_pm['pm25'].iloc[30:].mean())
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

        if not outdoor_temp_df.empty:
            outdoor_temp_value = round(outdoor_temp_df['temperature'].iloc[0], 1)
            outdoor_temp_text = f"{outdoor_temp_value} °F"

        max_aqi = max(indoor_aqi, outdoor_aqi, 100)

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

###################################################
# FAN STATUS UPDATE
###################################################
@app.callback(
    Output("filter-status-text", "children"),
    Output("filter-status-text", "style"),
    Input("interval-component", "n_intervals")
)
def update_filter_status(n_intervals):
    """
    Periodically checks if filter_state is 'ON' or 'OFF'
    and updates the text & style.
    """
    try:
        _, filter_state = get_last_filter_state()
    except Exception as e:
        logging.exception(f"Error retrieving filter_state: {e}")
        filter_state = "UNKNOWN"

    base_style = {
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
        "background-color": "white",
        "border-radius": "3.5px",
        "font-size": "1.7rem"
    }

    if filter_state == "ON":
        return "Filter Is On", {**base_style, "color": "green"}
    elif filter_state == "OFF":
        return "Filter Is Off", {**base_style, "color": "red"}
    else:
        return "Status Unknown", {**base_style, "color": "yellow"}

###################################################
# MODAL HANDLING CALLBACK
###################################################
@app.callback(
    [
        Output("modal-air-quality-filterstate", "is_open"),
        Output("on-alert-shown", "data"),
        Output("modal-disclaimer", "is_open"),
        Output("modal-caution", "is_open"),
        # >>> ADDED for reminder-cancelled
        Output("modal-reminder-cancelled", "is_open"),
    ],
    [
        Input("interval-component", "n_intervals"),
        Input("enable-fan-filterstate", "n_clicks"),
        Input("keep-fan-off-filterstate", "n_clicks"),
        Input("remind-me-filterstate", "n_clicks"),
        Input("remind-me-hour-filterstate", "n_clicks"),
        Input("disclaimer-yes", "n_clicks"),
        Input("disclaimer-no", "n_clicks"),
        Input("caution-close", "n_clicks"),
        Input("reminder-cancel-close", "n_clicks"),  # new close button
    ],
    [
        State("on-alert-shown", "data"),
        State("modal-air-quality-filterstate", "is_open"),
        State("modal-disclaimer", "is_open"),
        State("modal-caution", "is_open"),
        State("modal-reminder-cancelled", "is_open"),
    ],
    prevent_initial_call=True,
)
def handle_filter_state_event(
    n_intervals,
    enable_fan_clicks,
    keep_fan_off_clicks,
    remind_me_20_clicks,
    remind_me_hour_clicks,
    disclaimer_yes_clicks,
    disclaimer_no_clicks,
    caution_close_clicks,
    reminder_cancel_close_clicks,  # new
    alert_shown,
    modal_open_state,
    disclaimer_open_state,
    caution_open_state,
    reminder_cancel_open_state
):
    triggered_id = callback_context.triggered[0]["prop_id"].split(".")[0]
    modal_open = modal_open_state
    disclaimer_open = disclaimer_open_state
    caution_open = caution_open_state
    reminder_cancel_open = reminder_cancel_open_state

    try:
        # First, check if there's a due reminder
        due_reminder_event_id, reminder_id = get_due_reminder()
        if due_reminder_event_id and not modal_open and not reminder_cancel_open:
            # >>> ADDED: logic to check if system_control is still ON
            # If system_control is not ON, we show the "reminder cancelled" modal.
            # Else, we show the degrade modal as normal.
            current_event_id, current_system_input = get_last_system_state()
            if current_system_input == "ON":
                logging.info(f"Triggering degrade modal for reminder event_id={due_reminder_event_id}")
                modal_open = True
                remove_reminder(reminder_id)  # remove the reminder row
                return modal_open, True, False, False, False
            else:
                # System is not ON => show "reminder cancelled" modal
                logging.info(f"Reminder cancelled because system_input={current_system_input}")
                reminder_cancel_open = True
                remove_reminder(reminder_id)
                return False, True, False, False, reminder_cancel_open

        # Check if a new "ON" has been inserted into system_control
        last_event_id, last_system_input = get_last_system_state()
        if (
            last_system_input == "ON" and
            not is_event_processed(last_event_id) and
            not modal_open and
            not reminder_cancel_open
        ):
            logging.info(f"Detected new ON in system_control (event_id={last_event_id}). Opening modal.")
            modal_open = True
            record_event_as_processed(last_event_id, "modal_opened")
            return modal_open, True, disclaimer_open, caution_open, reminder_cancel_open

        # Handle user clicks inside the modals
        if triggered_id == "enable-fan-filterstate":
            update_user_control_decision("ON")
            modal_open = False
            record_event_as_processed(last_event_id, "User enabled fan")
            return modal_open, True, False, False, False

        elif triggered_id == "keep-fan-off-filterstate":
            modal_open = False
            record_event_as_processed(last_event_id, "User selected no on first modal")
            disclaimer_open = True
            return modal_open, True, disclaimer_open, False, False

        elif triggered_id == "remind-me-filterstate":
            event_for_reminder = due_reminder_event_id or last_event_id
            add_reminder(event_for_reminder, 20, "20 minutes")
            update_user_control_decision("OFF")
            record_event_as_processed(last_event_id, "User selected to be reminded in 20 minutes")
            modal_open = False
            return modal_open, True, False, False, False

        elif triggered_id == "remind-me-hour-filterstate":
            event_for_reminder = due_reminder_event_id or last_event_id
            add_reminder(event_for_reminder, 60, "1 hour")
            update_user_control_decision("OFF")
            record_event_as_processed(last_event_id, "User selected to be reminded in an hour")
            modal_open = False
            return modal_open, True, False, False, False

        elif triggered_id == "disclaimer-yes":
            update_user_control_decision("OFF")
            record_event_as_processed(last_event_id, "User selected to keep fan off again on disclaimer")
            disclaimer_open = False
            caution_open = True
            return False, True, disclaimer_open, caution_open, False

        elif triggered_id == "disclaimer-no":
            update_user_control_decision("ON")
            record_event_as_processed(last_event_id, "User changed mind and turned fan on in disclaimer")
            disclaimer_open = False
            return False, True, disclaimer_open, False, False

        elif triggered_id == "caution-close":
            caution_open = False
            record_event_as_processed(last_event_id, "User closed the caution")
            return False, True, False, caution_open, False

        # >>> ADDED for reminder-cancelled close
        elif triggered_id == "reminder-cancel-close":
            reminder_cancel_open = False
            return False, True, False, False, reminder_cancel_open

        return modal_open, alert_shown, disclaimer_open, caution_open, reminder_cancel_open

    except Exception as ex:
        logging.exception(f"Error in handle_filter_state_event callback: {ex}")
        # Return defaults if there's an error
        return modal_open_state, alert_shown, disclaimer_open_state, caution_open_state, reminder_cancel_open_state

###################################################
# ROUTING
###################################################
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/':
        return dashboard_layout()
    elif pathname == '/historical':
        return historical_conditions_layout()
    else:
        return html.Div("404 Page Not Found", className="text-center mt-4")

###################################################
# RUN
###################################################
if __name__ == '__main__':
    app.run_server(debug=True)
