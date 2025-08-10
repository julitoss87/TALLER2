import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import datetime as dt
import os # Importar os para manejo de variables de entorno, aunque no se usa directamente en esta función, es buena práctica si se usa en otro lado.


app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Dashboard energia"

server = app.server
app.config.suppress_callback_exceptions = True


# Load data from csv
def load_data():
    """
    Carga el archivo datos_energia.csv, convierte la columna de fecha a datetime
    y establece la fecha como índice del DataFrame.
    """
    try:
        # Cargar el archivo CSV
        # Asegúrate de que 'datos_energia.csv' esté en el mismo directorio que app.py
        df = pd.read_csv('datos_energia.csv')

        # Convertir la columna de fecha a formato datetime
        # Se ha corregido el nombre de la columna a 'time' según tu CSV.
        df['time'] = pd.to_datetime(df['time'])

        # Establecer la columna de fecha como índice del DataFrame
        # Se ha corregido el nombre de la columna a 'time'
        df.set_index('time', inplace=True)

        # Retornar el DataFrame cargado y procesado
        return df
    except FileNotFoundError:
        print("Error: El archivo 'datos_energia.csv' no se encontró. Asegúrate de que esté en el mismo directorio que app.py.")
        return pd.DataFrame() # Retorna un DataFrame vacío en caso de error
    except KeyError:
        # Este error ahora debería ser menos probable si la columna se llama 'time'
        print("Error: La columna de tiempo ('time') no se encontró en 'datos_energia.csv'. Por favor, verifica el nombre de la columna de fecha/hora.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Ocurrió un error inesperado al cargar los datos: {e}")
        return pd.DataFrame()

# Cargar datos al inicio de la aplicación
data = load_data()

# Graficar serie
def plot_series(data, initial_date, proy):
    # Asegurarse de que 'data' no esté vacío
    if data.empty:
        return go.Figure().add_annotation(text="No hay datos para mostrar. Verifica 'datos_energia.csv'.",
                                          xref="paper", yref="paper", showarrow=False,
                                          font=dict(size=16, color="red"))

    data_plot = data.loc[initial_date:]
    # Asegurarse de que la rebanada no sea mayor que el DataFrame
    end_index = min(len(data_plot), len(data_plot) - (120 - proy))
    data_plot = data_plot[:end_index]

    fig = go.Figure([
        go.Scatter(
            name='Demanda energética',
            x=data_plot.index,
            y=data_plot['AT_load_actual_entsoe_transparency'],
            mode='lines',
            line=dict(color="#188463"),
        ),
        go.Scatter(
            name='Proyección',
            x=data_plot.index,
            y=data_plot['forecast'],
            mode='lines',
            line=dict(color="#bbffeb",),
        ),
        go.Scatter(
            name='Upper Bound',
            x=data_plot.index,
            y=data_plot['Upper bound'],
            mode='lines',
            marker=dict(color="#444"),
            line=dict(width=0),
            showlegend=False
        ),
        go.Scatter(
            name='Lower Bound',
            x=data_plot.index,
            y=data_plot['Lower bound'],
            marker=dict(color="#444"),
            line=dict(width=0),
            mode='lines',
            fillcolor="rgba(242, 255, 251, 0.3)",
            fill='tonexty',
            showlegend=False
        )
    ])

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis_title='Demanda total [MW]',
        hovermode="x"
    )
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#2cfec1")
    fig.update_xaxes(showgrid=True, gridwidth=0.25, gridcolor='#7C7C7C')
    fig.update_yaxes(showgrid=True, gridwidth=0.25, gridcolor='#7C7C7C')

    return fig


def description_card():
    """
    :return: A Div containing dashboard title & descriptions.
    """
    return html.Div(
        id="description-card",
        children=[
            html.H3("Pronóstico de producción energética"),
            html.Div(
                id="intro",
                children="Esta herramienta contiene información sobre la demanda energética total en Austria cada hora según lo públicado en ENTSO-E Data Portal. Adicionalmente, permite realizar pronósticos hasta 5 dias en el futuro."
            ),
        ],
    )


def generate_control_card():
    """
    :return: A Div containing controls for graphs.
    """
    # Asegurarse de que 'data' no esté vacío antes de acceder a sus propiedades
    min_date = min(data.index.date) if not data.empty else dt.date.today()
    max_date = max(data.index.date) if not data.empty else dt.date.today()
    initial_date_picker = max(data.index.date) - dt.timedelta(days=7) if not data.empty else dt.date.today()
    initial_hour_dropdown = pd.to_datetime(max(data.index)-dt.timedelta(days=7)).hour if not data.empty else 0


    return html.Div(
        id="control-card",
        children=[

            # Fecha inicial
            html.P("Seleccionar fecha y hora inicial:"),

            html.Div(
                id="componentes-fecha-inicial",
                children=[
                    html.Div(
                        id="componente-fecha",
                        children=[
                            dcc.DatePickerSingle(
                                id='datepicker-inicial',
                                min_date_allowed=min_date,
                                max_date_allowed=max_date,
                                initial_visible_month=min_date,
                                date=initial_date_picker
                            )
                        ],
                        style=dict(width='30%')
                    ),
                    
                    html.P(" ",style=dict(width='5%', textAlign='center')),
                    
                    html.Div(
                        id="componente-hora",
                        children=[
                            dcc.Dropdown(
                                id="dropdown-hora-inicial-hora",
                                options=[{"label": i, "value": i} for i in np.arange(0,25)],
                                value=initial_hour_dropdown,
                                # style=dict(width='50%', display="inline-block")
                            )
                        ],
                        style=dict(width='20%')
                    ),
                ],
                style=dict(display='flex')
            ),

            html.Br(),

            # Slider proyección
            html.Div(
                id="campo-slider",
                children=[
                    html.P("Ingrese horas a proyectar:"),
                    dcc.Slider(
                        id="slider-proyeccion",
                        min=0,
                        max=119,
                        step=1,
                        value=0,
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                    )
                ]
            )     
     
        ]
    )


app.layout = html.Div(
    id="app-container",
    children=[
        
        # Left column
        html.Div(
            id="left-column",
            className="four columns",
            children=[description_card(), generate_control_card()]
            + [
                html.Div(
                    ["initial child"], id="output-clientside", style={"display": "none"}
                )
            ],
        ),
        
        # Right column
        html.Div(
            id="right-column",
            className="eight columns",
            children=[


                # Grafica de la serie de tiempo
                html.Div(
                    id="model_graph",
                    children=[
                        html.B("Demanda energética total en Austria [MW]"),
                        html.Hr(),
                        dcc.Graph(
                            id="plot_series",  
                        )
                    ],
                ),

            
            ],
        ),
    ],
)


@app.callback(
    Output(component_id="plot_series", component_property="figure"),
    [Input(component_id="datepicker-inicial", component_property="date"),
    Input(component_id="dropdown-hora-inicial-hora", component_property="value"),
    Input(component_id="slider-proyeccion", component_property="value")]
)
def update_output_div(date, hour, proy):

    # Asegurarse de que 'data' no esté vacío antes de procesar
    if data.empty:
        return go.Figure().add_annotation(text="No hay datos cargados para generar el gráfico.",
                                          xref="paper", yref="paper", showarrow=False,
                                          font=dict(size=16, color="red"))

    if ((date is not None) & (hour is not None) & (proy is not None)):
        hour = str(hour)
        minute = str(0)

        initial_date = date + " " + hour + ":" + minute
        initial_date = pd.to_datetime(initial_date, format="%Y-%m-%d %H:%M")

        # Graficar
        plot = plot_series(data, initial_date, int(proy))
        return plot
    return go.Figure() # Retornar una figura vacía si las entradas no son válidas


# Run the server
if __name__ == "__main__":
    app.run(debug=True) # Se ha cambiado app.run_server a app.run
# Modificacion de prueba
