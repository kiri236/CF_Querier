from io import BytesIO
import numpy as np
import requests
from PIL import Image,ImageDraw,ImageFont
from typing import Tuple,List,Union
import cv2
import re
from urllib.parse import urlparse
HEX = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'a': 10, 'b': 11, 'c': 12,
           'd': 13, 'e': 14, 'f': 15}
url_pattern = re.compile(r'^(https?://)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*/?$')
def is_valid_url(url:str)->bool:
    parsed = urlparse(url)
    return bool(parsed.scheme) and bool(parsed.netloc) and url_pattern.match(url)
def hex_to_RGB(s: str) -> List:
    s = s.lower()
    ans = []
    for i in range(1, len(s), 2):
        ans.append(HEX[s[i]] * 16 + HEX[s[i + 1]])
    return ans
def get_img(path:str)->Image.Image:
    if is_valid_url(path):
        data = requests.get(path)
        tmp = BytesIO(data.content)
        x = Image.open(tmp)
    else :
        x = Image.open(path)
    if path[-3:].lower() == 'png':
        x = x.convert('RGBA')
    return x
def scale_img(x:Image.Image,target:int=100)->Image.Image:
    x_resize = x.resize((target, int(x.size[1] * target / x.size[0])))
    return x_resize
def apply_mask(overlay_image:Image.Image,Type:str)->Image.Image:
    mask = Image.new('L', overlay_image.size, 0)  # 创建全黑遮罩
    draw = ImageDraw.Draw(mask)
    if Type == 'circle':
        draw.ellipse((0, 0, overlay_image.width, overlay_image.height), fill=255)
    elif Type == 'rect':
        draw.rectangle((0, 0, overlay_image.width, overlay_image.height), fill=255)
    else:
        raise TypeError("Type应为rect或circle")
    return mask
def brightness_enhance(img:Image.Image,factor:float=1.2)->Image.Image:
    r,g,b,a = img.split()
    r = r.point(lambda x: min(int(x * factor), 255))
    g = g.point(lambda x: min(int(x * factor), 255))
    b = b.point(lambda x: min(int(x * factor), 255))
    return Image.merge('RGBA',(r,g,b,a))
class MyDraw:
    def __init__(self,mode:str,width:int,height:int,color=Union[Tuple,str,None]):
        self.__img__ = Image.new(mode if mode else 'RGBA',(width,height),color)
        self.__draw__ = ImageDraw.Draw(self.__img__)
    def refresh(self):
        self.__draw__ = ImageDraw.Draw(self.__img__)
    def draw_round_rect(self,box: Union[Tuple, List],  r: int = 0,
                        fill: Union[Tuple, str, None] = 'red'):
        x0, y0, x1, y1 = box
        assert x1 >= x0, "x1 must be greater than x0"
        assert y1 >= y0, "y1 must be greater than y0"
        self.__draw__.ellipse((x0, y0, x0 + r, y0 + r), fill=fill)
        self.__draw__.ellipse((x1 - r, y0, x1, y0 + r), fill=fill)
        self.__draw__.ellipse((x0, y1 - r, x0 + r, y1), fill=fill)
        self.__draw__.ellipse((x1 - r, y1 - r, x1, y1), fill=fill)
        self.__draw__.rectangle((x0 + r / 2, y0, x1 - r / 2, y1), fill=fill)
        self.__draw__.rectangle((x0, y0 + r / 2, x1, y1 - r / 2), fill=fill)
        self.refresh()
    def add_drop_shadow(self,box: Union[List, Tuple],Type:str='rect', shadow_offsets: Tuple = (10, 10)
                        , shadow_blur: int = 10, shadow_color: Union[Tuple, str] = (0, 0, 0, 100)):
        shadow_layer = Image.new("RGBA", self.__img__.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        # 计算阴影位置
        dx, dy = shadow_offsets
        shadow_box = (
            box[0] + dx - shadow_blur,
            box[1] + dy - shadow_blur,
            box[2] + dx + shadow_blur,
            box[3] + dy + shadow_blur
        )
        if Type == 'rect':
            shadow_draw.rectangle(shadow_box, fill=shadow_color)
        elif Type == 'circle':
            shadow_draw.ellipse(shadow_box,fill=shadow_color)
        else:
            raise TypeError("Type应为rect或circle")
        cv_shadow = cv2.cvtColor(np.array(shadow_layer), cv2.COLOR_RGBA2BGRA)
        cv_shadow = cv2.GaussianBlur(cv_shadow, (0, 0), shadow_blur)
        blurred_shadow = Image.fromarray(cv2.cvtColor(cv_shadow, cv2.COLOR_BGRA2RGBA))

        # 合成阴影到原图（关键修正点）
        self.__img__ = Image.alpha_composite(self.__img__, blurred_shadow)
        self.refresh()
    def add_image(self,add_img:Image.Image,point:Tuple[int,int],masked:Union[str,None]=None):
        mask = None
        if masked == 'circle':
            mask = apply_mask(add_img,'circle')
        elif masked  == 'rect':
            mask = apply_mask(add_img,'rect')
        if add_img.mode == 'RGBA' and masked is None:
            self.__img__.paste(add_img,point,mask=add_img.split()[3])
        else:
            self.__img__.paste(add_img,point,mask=mask)
    def get_text_size(self,text:str,size:int,font:Union[str,None]=None)->Tuple[int,int]:
        if font:
            true_font = ImageFont.truetype(font,size)
        else:
            true_font = None
        bbox = self.__draw__.textbbox((0,0),text,font=true_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        self.refresh()
        return text_width,text_height
    def add_text(self,text:str,point:Tuple[float,float],font:Union[str,None]=None,size:int=10,fill:Union[Tuple, str]='white'):
        if font:
            true_font = ImageFont.truetype(font,size)
        else:
            true_font = None
        self.__draw__.text(point,text,fill=fill,font=true_font)
        self.refresh()
    def get_img(self)->Image.Image:
        return self.__img__
    def show(self,title:str=None):
        self.__img__.show(title)
