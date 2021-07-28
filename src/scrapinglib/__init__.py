# -*- coding: utf-8 -*-
"""
    scrapinglib
    
"""
import json
import re

from . import avsox
from . import fanza
from . import fc2
from . import jav321
from . import javbus
from . import javdb
from . import mgstage
from . import xcity
# from . import javlib
from . import dlsite
from . import airav
from . import carib
from . import fc2club


def get_data_state(data: dict) -> bool:
    """ 元数据获取失败检测
    """
    if "title" not in data or "number" not in data:
        return False

    if data["title"] is None or data["title"] == "" or data["title"] == "null":
        return False

    if data["number"] is None or data["number"] == "" or data["number"] == "null":
        return False

    return True

def get_data_from_json(file_number, c_sources, c_location_rule, c_naming_rule, max_title_len):
    """
    iterate through all services and fetch the data 
    """

    func_mapping = {
        "airav": airav.main,
        "avsox": avsox.main,
        "fc2": fc2.main,
        "fanza": fanza.main,
        "javdb": javdb.main,
        "javbus": javbus.main,
        "mgstage": mgstage.main,
        "jav321": jav321.main,
        "xcity": xcity.main,
        # "javlib": javlib.main,
        "dlsite": dlsite.main,
        "carib": carib.main,
        "fc2club": fc2club.main
    }

    # default fetch order list, from the beginning to the end
    sources = c_sources.split(',')
    if not len(c_sources) > 60:
        # if the input file name matches certain rules,
        # move some web service to the beginning of the list
        lo_file_number = file_number.lower()
        if "carib" in sources and (re.match(r"^\d{6}-\d{3}", file_number)
        ):
            sources.insert(0, sources.pop(sources.index("carib")))
        elif "avsox" in sources and (re.match(r"^\d{5,}", file_number) or
                                     "heyzo" in lo_file_number
        ):
            sources.insert(0, sources.pop(sources.index("javdb")))
            sources.insert(1, sources.pop(sources.index("avsox")))
        elif "mgstage" in sources and (re.match(r"\d+\D+", file_number) or
                                       "siro" in lo_file_number
        ):
            sources.insert(0, sources.pop(sources.index("mgstage")))
        elif "fc2" in sources and ("fc2" in lo_file_number
        ):
            sources.insert(0, sources.pop(sources.index("javdb")))
            sources.insert(1, sources.pop(sources.index("fc2")))
            sources.insert(2, sources.pop(sources.index("fc2club")))
        elif "dlsite" in sources and (
                "rj" in lo_file_number or "vj" in lo_file_number
        ):
            sources.insert(0, sources.pop(sources.index("dlsite")))

    json_data = {}
    
    for source in sources:
        try:
            json_data = json.loads(func_mapping[source](file_number))
            # if any service return a valid return, break
            if get_data_state(json_data):
                break
        except:
            break

    # Return if data not found in all sources
    if not json_data:
        return

    # ================================================网站规则添加结束================================================

    title = json_data.get('title')
    actor_list = str(json_data.get('actor')).strip("[ ]").replace("'", '').split(',')  # 字符串转列表
    actor_list = [actor.strip() for actor in actor_list]  # 去除空白
    release = json_data.get('release')
    number = json_data.get('number')
    studio = json_data.get('studio')
    source = json_data.get('source')
    runtime = json_data.get('runtime')
    outline = json_data.get('outline')
    label = json_data.get('label')
    series = json_data.get('series')
    year = json_data.get('year')

    if json_data.get('cover_small'):
        cover_small = json_data.get('cover_small')
    else:
        cover_small = ''

    trailer = ''
    if json_data.get('extrafanart'):
        extrafanart = json_data.get('extrafanart')
    else:
        extrafanart = ''

    imagecut = json_data.get('imagecut')
    tag = str(json_data.get('tag')).strip("[ ]").replace("'", '').replace(" ", '').split(',')  # 字符串转列表 @
    actor = str(actor_list).strip("[ ]").replace("'", '').replace(" ", '')

    if title == '' or number == '':
        return

    # if imagecut == '3':
    #     DownloadFileWithFilename()

    # ====================处理异常字符====================== #\/:*?"<>|
    title = title.replace('\\', '')
    title = title.replace('/', '')
    title = title.replace(':', '')
    title = title.replace('*', '')
    title = title.replace('?', '')
    title = title.replace('"', '')
    title = title.replace('<', '')
    title = title.replace('>', '')
    title = title.replace('|', '')
    release = release.replace('/', '-')
    tmpArr = cover_small.split(',')
    if len(tmpArr) > 0:
        cover_small = tmpArr[0].strip('\"').strip('\'')

    # ====================处理异常字符 END================== #\/:*?"<>|

    # ===  替换Studio片假名
    studio = studio.replace('アイエナジー','Energy')
    studio = studio.replace('アイデアポケット','Idea Pocket')
    studio = studio.replace('アキノリ','AKNR')
    studio = studio.replace('アタッカーズ','Attackers')
    studio = re.sub('アパッチ.*','Apache',studio)
    studio = studio.replace('アマチュアインディーズ','SOD')
    studio = studio.replace('アリスJAPAN','Alice Japan')
    studio = studio.replace('オーロラプロジェクト・アネックス','Aurora Project Annex')
    studio = studio.replace('クリスタル映像','Crystal 映像')
    studio = studio.replace('グローリークエスト','Glory Quest')
    studio = studio.replace('ダスッ！','DAS！')
    studio = studio.replace('ディープス','DEEP’s')
    studio = studio.replace('ドグマ','Dogma')
    studio = studio.replace('プレステージ','PRESTIGE')
    studio = studio.replace('ムーディーズ','MOODYZ')
    studio = studio.replace('メディアステーション','宇宙企画')
    studio = studio.replace('ワンズファクトリー','WANZ FACTORY')
    studio = studio.replace('エスワン ナンバーワンスタイル','S1')
    studio = studio.replace('エスワンナンバーワンスタイル','S1')
    studio = studio.replace('SODクリエイト','SOD')
    studio = studio.replace('サディスティックヴィレッジ','SOD')
    studio = studio.replace('V＆Rプロダクツ','V＆R PRODUCE')
    studio = studio.replace('V＆RPRODUCE','V＆R PRODUCE')
    studio = studio.replace('レアルワークス','Real Works')
    studio = studio.replace('マックスエー','MAX-A')
    studio = studio.replace('ピーターズMAX','PETERS MAX')
    studio = studio.replace('プレミアム','PREMIUM')
    studio = studio.replace('ナチュラルハイ','NATURAL HIGH')
    studio = studio.replace('マキシング','MAXING')
    studio = studio.replace('エムズビデオグループ','M’s Video Group')
    studio = studio.replace('ミニマム','Minimum')
    studio = studio.replace('ワープエンタテインメント','WAAP Entertainment')
    studio = re.sub('.*/妄想族','妄想族',studio)
    studio = studio.replace('/',' ')
    # ===  替换Studio片假名 END

    location_rule = eval(c_location_rule)

    if 'actor' in c_location_rule and len(actor) > 100:
        location_rule = eval(c_location_rule.replace("actor", "'多人作品'"))
    maxlen = max_title_len
    if 'title' in c_location_rule and len(title) > maxlen:
        shorttitle = title[0:maxlen]
        location_rule = location_rule.replace(title, shorttitle)

    # 返回处理后的json_data
    json_data['title'] = title
    json_data['actor'] = actor
    json_data['release'] = release
    json_data['cover_small'] = cover_small
    json_data['tag'] = tag
    json_data['location_rule'] = location_rule
    json_data['year'] = year
    json_data['actor_list'] = actor_list

    json_data['trailer'] = ''
   
    if extrafanart:
        json_data['extrafanart'] = extrafanart
    else:
        json_data['extrafanart'] = ''

    naming_rule = ""
    for i in c_naming_rule.split("+"):
        if i not in json_data:
            naming_rule += i.strip("'").strip('"')
        else:
            naming_rule += json_data.get(i)
    json_data['naming_rule'] = naming_rule
    return json_data
