import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import plotly.graph_objects as go

import os
import datetime
import pandas as pd

remote_dir = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'

# read data
confirmed = pd.read_csv(os.path.join(remote_dir, 'time_series_covid19_confirmed_global.csv'))
deaths = pd.read_csv(os.path.join(remote_dir, 'time_series_covid19_deaths_global.csv'))
recovered = pd.read_csv(os.path.join(remote_dir, 'time_series_covid19_recovered_global.csv'))

# format data

def add_column_countries_provinces(df):
    fmt = lambda x: '' if x == 'nan' else ' - ' + x
    aux = df['Country/Region'].astype(str) + df['Province/State'].astype(str).map(fmt)
    df['countries_provinces'] = aux
    return df

confirmed = add_column_countries_provinces(confirmed)
deaths = add_column_countries_provinces(deaths)
recovered = add_column_countries_provinces(recovered)



def get_country_data(df, pattern, drop_cols=['Country/Region', 'Province/State', 'Lat', 'Long', 'countries_provinces']):
    # ts = df[df['countries_provinces'].str.contains(pattern)]
    ts = df[df['countries_provinces'] == pattern]
    ts = ts.drop(drop_cols, axis=1)
    return ts

def get_country_dataframe(country):
    conf = get_country_data(confirmed, country)
    deat = get_country_data(deaths, country)
    reco = get_country_data(recovered, country)
    df = pd.concat({'Confirmed': conf, 'Deaths': deat, 'Recovered': reco})
    df = df.set_index(df.index.droplevel(1))
    df = df.T
    df['Active (C-R-D)'] = df['Confirmed'] - df['Recovered'] - df['Deaths']
    df['Active + Deaths (C-R)'] = df['Confirmed'] - df['Recovered']
    df.index = pd.to_datetime(df.index)
    return df


app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)

server = app.server

app.layout = html.Div([

    dcc.Markdown('''
# COVID-19 Data

Data sourced automatically from [Johns Hopkins University Center for Systems Science and Engineering (JHU-CSSE)](https://github.com/CSSEGISandData/COVID-19)
'''),
    html.Label('Select country:'),
    dcc.Dropdown(
        id='dd-input-countries',
        options=[{'label': x, 'value': x} for x in confirmed['countries_provinces']],
        value='New Zealand',
        style={'width':'60%'}
    ),
    html.Div(id='dd-output-graph'),
    html.A('Code on Github', href='https://github.com/rosatrancoso/dash-covid19-csse'),
    html.Br(),
    html.A("Data Source", href='https://github.com/CSSEGISandData/COVID-19'),
])


@app.callback(
    dash.dependencies.Output('dd-output-graph', 'children'),
    [dash.dependencies.Input('dd-input-countries', 'value')])
def update_output(value):
    if value is not '':
        df = get_country_dataframe(value)
        data = []
        colors = ['blue', 'green', 'red']
        for i,yname in enumerate(['Confirmed', 'Recovered', 'Deaths']):
            data += [go.Scatter(x=df.index, y=df[yname],name=yname,
                               line=dict(color=colors[i]))]

        yname = 'Active (C-R-D)'
        data += [go.Scatter(x=df.index, y=df[yname],name=yname,
                            line=dict(color='orange'))]

        yname = 'Active + Deaths (C-R)'
        data += [go.Scatter(x=df.index, y=df[yname],name=yname,
                            line=dict(color='orange', dash='dot'))]

        layout = dict(title=value,
                      xaxis_title='Dates',
                      yaxis_title='Number of cases')

        fig = go.Figure(data=data, layout=layout)
        graph = dcc.Graph(figure=fig)
        return [graph]


# Running the server
if __name__ == "__main__":
    app.run_server(debug=True)
    #app.run_server(host='0.0.0.0', debug=True, port=8050)




