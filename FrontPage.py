import gradio as gr

import Image
from Backend import CFQuery
from typing import List,Dict,Union
import plotly.express as px
import pandas as pd
from Image import MyDraw, hex_to_RGB


def get_ratings(username:str,l:int,r:int)->Dict:
    try:
        ratings = CFAPI.get_ratings(username)
    except ConnectionError:
        raise ValueError("用户名不存在")
    except ValueError:
        raise ConnectionError("连接错误")
    if (r is not None and r >= len(ratings)) or l < 0 :
        raise Exception("查询长度超出限制")
    keys = list(ratings.keys())[l:r]
    return {k[:10]:ratings[k] for k in keys}

def generate_rating_data(user_name:str,l:int=0,r:int=None)->pd.DataFrame:
    try:
        info = get_ratings(user_name,l,r)
    except ValueError as VE :
        raise VE
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
    'newbie':{'min':0,'max':1199,'color':'#cccccc'},
    'pupil':{'min':1200,'max':1399,'color':'#77ff77'},
    'specialist':{'min':1400,'max':1599,'color':'#77ddbb'},
    'expert':{'min':1600,'max':1899,'color':'#aaaaff'},
    'candidate master':{'min':1900,'max':2099,'color':'#ff88ff'},
    'master':{'min':2100,'max':2299,'color':'#ffcc88'},
    'international master':{'min':2300,'max':2399,'color':'#ffbb55'},
    'grandmaster':{'min':2400,'max':2599,'color':'#ff7777'},
    'international grandmaster':{'min':2600,'max':2999,'color':'#ff3333'},
    'legendary grandmaster':{'min':3000,'max':5000,'color':'#aa0000'}
}
def plot_codeforces_rating(user_name:str):
    try:
        df = generate_rating_data(user_name)
    except ValueError as ve:
        return (
            gr.update(visible=False),
            gr.update(
                value='<p style="color: red; font-weight: bold;">❌ 用户不存在！</p>',
                visible=True
            ),
            gr.update(visible=False)
        )
    except ConnectionError as ce:
        return (
            gr.update(visible=False),
            gr.update(
                value='<p style="color: red; font-weight: bold;">❌ 网络连接错误！</p>',
                visible=True
            ),
            gr.update(visible=False)
        )
    except Exception as e:
        raise e
    fig = px.line(
        df,
        x="Date",
        y='Rating',
        markers=True,
        title=f"Codeforces Rating History({user_name})",
        labels={"Rating": "Rating", "Date": "Contest Date"},
        hover_data={"Contest": True, "Delta": True,"Rank":True},
    )
    fig.update_traces(
        line=dict(width=3, color='gold'),
        marker=dict(size=4.5, color='LightCoral'),
        hovertemplate="<b>%{customdata[0]}</b><br>Date: %{x|%Y-%m-%d}<br>Rating: %{y}<br>Δ: %{customdata[1]}<br>Rank: %{customdata[2]}",
        hoverlabel=dict(
            bgcolor="#E6F3FF",  # 背景颜色（浅蓝色）
            bordercolor="#1E90FF",  # 边框颜色（道奇蓝）
            font=dict(
                color="#2F4F4F",  # 字体颜色（深石板灰）
                size=12,  # 字体大小
                family="Arial"  # 字体类型
            )
        )
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
    return (
        gr.update(value=fig, visible=True),
        gr.update(visible=False),
        gr.update(visible=False)
    )
def show_user_info(user_name:str):
    try:
        info = CFAPI.user_info(user_name)[0]
    except ConnectionError:
        return (
            gr.update(visible=False),
            gr.update(
                value='<p style="color: red; font-weight: bold;">❌ 用户不存在！</p>',
                visible=True
            ),
            gr.update(visible=False)
        )
    except ValueError:
        return (
            gr.update(visible=False),
            gr.update(
                value='<p style="color: red; font-weight: bold;">❌ 网络连接错误！</p>',
                visible=True
            ),
            gr.update(visible=False)
        )
    except Exception as e:
        raise e
    width,height = (1020,1520)
    padding = 50
    head_top = 320
    head_bottom = 820
    head = (padding,head_top,width-padding,head_bottom)
    centerx = width/2
    draw = MyDraw('RGBA',width,height,color=(*hex_to_RGB(COLORS[info.get('rank','newbie')]['color']),205))
    try:
        draw.add_drop_shadow(head)
    except TypeError:
        print("指定类型错误")
    draw.draw_round_rect(head,10,fill=(*hex_to_RGB(COLORS[info.get('rank','newbie')]['color']),185))
    icon = Image.get_img(info['titlePhoto'])
    icon_pos = (int(centerx-icon.size[0]/2),int(head_top-icon.size[1]/2))
    try:
        draw.add_drop_shadow((icon_pos[0],icon_pos[1],icon_pos[0]+icon.size[0],icon_pos[1]+icon.size[1]),'circle',shadow_offsets=(5,5),shadow_blur=5)
    except TypeError:
        print("指定类型错误")
    draw.add_image(icon,icon_pos,'circle')
    text_size = 80
    font = "C:/WINDOWS/Fonts/arial.ttf"
    text_width,text_height = draw.get_text_size(user_name,text_size,font)
    draw.add_text(user_name,((width-text_width)//2,icon_pos[1]+icon.size[1]-50+text_height),font,text_size)
    ##TODO:添加maxRating和好友数
    return (
        gr.update(value=draw.get_img(), visible=True),
        gr.update(visible=False),
        gr.update(visible=False)
    )

if __name__ == '__main__':
    CFAPI = CFQuery()
    custom_theme = gr.themes.Default(  # 基于默认主题修改
        primary_hue="orange",  # 主色调
        secondary_hue="indigo",  # 辅助色
        neutral_hue='zinc',
        font=[gr.themes.GoogleFont("Noto Sans SC"), "sans-serif"]  # 中文字体
    ).set(
        # 大圆角按钮
        shadow_spread="6px",  # 阴影大小
        checkbox_label_text_color="*primary_800"  # 文字颜色
    )
    with gr.Blocks(theme=custom_theme) as demo:
        with gr.Tab("查询最近比赛"):
            query_btn = gr.Button("查询最近比赛")
            text_output = gr.Markdown()
            query_btn.click(
                fn=CFAPI.get_current_contest,
                outputs=text_output
            )
        with gr.Tab("查询用户信息"):
            username = gr.Textbox(label="请输入用户名",placeholder="待查询用户名,如tourist")
            with gr.Row():
                user_btn = gr.Button("查询用户信息")
                rating_btn = gr.Button("查询用户rating")
            with gr.Column():
                plot = gr.Plot(visible=False,label='用户Rating')
                error_output = gr.HTML(visible=False)
                img = gr.Image(label='用户信息',type='pil',visible=False)
                rating_btn.click(
                    fn = plot_codeforces_rating,
                    inputs= username,
                    outputs=[plot,error_output,img]
                )
                user_btn.click(
                    fn=show_user_info,
                    inputs=username,
                    outputs=[img, error_output,plot]
                )
    demo.launch()