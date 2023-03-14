import io
import numpy as np
import pandas as pd
from datetime import timedelta, datetime
from dash import html, dcc, Input, Output
import plotly.express as px

import dash_bootstrap_components as dbc

from styles.styles import TITLE_STYLE, MARKDOWN_STYLE, CONTENT_STYLE, \
    DROPDOWN_STYLE, RADIOITEMS_STYLE, DROPDOWN_STYLE_LONG, TAB_STYLE, TABS_STYLES, TAB_SELECTED_STYLE, \
    colors, colors_scenario
from inputs.inputs import date_values_rts, date_values_t7k, energy_types, energy_types_asset_ids_rts_csv, energy_types_asset_ids_t7k_csv
from markdown.scenarios import markdown_text_scenario
from app import app, dbx

def dcc_tab_scenariovisualize(label= 'RTS',
                              date_values = date_values_rts, date_values_id = 'date_values_rts',
                              energy_types = energy_types, energy_types_id = 'energy_types_rts',
                              asset_id = 'asset_ids_rts',
                              scenario_plot_id = 'rts_scenario_plot_notuning'):
    dcc_tab = dcc.Tab(label=label,
            children=[
                dbc.Row(
                    dbc.Col([
                        html.H3(
                            'Visualize the Particular Scenario'),
                        html.Label(
                            'Please select the following options')
                    ]),
                ),

                # dbc.Row(
                #     dbc.Col([
                #         html.Br(),
                #         html.Label('Select Version'),
                #         dcc.RadioItems(
                #             options={'tuning': 'Tuning', 'notuning': 'No Tuning'},
                #             id='version_t7k',
                #             value='tuning',
                #             style=RADIOITEMS_STYLE)
                #     ])
                # ),

                dbc.Row(
                    dbc.Col([
                        html.Label('Select Day'),
                        dcc.Dropdown(date_values,
                                     id=date_values_id,
                                     value=date_values[0],
                                     style=DROPDOWN_STYLE)
                    ])
                ),

                # radioitem
                dbc.Row([
                    dbc.Col([
                        html.Br(),
                        html.Label('Select Asset Type'),
                        dcc.RadioItems(
                            list(
                                energy_types),
                            'load',
                            id=energy_types_id,
                            style=RADIOITEMS_STYLE)
                    ])
                ]),

                # dropdown
                dbc.Row([
                    dbc.Col([
                        html.Label('Select Asset ID'),
                        dcc.Dropdown(id=asset_id,
                                     style=DROPDOWN_STYLE_LONG),
                        # html.Br(),
                        # html.Button('Download', id='btn-nclicks-1', n_clicks=0),
                        html.Hr()
                    ])
                ]),

                # plot
                html.H3('Plot of the Scenario Selected'),
                html.Wbr(),
                dbc.Row(dbc.Col([
                    dcc.Graph(
                        id=scenario_plot_id)
                ]))
            ],
            style=TAB_STYLE,
            selected_style=TAB_SELECTED_STYLE)
    return dcc_tab


html_div_scenariooverview = html.Div(children=[

    html.H1(
        children='Energy Demand Scenarios Geneartion via Stochastic Model',
        style=TITLE_STYLE
    ),

    html.Div([
        dcc.Markdown(children=markdown_text_scenario,
                     style=MARKDOWN_STYLE),
        html.A(
            "Link to our scenario genearation PGscen github repo",
            href='https://github.com/PrincetonUniversity/PGscen',
            target="_blank")

    ],
        style={'padding': '20px'})
],
    style=CONTENT_STYLE)

html_div_scenariovisualize = html.Div(children=[

                dbc.Row(
                    dbc.Col(html.H3(children='Scenarios Visualization',
                                    style=TITLE_STYLE))
                    , justify='start', align='start'),

                dbc.Row(dcc.Tabs(
                    children=[
                        dcc_tab_scenariovisualize(label='RTS',
                                                  date_values=date_values_rts,
                                                  date_values_id='date_values_rts',
                                                  energy_types=energy_types,
                                                  energy_types_id='energy_types_rts',
                                                  asset_id='asset_ids_rts',
                                                  scenario_plot_id='rts_scenario_plot_notuning'),

                        dcc_tab_scenariovisualize(label='Texast7k',
                                                  date_values=date_values_t7k,
                                                  date_values_id='date_values_t7k',
                                                  energy_types=energy_types,
                                                  energy_types_id='energy_types_t7k',
                                                  asset_id='asset_ids_t7k',
                                                  scenario_plot_id='t7k_scenario_plot_notuning')
                    ],
                    style=TABS_STYLES,
                ),
                    justify='between')
            ], style=CONTENT_STYLE)


def build_timeseries(version, day, asset_type, asset_id,
                     actl_color, fcst_color, scen_color, fper_color):
    day = day.replace('-', '')
    file_path = '/ORFEUS-Alice/data/scenarios_data/{}-scens-csv/{}/{}/{}.csv'.format(
        version, day, asset_type, asset_id)
    _, res = dbx.files_download(file_path)

    with io.BytesIO(res.content) as stream:
        df = pd.read_csv(stream, index_col=0).reset_index()

    # build the list of date values
    # start from 00:00 to 23:00 on the day in local time
    start_date = datetime.strptime(
        '{}-{}-{}-00-00'.format(day[2:4], day[4:6], day[6:8]),
        "%y-%m-%d-%H-%M")
    end_date = start_date + timedelta(hours=23)
    date_values_7k = pd.date_range(start=start_date, end=end_date, freq='H')

    # find 5 percentile extreme scenarios
    df_5per = pd.DataFrame()
    df_95per = pd.DataFrame()
    num_largest = int((df.shape[0] - 2) * 0.05)

    for time in df.columns[2:]:
        df_5per[time] = df[time][2:].nlargest(num_largest).values
        df_95per[time] = df[time][2:].nsmallest(num_largest).values

    df_5per = df_5per.T
    df_5per.index = date_values_7k
    df_5per.name = 'date'
    df_5per.columns = np.arange(1, num_largest + 1)

    df_95per = df_95per.T
    df_95per.index = date_values_7k
    df_95per.name = 'date'
    df_95per.columns = np.arange(1, num_largest + 1)

    scen_summary = df.iloc[2:, 2:].describe()
    df_summary = pd.DataFrame({'date': date_values_7k,
                               'actual': df.loc[df['Type'] == 'Actual'].iloc[:,
                                         2:].values.flatten(),
                               'forecast': df.loc[
                                               df['Type'] == 'Forecast'].iloc[
                                           :, 2:].values.flatten(),
                               'scen_avg': scen_summary.loc['mean', :].values,
                               '5%': df.iloc[2:, 2:].quantile(0.05).values,
                               '95%': df.iloc[2:, 2:].quantile(0.95).values,
                               '25%': scen_summary.loc['25%', :].values,
                               '75%': scen_summary.loc['75%', :].values,
                               'max': scen_summary.loc['max', :].values,
                               'min': scen_summary.loc['min', :].values})

    # summary plot
    fig_summary = px.line(df_summary, x='date',
                          y=['scen_avg', 'actual', 'forecast'])

    fig_summary.data[1].line.color = actl_color

    fig_summary.data[2].line.color = fcst_color

    fig_summary.data[2].line.dash = 'dash'

    fig_summary.data[0].line.color = scen_color

    fig_summary.data[0].line.width = 2

    fig_summary.data[0].name = 'Scen Avg-{}'.format(version)

    fig_summary.data[1].name = 'Actual-{}'.format(version)

    fig_summary.data[2].name = 'Forecast-{}'.format(version)

    fig_summary.data[0].legendgroup = 'Scen Avg-{}'.format(version)

    fig_summary.data[1].legendgroup = 'Actual-{}'.format(version)

    fig_summary.data[2].legendgroup = 'Forecast-{}'.format(version)

    # add 5 percentile scenarios to plot
    fig_5per = px.line(df_5per, x=date_values_7k, y=df_5per.columns)
    fig_5per.update_traces(line_color=fper_color, line_width=2)
    fig_5per.for_each_trace(
        lambda t: t.update(name='Top 5 Percentile-{}'.format(version),
                           legendgroup='Top 5 Percentile-{}'.format(version)))

    fig_95per = px.line(df_95per, x=date_values_7k, y=df_95per.columns)
    fig_95per.update_traces(line_color=fper_color, line_width=2)
    fig_95per.for_each_trace(
        lambda t: t.update(name='Bottom 5 Percentile-{}'.format(version),
                           legendgroup='Bottom 5 Percentile-{}'.format(
                               version)))

    # fig_5per.data[0].name = 'top 5 percentile'
    for i in range(1, len(fig_5per.data)):
        fig_5per.data[i].showlegend = False

    for i in range(1, len(fig_95per.data)):
        fig_95per.data[i].showlegend = False

    # add percentiles to summary plot
    for i in range(len(fig_summary.data)):
        fig_5per.add_trace(fig_summary.data[i])

    for i in range(len(fig_95per.data)):
        fig_5per.add_trace(fig_95per.data[i])

    fig = fig_5per
    fig.update_layout(plot_bgcolor='#F9F9F9')

    date = datetime.strptime(day, "%Y%m%d").strftime("%b %d, %Y")
    fig.update_layout(
        title='Hourly Time Series for Asset {} on {} in Local Time Zone'.format(
            asset_id, date),
        yaxis_title='MWh',
        xaxis_title='Time',
        legend_title='',
        font_family='sans-serif', font_color=colors['text_1'],
        title_font_color=colors['plottitle'],
        legend=dict(x=1, y=1), legend_font_size=20, title_font_size=28,
        font_size=16,
        plot_bgcolor=colors['lightbackground'],
        paper_bgcolor=colors['background'])
    fig.update_xaxes(title_font_size=25, dtick=3600000, tickformat='%I%p',
                     title_font_color=colors['title'],
                     showgrid=True, gridwidth=1, gridcolor=colors['grid'],
                     zeroline=True, zerolinewidth=1,
                     zerolinecolor=colors['grid']
                     )
    fig.update_yaxes(title_font_size=25,
                     title_font_color=colors['title'],
                     showgrid=True, gridwidth=1, gridcolor=colors['grid'],
                     zeroline=True, zerolinewidth=1,
                     zerolinecolor=colors['grid'])

    return fig


@app.callback(
    Output('asset_ids_t7k', 'options'),
    Input('energy_types_t7k', 'value'))
def set_asset_ids_options(energy_type):
    return [{'label': i, 'value': i} for i in
            energy_types_asset_ids_t7k_csv[energy_type]]


@app.callback(
    Output('asset_ids_t7k', 'value'),
    Input('asset_ids_t7k', 'options'))
def set_asset_ids_value(energy_types_asset_ids_t7k_csv):
    return energy_types_asset_ids_t7k_csv[2]['value']


@app.callback(
    Output('asset_ids_rts', 'options'),
    Input('energy_types_rts', 'value'))
def set_asset_ids_options(energy_type):
    return [{'label': i, 'value': i} for i in
            energy_types_asset_ids_rts_csv[energy_type]]


@app.callback(
    Output('asset_ids_rts', 'value'),
    Input('asset_ids_rts', 'options'))
def set_asset_ids_value(energy_types_asset_ids_rts_csv):
    return energy_types_asset_ids_rts_csv[0]['value']

@app.callback(
    Output('t7k_scenario_plot_notuning', 'figure'),
    # Input('version_t7k', 'value'),
    Input('date_values_t7k', 'value'),
    Input('energy_types_t7k', 'value'),
    Input('asset_ids_t7k', 'value'))
def update_scenario_plot(day, asset_type, asset_id):
    return build_timeseries('t7k', day, asset_type, asset_id,
                            colors_scenario['actual_notuning'],
                            colors_scenario['forecast_tuning'],
                            colors_scenario['scen_notuning'],
                            colors_scenario['5per_notuning'])


@app.callback(
    Output('rts_scenario_plot_notuning', 'figure'),
    # Input('version_t7k', 'value'),
    Input('date_values_rts', 'value'),
    Input('energy_types_rts', 'value'),
    Input('asset_ids_rts', 'value'))
def update_scenario_plot_rts(day, asset_type, asset_id):
    return build_timeseries('rts', day, asset_type, asset_id,
                            colors_scenario['actual_notuning'],
                            colors_scenario['forecast_tuning'],
                            colors_scenario['scen_notuning'],
                            colors_scenario['5per_notuning'])