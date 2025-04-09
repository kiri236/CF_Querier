import requests
import datetime
from typing import Dict, List, Optional, Union
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
            response = self.session.get(f'{self.baseurl}{method}',params=params,timeout=(10,1000))
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
                        results.sort(key=lambda x: x['开始时间'])
                return results
        except TypeError as TE:
            raise TE
        except Exception as e:
            raise Exception(f'未知错误:{str(e)}') from e
    def get_current_contest(self)->str:
        contests = self._contests_
        if contests:
            res = '# 最近的比赛'
            res+= """
            """
            res +="""| 比赛名 | 开始时间 | 持续时间 | 赛制 | 比赛状态 |
            |---|---|---|---|---| """
            res += """
            """
            for contest in contests:
                for v in contest.values():
                    res += "| " + str(v) + " "
                res += """|
            """
            print(res)
            return res
        else:
            return '暂无进行中或即将开始的比赛'
    def contest_status(self,contest_id:int,handle:Optional[str]=None,
                       from_:Optional[int]=None,count:Optional[int]=None)->List[Dict]:
        """提交状态"""
        params = {'contestId':contest_id}
        if handle:
            params['handle'] = handle
        if from_:
            params['from'] = from_
        if count:
            params['count'] = count
        return self.make_request('contest.status',params)
    def contest_rating_changes(self,contest_id:int)->List[Dict]:
        """评分变化"""
        return self.make_request('contest.ratingChanges',{'contestId':contest_id})
    def user_info(self,handles:Union[str,List[str]])->List[Dict]:
        """用户信息"""
        if isinstance(handles,List):
            handles = ';'.join(handles)
        return self.make_request('user.info',{'handles':handles})
    def user_rating(self,handle:str)->List[Dict]:
        """用户rating"""
        return self.make_request('user.rating',{'handle':handle})
    def get_ratings(self,handle:str)->Dict:
        """用户rating变化"""
        rating = self.user_rating(handle)
        ratings = {self.format_time(entry['ratingUpdateTimeSeconds']):entry['newRating'] for entry in rating}
        return ratings
    def get_user_submission_in_contest(self,contest_id:int,user:str)->Union[List[Dict],str]:
        contest_status = self.contest_status(contest_id,handle=user)
        results = []
        for status in contest_status:
            submission_time = status['creationTimeSeconds']-status['author']['startTimeSeconds']
            submission_time_str = self.convert_time(submission_time)
            results.append(
                {
                    '提交时间':submission_time_str,
                    '题目':status['problem']['index']+'.'+status['problem']['name'],
                    '语言':status['programmingLanguage'],
                    '状态':'Accept' if status['verdict']=='OK' else status['verdict'],
                    '时间':str(status['timeConsumedMillis'])+'ms',
                    '空间占用':str(status['memoryConsumedBytes']//1000)+'KB'
                }
            )
        results.sort(key=lambda x:x['提交时间'])
        if results:
            return results
        else:
            return "找不到指定用户的提交信息"