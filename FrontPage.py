import gradio as gr

import Image
from Backend import CFQuery
from typing import List,Dict,Union
import plotly.express as px
import pandas as pd
from Image import MyDraw, hex_to_RGB
import base64

def image_to_base64(img_path:str)->str:
    with open(img_path, "rb") as f:
        return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
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
    'newbie':{'min':0,'max':1199,'color':'#cccccc','short':'Newbie'},
    'pupil':{'min':1200,'max':1399,'color':'#77ff77','short':'Pupil'},
    'specialist':{'min':1400,'max':1599,'color':'#77ddbb','short':'Specialist'},
    'expert':{'min':1600,'max':1899,'color':'#aaaaff','short':'Expert'},
    'candidate master':{'min':1900,'max':2099,'color':'#ff88ff','short':'CM'},
    'master':{'min':2100,'max':2299,'color':'#ffcc88','short':'Master'},
    'international master':{'min':2300,'max':2399,'color':'#ffbb55','short':'IM'},
    'grandmaster':{'min':2400,'max':2599,'color':'#ff7777','short':'GM'},
    'international grandmaster':{'min':2600,'max':2999,'color':'#ff3333','short':'IGM'},
    'legendary grandmaster':{'min':3000,'max':3999,'color':'#aa0000','short':'LGM'},
    'tourist':{'min':4000,'max':6000,'color':'#aa0000','short':'Tourist'}
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
        counts, diffs = CFAPI.count_solved_problem_by_diff(user_name)
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
    head_bottom = 720
    head = (padding,head_top,width-padding,head_bottom)
    centerx = width/2
    colors = hex_to_RGB(COLORS[info.get('rank', 'newbie')]['color'])
    maxn = 0
    ans = 0
    for i,color in enumerate(colors):
        if color > maxn:
            maxn = color
            ans = i
    def get_color(x:int,y:int)->List:
        return [(min(color + x, 255) if color > 128 else max(color-x,0)) if i == ans else min(color + y, 255) for i, color in enumerate(colors)]
    draw = MyDraw('RGBA',width,height,color=(*get_color(60,25),255))
    try:
        draw.add_drop_shadow(head)
    except TypeError:
        print("指定类型错误")
    draw.draw_round_rect(head,25,fill=(*get_color(45,30),250))
    icon = Image.get_img(info['titlePhoto'])
    icon = Image.scale_img(icon,256)
    icon_pos = (int(centerx-icon.size[0]/2),int(head_top-icon.size[1]/2))
    try:
        draw.add_drop_shadow((icon_pos[0],icon_pos[1],icon_pos[0]+icon.size[0],icon_pos[1]+icon.size[1]),'circle',shadow_offsets=(5,5),shadow_blur=5)
    except TypeError:
        print("指定类型错误")
    draw.add_image(icon,icon_pos,'circle')
    text_size = 60
    font = "C:/WINDOWS/Fonts/arial.ttf"
    text_width,text_height = draw.get_text_size(user_name,text_size,font)
    draw.add_text(user_name,((width-text_width)//2,icon_pos[1]+icon.size[1]-30+text_height),font,text_size)
    left_width,left_height = (300,80)
    left_box = (padding+80,head_top+250,padding+80+left_width,head_top+250+left_height)
    dist = 450
    right_box = (left_box[0]+dist,left_box[1],left_box[2]+dist,left_box[3])
    try:
        draw.add_drop_shadow(left_box,shadow_offsets=(5,5),shadow_blur=5)
    except TypeError:
        print("指定类型错误")
    draw.draw_round_rect(left_box,15,fill=(*get_color(15,25),245))
    try:
        draw.add_drop_shadow(right_box,shadow_offsets=(5,5),shadow_blur=5)
    except TypeError:
        print("指定类型错误")
    draw.draw_round_rect(right_box, 15, fill=(*get_color(25, 25), 245))
    icon_size = 60
    rating_size = icon_size
    rating_icon = Image.get_img('resources/icons/图表.png')
    rating_icon = Image.scale_img(rating_icon,rating_size)
    draw.add_image(rating_icon,(left_box[0]+20,left_box[1]+(left_height-rating_icon.size[1])//2-4))
    max_rating_size = 25
    max_rating_width,max_rating_height = draw.get_text_size(f"MaxRating {info.get('maxRating',0)}",max_rating_size,font)
    draw.add_text(f"MaxRating {info.get('maxRating',0)}",(left_box[0]+(left_width-max_rating_width)//2+35,left_box[1]+(left_height-max_rating_height)//2-6),font,max_rating_size)
    star_size = icon_size
    star_icon = Image.get_img('resources/icons/star.png')
    star_icon = Image.scale_img(star_icon,star_size)
    star_icon = Image.brightness_enhance(star_icon,1.1)
    draw.add_image(star_icon,(right_box[0]+20,right_box[1]+(left_height-star_icon.size[1])//2-5))
    friends_size = 30
    friends_width,friends_height = draw.get_text_size(f"{str(info.get('friendOfCount',0))} {'stars' if info.get('friendOfCount',0)>1 else 'star'}",friends_size,font)
    draw.add_text(f"{str(info.get('friendOfCount',0))} {'stars' if info.get('friendOfCount',0)>1 else 'star'}",(right_box[0]+(left_width-friends_width)//2+35,right_box[1]+(left_height-friends_height)//2-6),font,friends_size)
    ver_dist = 80
    body_top = head_bottom+ver_dist
    body_height = 600
    body_bottom = body_top + body_height
    body = (padding,body_top,width-padding,body_bottom)
    try:
        draw.add_drop_shadow(body)
    except TypeError:
        print("指定类型错误")
    draw.draw_round_rect(body,25,fill=(*get_color(45,30),250))
    font_padding = 70
    level_size = 50
    level_ver_pos = 60
    content_ver_dist = 80
    content_size = 80
    level_width,_ = draw.get_text_size('Level',level_size,font)
    _,content_height = draw.get_text_size(COLORS[info.get('rank','newbie')]['short'],content_size,font)
    draw.add_text('Level',(body[0]+font_padding,body[1]+level_ver_pos),font,level_size)
    draw.add_text(COLORS[info.get('rank','newbie')]['short'], (body[0]+font_padding+level_width-60, body[1] + level_ver_pos + content_ver_dist), font, content_size)
    rate_size = 50
    rate_level_dist = 70
    rate_ver_pos = level_ver_pos + content_ver_dist + content_height + rate_level_dist
    rate_width,_ = draw.get_text_size('Rating',rate_size,font)
    num_ver_dist = content_ver_dist
    num_size = content_size+20
    draw.add_text('Rating',(body[0]+font_padding,body[1]+rate_ver_pos),font,rate_size)
    draw.add_text(str(info.get('rating',0)),(body[0]+font_padding+rate_width-70,body[1]+rate_ver_pos+num_ver_dist),font,num_size)
    solved_size = 40
    solved_ver_pos = level_ver_pos
    hor_dist = 400
    total_width = 400
    total_height = 10
    solved_800_dist = 20
    line_space = solved_800_dist
    right_x = body[0]+font_padding+hor_dist
    right_y = body[1]+solved_ver_pos
    _,solved_height = draw.get_text_size(f'solved {counts} problems',solved_size,font)
    draw.add_text(f'solved {counts} problems',(right_x,right_y),font,solved_size)
    right_y += solved_height+line_space
    for diff in diffs.items():
        rank,pbm = diff
        rank_size = 50
        _,rank_height = draw.get_text_size(f'{str(rank)} +',rank_size,font)
        draw.add_text(f'{str(rank)} +',(right_x,right_y),font,rank_size)
        right_margin = right_x + total_width
        ratio_size = rank_size
        try:
            ratio = pbm/counts
        except ZeroDivisionError:
            ratio = 0
        ratio_width,_ = draw.get_text_size(f'{ratio*100:.1f}%',ratio_size,font)
        draw.add_text(f'{ratio*100:.1f}%',(right_margin-ratio_width,right_y),font,ratio_size)
        line_space = 40
        right_y += rank_height+line_space
        draw.draw_rounded_line((right_x,right_y,right_x+total_width*ratio,right_y),total_height,fill='white')
        line_space = 20
        right_y += total_height+line_space
    forces_size = 30
    forces_width,_=draw.get_text_size('Forces',forces_size,font)
    now_x = width-forces_width-20
    draw.add_text('Forces',(now_x,10),font,forces_size,fill='DodgerBlue')
    code_size = forces_size
    code_width,_=draw.get_text_size('Code',code_size,font)
    now_x -= code_width
    draw.add_text('Code',(now_x,10),font,code_size)
    cf_icon = Image.get_img('resources/icons/icons8-codeforces-48.png')
    now_x -= cf_icon.size[0]+5
    draw.add_image(cf_icon,(now_x,0))
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
    logo_base64 = image_to_base64("resources/icons/icons8-codeforces-48.png")
    with gr.Blocks(theme=custom_theme,css="""
.title-container {
    padding: 20px 0;
    border-bottom: 2px;
    margin-bottom: 30px;
}
""") as demo:
        gr.HTML(f"""
            <div class="title-container">
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    margin-left: 20px;
                ">
                    <img src="{logo_base64}" 
                         style="width: 40px; height: 40px; object-fit: contain;">
                    <h1 style="margin: 0; font-family: 'Microsoft Yahei'; 
                               color: white;">Codeforces Querier</h1>
                </div>
            </div>
            """)
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
                gr.Examples(
                    examples=['jiangly',
                              'tourist',
                              'dfs',
                              'Benq',
                              'kotori'
                              ],
                    inputs=username
                )
    demo.launch(share=True)