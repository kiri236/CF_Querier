import gradio as gr
from Backend import CFQuery
from typing import List,Dict
def get_ratings(username:str,l:int,r:int)->Dict:
    ratings = CFAPI.get_ratings(username)
    if r >= len(ratings) or l < 0 :
        raise Exception("查询长度超出限制")
    keys = list(ratings.keys())[l:r]
    return {k:ratings[k] for k in keys}
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
    demo.launch()
