from time import sleep

import requests
import datetime

from typing import Dict, List, Optional, Union
from requests import RequestException


class CFQuery:
    def __init__(self):
        self.baseurl = 'https://codeforces.com/api/'
        self.session = requests.Session()
    @staticmethod
    def format_time(timestamp:int)->str:
        """UNIX时间戳转换为一般时间"""
        return datetime.datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')
    @staticmethod
    def convert_time(Seconds:int)->str:
        """将秒数转换为小时+分钟+秒"""
        hours = Seconds//3600
        minutes = (Seconds%3600)//60
        seconds = Seconds%60
        minute_str = '0'+f'{minutes}' if minutes<10 else f'{minutes}'
        second_str = '0' + f'{seconds}' if seconds < 10 else f'{seconds}'
        return f'{hours}小时{minute_str}分钟{second_str}秒'
    def make_request(self,method:str,params:Optional[Dict]=None)->Union[Dict,List]:
        """请求"""
        try:
            response = self.session.get(f'{self.baseurl}{method}',params=params,timeout=10)
            response.raise_for_status()
            data = response.json()
            if data['status']!='OK':
                raise ValueError(f"API Error:{data.get('comment','Unknown Error')}")
            return data['result']
        except requests.exceptions.RequestException as reR:
            raise ConnectionError(f'请求失败:{str(reR)}') from reR
        except ValueError as VE:
            raise VE
        except Exception as e:
            raise RuntimeError(f"未知错误: {str(e)}") from e

    @property
    def _contests_(self,gym:bool = False)->List[Dict]:
        """获取比赛列表"""
        contests = self.make_request('contest.list',{'gym':str(gym).lower()})
        results = []
        try:
            if not isinstance(contests,List):
                raise TypeError(f'Type Error')
            else:
                for contest in contests:
                    phase = contest.get('phase','')
                    ##找未结束的比赛
                    if phase in ['BEFORE','CODING']:
                        ##处理开始时间戳
                        start_time_second = contest.get('startTimeSeconds', 0)
                        if start_time_second:
                            start_time_str = self.format_time(start_time_second)
                        else:
                            start_time_str = 'N/A'
                        ##处理持续时间
                        duration_time_str = self.convert_time(contest.get('durationSeconds', 0))
                        rest_time = start_time_second-int(datetime.datetime.utcnow().timestamp())
                        rest_time_str = self.convert_time(rest_time)
                        results.append(
                            {
                                '比赛':contest.get('name','未知比赛'),
                                '开始时间':start_time_str,
                                '持续时间':duration_time_str,
                                '赛制':contest.get('type','未知赛制'),
                                '比赛状态':'进行中' if phase == 'CODING' else f'距离比赛开始还有{rest_time_str}'
                            }
                        )
                return results
        except TypeError as TE:
            raise TE
        except Exception as e:
            raise Exception(f'未知错误:{str(e)}') from e
    def get_current_contest(self)->str:
        contests = self._contests_
        if contests:
            res = ''
            for contest in contests:
                tmp = ''
                for k,v in contest.items():
                    tmp+=k
                    tmp+=':'
                    if not isinstance(v,str):
                        tmp+=str(v)
                    else:
                        tmp+=v
                    tmp+=' '
                res+=tmp
                res+='\n'
            return res
        else:
            return '暂无进行中或即将开始的比赛'

x = CFQuery()
print(x.get_current_contest())
