import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_elo_trend(df):
    """
    Expects DataFrame with columns: date, elo, player_name (optional)
    """
    if df.empty:
        return go.Figure()
        
    fig = px.line(
        df, 
        x='date', 
        y='elo', 
        markers=True,
        title="ELO Trend over Time"
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="ELO")
    return fig

def plot_civ_win_rates(df):
    """
    Expects DataFrame with columns: civ_name, win_rate, total_games
    """
    if df.empty:
        return go.Figure()
        
    fig = px.bar(
        df,
        x='civ_name',
        y='win_rate',
        color='win_rate',
        hover_data=['total_games'],
        title="Win Rate by Civilization"
    )
    fig.update_layout(yaxis_range=[0, 100])
    return fig
