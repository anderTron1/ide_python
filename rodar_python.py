import dash
import dash_ace
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import io
import contextlib
import socket
import pandas as pd
from scipy.stats import norm
import numpy as np
import re

from gerenciar_db import banco_de_dados

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                dash_ace.DashAceEditor(
                    id='editor',
                    value="print('Hellow word!')",
                    theme='monokai',
                    mode='python',
                    tabSize=4,
                    enableBasicAutocompletion=True,
                    enableLiveAutocompletion=True,
                    placeholder='Digite seu código aqui...',
                    style={'height': '90vh',"width": "100%", 'padding': "0px", "margin": "0px"}
                ),
                html.Div([
                    html.Button('Executar', id='run-button', n_clicks=0,
                    style={'background-color': '#2F4F4F', 'border': 'none', 'margin': '10px 5px', 'color': "#fff"}),
                    dcc.RadioItems(
                        id="lista-grafico",
                        options=[
                           {"label": "Barra", "value": "barra"},
                           {"label": "Linha", "value": "linha"},
                           {"label": "Pizza", "value": "pizza"},
                           {"label": "Box", "value": "box"},
                           {"label": "Dist. Normal", "value": "dist"}
                        ],
                        labelStyle={'display': 'inline', "margin-left": "10px"},
                        inline=True
                    )
                ],style={"display": "flex"})
            ])
        ], style={"width": "50%", 
                  'margin-right': "10px", 
                  'padding': "0px", 
                  "margin": "0px",
                  'border': '1px solid white'}),
        dbc.Col([
            html.Div(id='output', style={"overflowY": "scroll", "height": "40vh"}),
            dcc.Graph(id="grafico", style={"height": "50vh", "marginTop": "10px", 'backgroundColor': 'rgba(0, 0, 0, 0)'})
        ], style={"border": "1px solid white", "width": "50%",'height': '96vh'})
    ], style={"display": "flex", "width": "100%"})
], style={ 'padding': "0px", "margin": "0px", "margin-left": '20px', "width": "98%"}, fluid=True)

def get_ipv4_address():
    # Cria um socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Conecta-se a um servidor (neste caso, o Google DNS) para obter o endereço IP
        s.connect(('8.8.8.8', 80))
        # Obtém o endereço IPv4 atribuído ao socket
        ipv4_address = s.getsockname()[0]
    except Exception as e:
        #print("Ocorreu um erro ao obter o endereço IPv4:", e)
        ipv4_address = 'localhost'
        pass
    finally:
        # Fecha o socket
        s.close()
    return ipv4_address

@app.callback(
    [Output('output', 'children'), Output('grafico', 'figure')],
    [Input('run-button', 'n_clicks'),
     Input("lista-grafico", "value")],
    [State('editor', 'value')]
)
def run_code(n_clicks, lista_grafico, code):
    fig = go.Figure()
    fig.update_layout(barmode='group',  
                                  xaxis={'type': 'category', 'title': 'Colunas'},
                                  plot_bgcolor='rgba(0, 0, 0, 0)',  # Fundo do gráfico
                                  paper_bgcolor='rgb(30, 30, 30)',  # Fundo do papel
                                  font=dict(color='white'),  # Cor da fonte
                                  margin=dict(l=5, r=5, t=30, b=5))
    if n_clicks > 0:
         # Capturar a saída padrão
        str_io = io.StringIO()
        data = None
        
        try:
            
            with contextlib.redirect_stdout(str_io):
                exec_globals = {'pd': pd}

                padrao = r"(##([a-zA-Z0-9_-]+\.db)##.*?##([a-zA-Z0-9_-]+\.db)##)(.*)"
                resultado = re.search(padrao, code, re.S)
                if resultado:
                    script = re.sub(r'##([a-zA-Z0-9_-]+\.db)##', '', resultado.group(1).strip())
                    #print(script)
                    script_sql = "##" +resultado.group(3).strip() +"##" + script
                    banco_de_dados(script_sql)
                    exec(resultado.group(4).strip(), exec_globals)
                else:
                    exec(code, exec_globals)


            if 'grafico' in exec_globals and isinstance(exec_globals['grafico'], pd.DataFrame):
                data = exec_globals['grafico']
                if lista_grafico == "barra":                
                    #for column in data.columns:
                    for column in data.columns:
                        fig.add_trace(go.Bar(x=[column], y=data[column].values, name=column))
                    fig.update_layout(title=dict(text="Gráfico de barra", x=0.5))
                elif lista_grafico == "linha":
                    for column in data.columns:
                        if column != "x":
                            fig.add_trace(go.Scatter(x=data["x"], y=data[column].values, name=column))
                        fig.update_layout(title=dict(text="Gráfico de Linha", x=0.5))
                elif lista_grafico == "pizza":
                    for column in data.columns:
                        if column != "x":
                            fig.add_trace(go.Pie(labels=data["x"], values=data[column].values))
                        fig.update_layout(title=dict(text="Gráfico de Pizza", x=0.5))
                elif lista_grafico == "box":
                    for column in data.columns:
                        fig.add_trace(go.Box(y=data[column], name=column, boxmean="sd"))
                    fig.update_layout(title=dict(text="Gráfico de BoxPlot", x=0.5))
                elif lista_grafico == "dist":
                    
                    for column in data.columns:
                        mean = data[column].mean()
                        std = data[column].std()
                        """fig.add_trace(go.Histogram(
                            x=data[column],              # Dados para o eixo x
                            #nbinsx=10,                    # Número de bins
                            #marker=dict(color='blue'),    # Cor das barras
                            #opacity=0.75,                 # Opacidade das barras
                            name=column,
                            marker=dict(color='blue', line=dict(color='black', width=1)),
                            histnorm='probability density',
                        ))"""
                        fig.update_layout(title=dict(text="Gráfico de Distribuição Normal", x=0.5))

                        x_values = np.linspace(data[column].min(), data[column].max(), 100)
                        y_values = norm.pdf(x_values, mean, std)
                        #fig.update_layout(barmode='overlay')

                        fig.add_trace(go.Scatter(x=x_values, y=y_values, mode='lines', name=f'Curva[{column}]', 
                            line=dict(width=2)))
                        #fig.add_trace(go.Bar(x=x_values, y=y_values, name=column))
            else:
                    fig = go.Figure()
                    fig.update_layout(barmode='group',  
                                      xaxis={'type': 'category', 'title': 'Colunas'},
                                      plot_bgcolor='rgba(0, 0, 0, 0)',  # Fundo do gráfico
                                      paper_bgcolor='rgb(30, 30, 30)',  # Fundo do papel
                                      font=dict(color='white'),  # Cor da fonte
                                      margin=dict(l=5, r=5, t=30, b=5))
        except Exception as e:
            return html.Pre(f'Erro na execução do código: {e}'), fig
        return html.Pre(str_io.getvalue()), fig
    return '', fig

if __name__ == '__main__':
    app.run_server(debug=True)