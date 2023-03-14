import io
import bz2
import numpy as np
import pandas as pd
from datetime import date, timedelta, datetime
import dill as pickle
from dash import html, dcc, Input, Output, ctx
import plotly.express as px
from plotly.colors import n_colors
import plotly.graph_objects as go

import dash_bootstrap_components as dbc

from styles.styles import TITLE_STYLE, CONTENT_STYLE, MARKDOWN_STYLE_DOWNLOAD, DROPDOWN_STYLE, MARKDOWN_STYLE
from inputs.inputs import date_values_t7k, bus, branch
from markdown.lmps import markdown_text_lmps_overview, markdown_text_lmps_plot
from app import app, dbx

# geographical plot token
PLOT_TOKEN = 'pk.eyJ1IjoiZmFuZ2oxIiwiYSI6ImNsZDBoY2JseTAxaDUzb3NzMGx3NG5pNDAifQ' \
             '.3vAgWckVvvRuo5S6aeD_Mg'

html_div_lmps_overview =  html.Div(children=[

                html.H1(
                    children='Locational Marginal Prices',
                    style=TITLE_STYLE
                ),

                html.Div([
                    dcc.Markdown(
                        children= markdown_text_lmps_overview,
                        style = MARKDOWN_STYLE),
                ]),

                html.A(
                    "Link to our grid simulation Vatic github repo",
                    href='https://github.com/PrincetonUniversity/Vatic/tree/v0.4.0-a2',
                    target="_blank")
            ],
                style=CONTENT_STYLE)



html_div_lmps = html.Div(children=[
                  dbc.Row(
                      dbc.Col(html.H3(children='LMP Geographic Plots', style=TITLE_STYLE))
                      , justify='start', align='start'),

                    html.Div([
                        dcc.Markdown(
                            children=markdown_text_lmps_plot,
                            style=MARKDOWN_STYLE_DOWNLOAD),
                    ],
                        style={'padding': '20px'}),

                    html.Hr(),

                    dbc.Row(
                        dbc.Col([
                            html.Label('Select Day'),
                            dcc.Dropdown(date_values_t7k[:-2],
                                         id='date_values_t7k_lmps',
                                         value=date_values_t7k[0],
                                         style=DROPDOWN_STYLE),
                            html.Br()
                        ])
                    ),

                    dbc.Row(
                        dbc.Col([
                            html.Label('Select Hr'),
                            dcc.Dropdown(list(range(24)),
                                         id='hr_values_t7k_lmps',
                                         value=15,
                                         style=DROPDOWN_STYLE)
                        ])
                    ),

                    html.Br(),

                    dbc.Row([
                        dbc.Col(
                            dcc.Graph(
                                id='fig_lmp_geo',
                                style={'padding-left': '10px'}
                            ))
                    ]
                        , justify='start')

                ], style = CONTENT_STYLE)


def plot_particular_hour(hr, bus_detail, line_detail):
    # Manually Set up Discrete Color Scale
    bus_detail_hr = bus_detail[bus_detail['Hour'] == hr]
    line_detail_hr = line_detail[line_detail['Hour'] == hr]

    line_detail_hr['Flow'] = line_detail_hr['Flow'].apply(
        lambda x: round(x, 2))
    line_detail_hr['UID_Flow'] = line_detail_hr['UID'].astype(str) + ': ' + \
                                 line_detail_hr['Flow'].astype(str)

    bus_detail_hr['ABS LMP'] = bus_detail_hr['LMP'].apply(lambda x: abs(x))
    # The size would vary with LMP
    bus_detail_hr['size'] = bus_detail_hr['ABS LMP']

    size_max_ = bus_detail_hr['size'].max()
    # Emphasize the extreme case in the plot by increasing size where prices <= -1e4
    bus_detail_hr.loc[bus_detail_hr['LMP'] < 0, 'size'] = size_max_
    #     bus_detail_hr.loc[bus_detail_hr['LMP'] >= 1000, 'size'] = size_max_

    #     max_lmp_hr = bus_detail_hr['ABS LMP'].max()
    #     min_lmp_hr = bus_detail_hr['ABS LMP'].min()

    #     if (max_lmp_hr-min_lmp_hr) != 0:
    #          bus_detail_hr['size'] = 5+(bus_detail_hr['ABS LMP']-min_lmp_hr)/(max_lmp_hr-min_lmp_hr)
    #         print(bus_detail_hr['size'])
    #     else:
    #         print('LMP Prices are Same across all Busses')
    #         bus_detail_hr['size'] = 5

    bus_detail_mismatch = bus_detail_hr.loc[bus_detail_hr['Mismatch'] != 0]

    # separate high congest from low congest
    line_detail_hr_highcongest = line_detail_hr[
        line_detail_hr['CongestionRatio'] >= 0.98] \
        .reset_index().sort_values(by=['CongestionRatio'])

    bus_highcongest = set(line_detail_hr_highcongest['To Bus'].unique()).union(
        set(line_detail_hr_highcongest['From Bus'].unique()))
    bus_detail_hr_highcongest = bus_detail_hr[
        bus_detail_hr['Bus ID'].isin(bus_highcongest)]
    bus_detail_hr_lowcongest = bus_detail_hr[
        ~bus_detail_hr['Bus ID'].isin(bus_highcongest)]

    #     print('Maximum Congestion Ratio')
    #     print(line_detail_hr_highcongest['CongestionRatio'][0])
    # plot highcongest before lowcongest so we could hover to see highcongest info even if these buses are in the same location
    fig = px.scatter_mapbox(bus_detail_hr_lowcongest, lat="lat",
                                       lon="lng", color="LMP", opacity=0.7,
                                       size='size',
                                       hover_name='Bus Name',
                                       hover_data=['Bus ID', 'LMP',
                                                   'Demand',
                                                   'GEN UID'],
                                       color_continuous_scale=px.colors.sequential.Turbo,
                                       size_max=15, zoom=1)

    if bus_detail_hr_highcongest.shape[0] != 0:
        fig_highcongest = px.scatter_mapbox(bus_detail_hr_highcongest, lat="lat",
                                lon="lng",
                                color="LMP", opacity=0.7, size='size',
                                hover_name='Bus Name',
                                hover_data=['Bus ID', 'LMP', 'Demand',
                                            'GEN UID'],
                                color_continuous_scale=px.colors.sequential.Turbo,
                                size_max=15, zoom=1)

    fig.add_trace(fig_highcongest.data[0])

    if bus_detail_mismatch.shape[0] != 0:
        busids_mismatch = list(bus_detail_mismatch['Bus ID'].unique())
        line_detail_hr_mismatch = line_detail_hr[
            line_detail_hr['From Bus'].isin(busids_mismatch) |
            line_detail_hr['To Bus'].isin(busids_mismatch)]
        fig_mismatch = px.scatter_mapbox(bus_detail_mismatch, lat="lat",
                                         lon="lng", color="LMP", opacity=1.0,
                                         size='size',
                                         hover_name='Bus Name',
                                         hover_data=['Bus ID', 'LMP',
                                                     'Mismatch', 'Demand',
                                                     'GEN UID'],
                                         color_continuous_scale=px.colors.sequential.Turbo,
                                         size_max=15, zoom=1)
        fig.add_trace(fig_mismatch.data[0])

    fig.update_layout(
        hovermode='closest',
        mapbox=dict(
            accesstoken=PLOT_TOKEN,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=31,
                lon=-99.9018
            ),
            pitch=0,
            zoom=4.5,
     )
    )

    # need to consider direction:the bus line is starting point
    fig1 = go.Figure(fig)

    # plot high congestion bus so we could hover them even if they overlap with other buses in same location
    # Plot Transmission Lines Related to Mismatch Buses

    bluepurplered = n_colors('rgb(0, 0, 255)', 'rgb(255, 0, 0)',
                             line_detail_hr_highcongest.shape[0],
                             colortype='rgb')
    # Fix decimal point imprecision
    bluepurplered[0] = 'rgb(0, 0, 255)'
    bluepurplered[-1] = 'rgb(255, 0, 0)'

    # Plot line details
    if line_detail_hr_highcongest.shape[0] != 0:
        for idx, line_detail_hr_row in line_detail_hr_highcongest.iterrows():
            fromlmp = bus_detail_hr[
                bus_detail_hr['Bus ID'] == line_detail_hr_row['From Bus']][
                'LMP'].values[0]
            tolmp = \
                bus_detail_hr[
                    bus_detail_hr['Bus ID'] == line_detail_hr_row['To Bus']][
                    'LMP'].values[0]

            fig1.add_trace(go.Scattermapbox(
                mode="lines",
                lat=line_detail_hr_row[['From Bus Lat', 'To Bus Lat']].values,
                lon=line_detail_hr_row[['From Bus Lng', 'To Bus Lng']].values,
                hovertemplate=line_detail_hr_row[
                                  'UID_Flow'] + ' <br>From: ' + str(
                    line_detail_hr_row['From Bus']) +
                              '<br>To:' + str(line_detail_hr_row['To Bus']) +
                              '<extra>CongesRatio={CongesRatio:.2f}</extra>'.format(
                                  CongesRatio=line_detail_hr_row[
                                      'CongestionRatio']) +
                              '<extra><br>FromLMP={FromLMP:.2f}</extra>'.format(
                                  FromLMP=fromlmp) +
                              '<extra><br>ToLMP={ToLMP:.2f}</extra>'.format(
                                  ToLMP=tolmp),
                line=dict(
                    width=5 + line_detail_hr.iloc[0]['CongestionRatio'] * 10,
                    color=bluepurplered[-1]), opacity=1,
                name='Congested Lines', legendgroup='Congested Lines'
            ))

    fig1.update_layout(title='LMPs Distribution at Hr {}, {} under Texas 7k Grid'.format(hr,
                                                                     bus_detail_hr[
                                                                         'Date'].unique()[
                                                                         0]),
                       legend=dict(x=1, y=1),
                       coloraxis_colorbar=dict(orientation="h"),
                       height=600, width=1000)

    for i in range(line_detail_hr_highcongest.shape[0]):
        fig1.data[-(1 + i)].showlegend = False

    if bus_detail_hr_highcongest.shape[0] != 0:
        fig1.data[0].name = 'Buses with No Congested Lines Connected to'
        fig1.data[1].name = 'Buses with Congested Lines Connected to'
        fig1.data[0].showlegend = True
        fig1.data[1].showlegend = True
        if bus_detail_mismatch.shape[0] != 0:
            fig1.data[2].name = 'Buses with Mismatch in Demand and Supply'
            fig1.data[2].showlegend = True
    else:
        fig1.data[0].name = 'Buses'
        fig1.data[0].showlegend = True
        if bus_detail_mismatch.shape[0] != 0:
            fig1.data[1].name = 'Buses with Mismatch in Demand and Supply'
            fig1.data[1].showlegend = True
    fig1.data[-1].showlegend = True
    return fig1, line_detail_hr_highcongest

def build_lmp_plot_file(file_name, bus, branch):
    file_path = '/ORFEUS-Alice/data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20/{}'.format(file_name)
    _, res = dbx.files_download(file_path)

    with io.BytesIO(res.content) as stream:
        with bz2.BZ2File(stream, 'r') as f:
            df_pickle = pickle.load(f)

    bus_detail = df_pickle['bus_detail'].reset_index()
    line_detail = df_pickle['line_detail'].reset_index()

    line_detail = pd.merge(line_detail, branch[['UID', 'From Bus', 'To Bus',
                                                'From Name', 'To Name',
                                                'Cont Rating']],
                           left_on='Line', right_on='UID')
    line_detail['CongestionRatio'] = line_detail['Flow'].apply(
        lambda x: abs(x)) / line_detail['Cont Rating']

    bus_detail = pd.merge(bus_detail, bus[
        ['Bus ID', 'lat', 'lng', 'Zone', 'Sub Name', 'Bus Name', 'Area',
         'GEN UID']],
                          left_on='Bus', right_on='Bus Name')

    busid_lat = dict(zip(bus_detail['Bus ID'], bus_detail['lat']))
    busid_lng = dict(zip(bus_detail['Bus ID'], bus_detail['lng']))
    line_detail['To Bus Lat'] = line_detail['To Bus'].apply(
        lambda x: busid_lat[x])
    line_detail['To Bus Lng'] = line_detail['To Bus'].apply(
        lambda x: busid_lng[x])
    line_detail['From Bus Lat'] = line_detail['From Bus'].apply(
        lambda x: busid_lat[x])
    line_detail['From Bus Lng'] = line_detail['From Bus'].apply(
        lambda x: busid_lng[x])
    return bus_detail, line_detail

@app.callback(
    Output('fig_lmp_geo', 'figure'),
    Input('date_values_t7k_lmps', 'value'),
    Input('hr_values_t7k_lmps', 'value'))
def hourly_cost_dist_rts(date, hr):
    bus_detail, line_detail = build_lmp_plot_file(file_name=date + '.p.gz',
                                                  bus=bus, branch=branch)
    fig, _ = plot_particular_hour(hr, bus_detail, line_detail)
    return fig
