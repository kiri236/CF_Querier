import gradio as gr
from Backend import CFQuery
from typing import List,Dict
import plotly.express as px
import pandas as pd
def get_ratings(username:str,l:int,r:int)->Dict:
    ratings = CFQuery().get_ratings(username)
    if (r is not None and r >= len(ratings)) or l < 0 :
        raise Exception("查询长度超出限制")
    keys = list(ratings.keys())[l:r]
    return {k[:10]:ratings[k] for k in keys}

def generate_rating_data(user_name:str,l:int=0,r:int=None)->pd.DataFrame:
    info = get_ratings(user_name,l,r)
    dates = list(info.keys())
    ratings = [x['rating'] for x in info.values()]
    contests = [x['contest_Name'] for x in info.values()]
    deltas = [x['delta'] for x in info.values()]
    ranks = [x['rank'] for x in info.values()]

    return pd.DataFrame({
        "Date": dates,
        "Rating": ratings,
        "Contest": contests,
        "Delta": deltas,
        "Rank":ranks
    })
COLORS = {
    'Newbie':{'min':0,'max':1199,'color':'#cccccc'},
    'Pupil':{'min':1200,'max':1399,'color':'#77ff77'},
    'Specialist':{'min':1400,'max':1599,'color':'#77ddbb'},
    'Expert':{'min':1600,'max':1899,'color':'#aaaaff'},
    'Candidate Master':{'min':1900,'max':2099,'color':'#ff88ff'},
    'Master':{'min':2100,'max':2299,'color':'#ffcc88'},
    'International Master':{'min':2300,'max':2399,'color':'#ffbb55'},
    'Grandmaster':{'min':2400,'max':2599,'color':'#ff7777'},
    'International Grandmaster':{'min':2600,'max':2999,'color':'#ff3333'},
    'Legendary Grandmaster':{'min':3000,'max':5000,'color':'#aa0000'}
}
def plot_codeforces_rating(user_name:str):
    df = generate_rating_data(user_name)
    # colors = ["green" if delta >= 0 else "red" for delta in df["Delta"]]
    fig = px.line(
        df,
        x="Date",
        y='Rating',
        markers=True,
        title="Codeforces Rating History",
        labels={"Rating": "Rating", "Date": "Contest Date"},
        hover_data={"Contest": True, "Delta": True,"Rank":True}
    )
    fig.update_traces(
        line=dict(width=2),
        marker=dict(size=8),
        hovertemplate="<b>%{customdata[0]}</b><br>Date: %{x|%Y-%m-%d}<br>Rating: %{y}<br>Δ: %{customdata[1]}<br>Rank: %{customdata[2]}"
    )
    for level in COLORS.values():
        fig.add_shape(
            type="rect",
            xref="paper",
            yref="y",
            x0=0,
            x1=1,
            y0=level['min'],
            y1=level['max'],
            fillcolor=level['color'],
            opacity=0.2,
            layer="below",
            line_width=0
    )
    min_rating = df["Rating"].min()
    max_rating = df["Rating"].max()
    fig.update_layout(
            yaxis_range=[min_rating - 100, max_rating + 100],
            plot_bgcolor="rgba(0,0,0,0)"  # 透明背景
    )
    return fig
def toggle_components(user_name:str)->List:
    return [
        plot_codeforces_rating(user_name=user_name),
        gr.Plot(visible=True)
    ]
if __name__ == '__main__':
    CFAPI = CFQuery()
    with gr.Blocks() as demo:
        with gr.Tab("查询最近比赛"):
            query_btn = gr.Button("查询最近比赛")
            text_output = gr.Markdown()
            query_btn.click(
                fn=CFAPI.get_current_contest,
                outputs=text_output
            )
        with gr.Tab("查询用户信息"):
            username = gr.Textbox(label="请输入用户名",placeholder="待查询用户名")
            with gr.Row():
                user_btn = gr.Button("查询用户信息")
                rating_btn = gr.Button("查询用户rating")
            with gr.Column():
                plot = gr.Plot(visible=False)
                rating_btn.click(
                    fn = toggle_components,
                    inputs= username,
                    outputs=[plot,plot]
                )
    demo.launch()