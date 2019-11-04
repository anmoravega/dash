import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objects as go
from datetime import datetime
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:Zpch9AQR6pPecJB7SYnctest@ds4acolombia.cl3uubspnmbm.us-east-2.rds.amazonaws.com/trades')
df = pd.read_sql("SELECT * from trades", engine.connect(), parse_dates=('OCCURRED_ON_DATE',))
df['YearMonth'] = df['Entry time'].dt.to_period('M')

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css', 'https://codepen.io/uditagarwal/pen/YzKbqyV.css'])

app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Bitcoin Leveraged Trading Backtest Analysis", className='h2-title'),
            ],
            className='study-browser-banner row'
    ),
    html.Div(
        className="row app-body",
        children=[
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        className="padding row",
                        children=[
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Exchange",),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['Exchange'].unique()
                                        ],
                                        value='Bitmex',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ]
                            ),
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Leverage"),
                                    dcc.RadioItems(
                                        id="leverage-select",
                                        options=[
                                            {'label': str(label), 'value': str(label)} for label in df['Margin'].unique()
                                        ],
                                        value='1',
                                        labelStyle={'display': 'inline-block'}
                                    ),
                                ]
                            ),
                            html.Div(
                                className="three columns card",
                                children=[
                                    html.H6("Select a Date Range"),
                                    dcc.DatePickerRange(
                                        id='date-range-select',
                                        min_date_allowed=df['Entry time'].min(),
                                        max_date_allowed=df['Entry time'].max(),
                                        start_date=df['Entry time'].min(),
                                        end_date=df['Entry time'].max(),
                                        display_format='MMM YY'
                                    ),
                                ]
                            ),
                            html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Strategy Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Strategy vs. Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                        ]
                )
        ]),
        html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure={
                        'data': []
                    }
                )
            ]
        ),
        html.Div(
                className="padding row",
                children=[
                    html.Div(
                        className="six columns card",
                        children=[
                            dash_table.DataTable(
                                id='table',
                                columns=[
                                    {'name': 'Number', 'id': 'Number'},
                                    {'name': 'Trade type', 'id': 'Trade type'},
                                    {'name': 'Exposure', 'id': 'Exposure'},
                                    {'name': 'Entry balance', 'id': 'Entry balance'},
                                    {'name': 'Exit balance', 'id': 'Exit balance'},
                                    {'name': 'Pnl (incl fees)', 'id': 'Pnl (incl fees)'},
                                ],
                                style_cell={'width': '50px'},
                                style_table={
                                    'maxHeight': '450px',
                                    'overflowY': 'scroll'
                                },
                            )
                        ]
                    ),
                    dcc.Graph(
                        id="pnl-types",
                        className="six columns card",
                        figure={}
                    )
                ]
            ),
            html.Div(
                className="padding row",
                children=[
                    dcc.Graph(
                        id="daily-btc",
                        className="six columns card",
                        figure={}
                    ),
                    dcc.Graph(
                        id="balance",
                        className="six columns card",
                        figure={}
                    )
                ]
            )
    ])        
])                            


def filter_df(df,exchange='Bitmex', margin=1, start=df['Entry time'].min(), end=df['Entry time'].max()):
    return(df[(df['Exchange']==exchange) & (df['Margin']==int(margin)) & (df['Entry time']>=start) & (df['Entry time']<=end)])

@app.callback(
        [dash.dependencies.Output('date-range-select','start_date'),
         dash.dependencies.Output('date-range-select','end_date')],
        [dash.dependencies.Input('exchange-select','value')])

def start_end_on_exchange(options):
    a = df[df['Exchange']==options]['Entry time']
    return(a.min(),a.max())

#@app.callback(
#        dash.dependencies.Output('monthly-chart','figure'),
#        [dash.dependencies.Input('exchange-select','value'),
#         dash.dependencies.Input('leverage-select','value'),
#         dash.dependencies.Input('date-range-select','start_date'),
#         dash.dependencies.Input('date-range-select','end_date')
#         ]
#        )
#
#
#def candle_plot(ex_value, le_value, start, end):
#    a = filter_df(df,ex_value, le_value, start, end)
#    trace = go.Candlestick(x= [datetime(a.year, a.month, a.day) for a in df.groupby(['YearMonth'])['YearMonth'].min().to_timestamp()],
#                           open = list((df.groupby(['YearMonth']).min())['Entry balance'].values),
#                           close = list((a.groupby(['YearMonth']).min())['Exit balance'].values),
#                           increasing={'line': {'color': '#00CC94'}},
#                           decreasing={'line': {'color': '#F50030'}})
#    return {'data': [trace],
#            'layout': go.Layout(title='Monthly returns')}


def calc_returns_over_month(dff):
    out = []

    for name, group in dff.groupby('YearMonth'):
        exit_balance = group.head(1)['Exit balance'].values[0]
        entry_balance = group.tail(1)['Entry balance'].values[0]
        monthly_return = (exit_balance*100 / entry_balance)-100
        out.append({
            'month': name.to_timestamp(),
            'entry': entry_balance,
            'exit': exit_balance,
            'monthly_return': monthly_return
        })
    return out


def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)['BTC Price'].values[0]
    btc_end_value = dff.head(1)['BTC Price'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(dff):
    start_value = dff.tail(1)['Exit balance'].values[0]
    end_value = dff.head(1)['Entry balance'].values[0]
    returns = (end_value * 100/ start_value)-100
    return returns

@app.callback(
    [
        dash.dependencies.Output('monthly-chart', 'figure'),
        dash.dependencies.Output('market-returns', 'children'),
        dash.dependencies.Output('strat-returns', 'children'),
        dash.dependencies.Output('strat-vs-market', 'children'),
    ],
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),

    )
)
def update_monthly(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(dff)
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns

    return ({
        'data': [
            go.Candlestick(
                open=[each['entry'] for each in data],
                close=[each['exit'] for each in data],
                x=[each['month'] for each in data],
                low=[each['entry'] for each in data],
                high=[each['exit'] for each in data]
            )
        ],
        'layout': {
            'title': 'Overview of Monthly performance'
        }
    }, f'{btc_returns:0.2f}%', f'{strat_returns:0.2f}%', f'{strat_vs_market:0.2f}%')

@app.callback(
    dash.dependencies.Output('table', 'data'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)

def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    dff['YearMonth'] = [a.to_timestamp() for a in dff['YearMonth']]
    return dff.to_dict('records')

@app.callback(dash.dependencies.Output('pnl-types','figure'),
              [dash.dependencies.Input('exchange-select','value'),
               dash.dependencies.Input('leverage-select','value'),
               dash.dependencies.Input('date-range-select','start_date'),
               dash.dependencies.Input('date-range-select','end_date')])

def bar_chart(ex, le, start, end):
    dff = filter_df(df, ex,le,start,end)
    dff['YearMonth'] = [a.to_timestamp() for a in dff['YearMonth']]
    short = dff[dff['Trade type']=='Short']
    long = dff[dff['Trade type']=='Long']
    dff.groupby(dff['Entry time'].dt.date).sum()
    return {'data': [go.Bar(x = short.groupby(short['Entry time'].dt.date).sum().index,
                            y = short.groupby(short['Entry time'].dt.date).sum()['Pnl (incl fees)'],
                            name = 'Short',
                            marker=go.bar.Marker(color='rgb(55, 83, 109)')),
                    go.Bar(x = long.groupby(long['Entry time'].dt.date).sum().index,
                           y = long.groupby(long['Entry time'].dt.date).sum()['Pnl (incl fees)'],
                           name = 'Long',
                           marker=go.bar.Marker(color = 'rgb(128,0,0)'))                    
                     ],
            'layout' : {'title' : 'PnL vs Trade type',
                        'width':'700',
                       'height':'500'}
            }

@app.callback(dash.dependencies.Output('daily-btc','figure'),
              [dash.dependencies.Input('exchange-select','value'),
               dash.dependencies.Input('leverage-select','value'),
               dash.dependencies.Input('date-range-select','start_date'),
               dash.dependencies.Input('date-range-select','end_date')])
    
def line_btc(ex, le, start, end):
    dff = filter_df(df, ex,le,start,end)
    dff['YearMonth'] = [a.to_timestamp() for a in dff['YearMonth']]
    agr = dff.groupby(dff['Entry time'].dt.date).mean()
    return{'data' : [go.Line(x = agr.index,
                             y = agr['BTC Price'])],
           'layout' : {'title':'Daily BTC Price',
                       'width':'700',
                       'height':'500'}
            }
    
@app.callback(dash.dependencies.Output('balance','figure'),
              [dash.dependencies.Input('exchange-select','value'),
               dash.dependencies.Input('leverage-select','value'),
               dash.dependencies.Input('date-range-select','start_date'),
               dash.dependencies.Input('date-range-select','end_date')])
    
def balance(ex, le, start, end):
    dff = filter_df(df, ex,le,start,end)
    dff['YearMonth'] = [a.to_timestamp() for a in dff['YearMonth']]
    agr = dff.groupby(dff['Entry time'].dt.date).mean()
    return{'data' : [go.Line(x = agr.index,
                             y = agr['Exit balance'] - agr['Profit'])],
           'layout' : {'title':'Balance over time',
                       'width':'700',
                       'height':'500'}
            }
    
if __name__ == "__main__":
    app.run_server(debug=True)

