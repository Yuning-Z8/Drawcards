#5.2.21
import random as r
import json
import os
import hashlib
from functools import wraps
from typing import Type, TypeVar, Any, Optional, Union

ERROR = '\033[91m错误：'
WARN = '\033[93m警告：'
END = '\033[0m'

def error(a: str):
    print(f"{ERROR}{a}{END}")

def warn(a: str):
    print(f"{WARN}{a}{END}")

# 辅助函数

def probability_fix(probability: list):
    """修正概率并计算累积概率"""
    if sum(probability) > 1:
        error('概率总和超过1')
        return
    return [sum(probability[:i+1]) for i in range(len(probability))] + [1]

tips = [
    "输入help查看完整指令列表",
    "清除数据不会重置系统配置",
    "使用exit退出",
    "个数|占比|与理论差值",
    "使用' '分割参数",
    "指令不区分大，小写"
]

def tip():
    """随机返回一个提示"""
    return r.choice(tips)

class zint(int):
    def __new__(cls, value):
        if isinstance(value, str):
            try:
                num = int(value)
                return super().__new__(cls, abs(num))
            except ValueError:
                raise ValueError(f"无效的非负整数输入: '{value}'")
        elif isinstance(value, int):
            return super().__new__(cls, abs(value))
        else:
            raise ValueError
class zfloat(float):
    def __new__(cls, value):
        if isinstance(value, str):
            try:
                num = float(value)
                return super().__new__(cls, abs(num))
            except ValueError:
                raise ValueError(f"invalid literal for zfloat(): '{value}'")
        elif isinstance(value, float):
            return super().__new__(cls, abs(value))
        else:
            raise ValueError
class boolyn(int):
    def __new__(cls, value):
        if isinstance(value, str):
            value = value.lower()
            if value == 'y':
                return super().__new__(cls, 1)
            elif value == 'n':
                return super().__new__(cls, 0)
        raise ValueError
class bool01(int):
    def __new__(cls, value):
        if isinstance(value, str):
            if value == '1':
                return super().__new__(cls, 1)
            elif value == '0':
                return super().__new__(cls, 0)
        elif isinstance(value, int):
            if value in [0, 1]:
                return super().__new__(cls, value)
        raise ValueError
T = TypeVar('T')
def need(var: Any, type_: Type[T]) -> Optional[T]:
    """
    类型检查和转换函数
    
    参数:
        var: 需要检查或转换的变量
        type_: 目标类型
        
    返回:
        转换后的对象（如果成功），否则返回 None
    """
    if type_ != type(var):
        try:
            return type_(var) # type: ignore
        except (ValueError, TypeError) as e:
            error(f"参数 {var!r} 不符合要求，应为 {type_.__name__} 类型: {e}")
            return
    return var

def save_data():
    """保存所有数据到文件"""
    with open('cards.json', 'w', encoding='utf-8') as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_data():
    """从文件加载数据"""
    global cards, users
    with open('cards.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)
    with open('users.json', 'r', encoding='utf-8') as f:
        users = json.load(f)

def login_required(func):
    """装饰器：检查用户是否登录"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user is None:
            error("需要先登录")
            return
        return func(*args, **kwargs)
    return wrapper

def hash_password(password: str, salt: str | None = None):
    """哈希密码，如果提供salt则使用，否则生成新的"""
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    return salt, hashed

# 用户数据
current_user = None
cards = {}
users = {}
nres = True
respos = 0

card_ = '默认'
card = {
    'op': [],
    'name': ['A', 'B', 'C', 'D'],
    'probability': [0.001, 0.02, 0.25],
    'baodi': [1250, 75, 0, 0],
    'len': 4
}

result: dict = {
    'card': card_,
    'op': [],
    'use_times': [0] * card['len'],
    'result': [0] * card['len'],
    'baodi': [0] * card['len'],
    'times': 0
}

opt_print_result = False
#opt_baodi = True
opt_show_res = True
opt_round_extent = 2
#

probability_fixed = probability_fix(card['probability'])
times_once = None

#.
def hand_result(result_: dict | None = None):
    """显示当前抽卡结果"""
    if result_ is None:
        result_ = result
    for i in range(0, len(result_['result'])):
        actual = (result_['result'][i] - result_['baodi'][i]) / (result_['times'] - sum(result_['baodi'])) if (result_['times'] - sum(result_['baodi'])) > 0 else 0
        theory = card['probability'][i] if i < len(card['probability']) else (1 - sum(card['probability']))
        print(f'{i + 1}.{card["name"][i]}:{result_["result"][i]}({result_["baodi"][i]}[{result_["use_times"][i]}])  |{actual * 100:.{opt_round_extent}f}%|{(actual - theory) * 100:.{opt_round_extent}f}%')
    print('提示:', tip())

@login_required
def save(val = None):
    '''保存结果'''
    global result, users, card, nres
    print('保存中...')
    if not nres:
        users[current_user]['results'].pop()
    users[current_user]['results'].append(result)
    nres = False
    users[current_user]['option'] = [opt_print_result, opt_show_res, opt_round_extent, times_once]
    cards[card_] = card
    print('保存完成')

def makesure(val: list, lenth: int = 1, limed: bool = True):
    if limed:
        if len(val) < lenth:
            return
        elif len(val) != lenth:
            warn(f'你使用了额外的参数，但命令只需要 {lenth} 个，前 {lenth} 个参数将被自动采用')
    else:
        vali = val.copy()
        val = []
        while len(vali) >= lenth:
            val.append(vali[:lenth])
            if len(vali) == lenth:
                vali = []
            else:
                vali = vali[lenth:]
        if not val:
            return
        if vali:
            warn(f'输入应该是每组 {lenth} 个参数，但你提供了额外的 {len(vali)} 个参数，它们将被自动舍弃')
    return val

#show
def show_res(val: list[str | int] | None = None):
    """显示当前结果"""
    if val is not None:
        try:
            if not current_user:
                error('你还没有登录')
                return
            if makesure(val) is None:
                error('你应该输入有效的序号')
                return
            index = need(val[0], int)
            if index is None:
                return
            result_ = users[current_user]['results'][index]
        except IndexError:
            error("索引超出范围")
            return
    else:
        result_ = result
    print(f'共计:{result_["times"]}')
    hand_result(result_)

def show_option(val = None):
    """显示当前选项"""
    print(f"实时显示: {'开启' if opt_print_result else '关闭'}")
    print(f"显示结果: {'开启' if opt_show_res else '关闭'}")
    print(f"小数位数: {opt_round_extent}")
    print(f"抽卡次数: {times_once if times_once is not None else '未设置'}")

def show_card(val: list[str] | None = None):
    """显示卡片信息"""
    if val is None:
        card_i = card_
        cardi = card
    else:
        if makesure(val) is None:
            error('你应该输入卡组名')
            return
        card_i = val[0]
        if card_i not in cards:
            error(f"卡片 {card_i} 不存在")
            return
        cardi = cards[card_i]
    print(f"{card_i}(共{cardi['len']}张):")
    print(f"可操作用户: {', '.join(cardi['op'])}")
    for i in range(cardi['len']):
        print(f"{cardi['name'][i]}: 概率={cardi['probability'][i] if i < len(cardi['probability']) else 1 - sum(cardi['probability'])}, 保底次数={cardi['baodi'][i]}")
def new_res(val = None):
    '''保存旧的结果（如果登录），生成新的结果'''
    global result, nres
    if current_user:
        save()
    print('清除完成')
    result = {
        'card': card_,
        'use_times': [0] * card['len'],
        'result': [0] * card['len'],
        'baodi': [0] * card['len'],
        'times': 0
    }
    nres = True

@login_required
def look_res(val: list[str | zint] | None = None):
    if val is None:
        pos = -1
    else:
        if makesure(val) is None:
            error('你应该输入序号')
            return
        pos = need(val[0], zint)
        if pos is None:
            return
        pos = -pos
    try:
        for i in range(pos,0):
            show_res([i])
    except IndexError:
            error("索引超出范围")
            return

@login_required
def look_card(val: list[str | int] | None = None):
    if val is None:
        pos = -1
    else:
        if makesure(val) is None:
            error('你应该输入序号')
            return
        pos = need(val[0], zint)
        if pos is None:
            return
        else:
            pos = -pos
    try:
        for i in list(cards)[pos:]:
            show_card([i])
    except IndexError:
            error("索引超出范围")
            return

def look_user(val: list[str | int] | None = None):
    if val is None:
        pos = -1
    else:
        if makesure(val) is None:
            error('你应该输入序号')
            return
        pos = need(val[0], zint)
        if pos is None:
            return
        else:
            pos = -pos
    try:
        for i in list(users)[pos:]:
            print(i)
    except IndexError:
            error("索引超出范围")
            return

def use_card(val:list[str] = ['默认']):
    global card, card_
    save()
    if makesure(val) is None:
        error('你应该输入卡组名')
        return
    try:
        card_ = need(val[0], str)
        card = cards[card_]
    except KeyError:
        error(f"卡组 {card_} 不存在")
        return
    new_res()

@login_required
def new_card(val:list[str] | None = None):
    global card, card_
    if val is None:
        error('你应该输入卡组名和卡片数量')
        return
    if makesure(val, 2) is None:
        error('输入格式错误，你应该输入 [名称] [数量]')
        return
    lenth = need(val[1], zint)
    card_i = need(val[0], str)
    if lenth is None or card_i is None:
        error('你应该输入有效的名称和数量')
        return
    if card_i in cards:
        error('该卡组已存在')
        return
    card_ = card_i
    cards[card_] = {
    "op":[current_user],
    "name": [],
    "probability": [],
    "baodi": [],
    "len": 0
    }
    card = cards[card_]
    change_long([lenth])
    card = cards[card_]
    new_res()
@login_required
def read_res(val: list[str | int] = [-1]):
    global result, nres
    if makesure(val) is None:
        error('你应该输入序号')
        return
    pos = need(val[0], int)
    if pos is None:
        return
    try:
        result = users[current_user]['results'][pos]
        nres = False
    except IndexError:
        error('没有该历史记录')
        return

def sign_in(val: list[str] | None = None):
    """用户登录/注册"""
    global current_user, nres
    if val is None:
        error('你应该输入用户名和密码')
        return
    if makesure(val, 2) is None:
        if makesure(val) is None:
            error("你应该使用 signIn/si [用户名] [密码] 进行登录或注册")
            return
        else:
            val.append(input('输入密码 \033[8m'))
            intype = 0
    else:
        intype = 1
    username = need(val[0], str)
    password = need(val[1], str)
    if username is None or password is None:
        error('你应该输入有效的用户名和密码')
        return
    if username == 'later':
        error('非法名称')
        return
    if intype:
        print(f"\033[F\033[2K\r> si {username} {'*' * len(password)}", end="\n")
    else:
        print('\033[0m', end = '', flush = True)
    if username in users:
        # 登录
        salt, stored_hash = users[username]["password"]
        _, input_hash = hash_password(password, salt)
        if input_hash == stored_hash:
            current_user = username
            print(f"欢迎回来, {username}!")
            nres = True
            # 加载用户设置
            global opt_print_result, opt_show_res, opt_round_extent, times_once
            user_opts = users[username]["option"]
            opt_print_result = user_opts[0]
            opt_show_res = user_opts[1]
            opt_round_extent = user_opts[2]
            times_once = user_opts[3]
            use_last_res = need(input('是否使用上次的结果[y/n] '), boolyn)
            if use_last_res is None:
                error("输入无效，请输入 'y' 或 'n'")
                return
            if use_last_res:
                read_res()
            else:
                new_res()
        else:
            print("密码错误")

    else:
        # 注册
        if input('确认密码 \033[8m') != password:
            print('\033[0m密码错误')
            return
        salt, hashed = hash_password(password)
        users[username] = {
            "password": [salt, hashed],
            "option": [opt_print_result, opt_show_res, opt_round_extent, times_once],
            "last card": "默认",
            "results": []
        }
        nres = True
        current_user = username
        print(f"\033[0m注册成功, 欢迎{username}!")

@login_required
def sign_out(val = None):
    """用户登出"""
    global current_user
    save()
    print(f"再见, {current_user}!")
    current_user = None
    new_res()

#main
def set_times(val: list[str] | None = None):
    """设置抽卡次数"""
    global times_once
    if val is None:
        error('你应该输入抽卡次数')
        return
    if makesure(val) is None:
        error('你应该输入抽卡次数')
        return
    times_once_ = need(val[0], zint)
    if times_once_ is None:
        error('你应该输入有效的抽卡次数')
        return
    if times_once_ > 300000:
        error('抽卡次数太大，请使用小于300000的次数')
        return
    times_once = times_once_
    print(f"已设置抽卡次数: {times_once}")

def drawcards(val: list[str] | None = None):
    """执行抽卡"""
    global result
    if val is None:
        if times_once is None:
            error("请先设置抽卡次数")
            return
        times = times_once
    else:
        if makesure(val) is None:
            error('你应该输入抽卡次数')
            return
        times = need(val[0], zint)
        if times is None:
            error('你应该输入有效的抽卡次数')
            return
    if times > 300000:
        error('抽卡次数太大，请使用小于300000的次数')
        return
    while times != 0:
        g = r.random()
        for i in range(card['len']):
            choudao = False
            if g <= probability_fixed[i]: # type: ignore
                choudao = True
            elif card['baodi'][i] != 0 and result['use_times'][i] >= card['baodi'][i]:
                result['baodi'][i] += 1
                choudao = True
            if choudao:
                result['use_times'][i] = 0
                if opt_print_result:
                    print(card['name'][i])
                result['result'][i] += 1
                break
            else:
                result['use_times'][i] += 1
        times -= 1
        result['times'] += 1
    if opt_show_res:
        hand_result()

def help_(val = None):
    """显示帮助信息"""
    print(f"""\033[1m 命令格式说明 \033[0m
  [参数]   *可省略   ...可重复多组

\033[1m 主命令\033[0m
  help/?                     显示帮助
  exit                       退出程序（自动保存）
  set/s [次数:1-300000]      设置默认抽卡次数
  drawcards/d [次数]*        执行抽卡（默认使用set提供的值）
  clean/c                    清除当前抽卡数据

\033[1m 数据命令\033[0m
  handresult/hr [序号:-N~N]* 显示抽卡结果
  handcard/hc [卡组名]*      查看卡组详情
  handoption/ho              显示当前用户设置
  save/sv                    立即保存数据
  userresult/ur [序号]*      查看历史记录
  useruseresult/uur [序号]   载入历史结果继续抽卡
  usernewresult/unr          创建空白抽卡记录

\033[1m 用户设置\033[0m
  signin/si [账号] [密码]    登录/注册
  signout/so                 退出当前账号
  userr/u [序号]*            查看用户列表
  ifprint/ip/p [0/1]         开关实时显示
  ifshowresult/ir [0/1]      开关结果统计显示
  setround/sr [位数:1-10]    设置小数位数

\033[1m 卡组设置（需创建者权限）\033[0m
  usercard/uc [序号]*            查看可用卡组
  userusecard/uuc [卡组名]       切换卡组
  usernewcard/unc [名称] [数量]      创建卡组
  setprobability/sp [位置] [概率:0~1]...   设置概率
  setname/sn [位置] [名称]...    设置名称
  setlength/sl [数量]            设置卡片数量
  setbaodi/sb [位置] [保底次数]...   设置保底""")

#setting
def wprint(val: list[str] | None = None):
    """设置是否实时显示抽卡结果"""
    global opt_print_result
    if val is None:
        error('你应该输入 0 或 1')
        return
    if makesure(val) is None:
        error('你应该输入 0 或 1')
        return
    i = need(val[0], bool01)
    if i is None:
        error('你应该输入 0 或 1')
        return
    opt_print_result = i
    print(f'实时显示: {"开启" if opt_print_result else "关闭"}')

def whres(val: list[str] | None = None):
    """设置是否显示抽卡结果"""
    global opt_show_res
    if val is None:
        error('你应该输入 0 或 1')
        return
    if makesure(val) is None:
        error('你应该输入 0 或 1')
        return
    i = need(val[0], bool01)
    if i is None:
        error('你应该输入 0 或 1')
        return
    opt_show_res = i
    print(f'显示结果: {"开启" if opt_show_res else "关闭"}')

@login_required
def change_baodi(vali: list[str] | None = None):
    """修改保底设置"""
    global card
    if current_user not in card['op']:
        error('你没有操作权限')
        return
    if vali is None:
        error('你应该输入位置和保底次数')
        return
    valj = makesure(vali, 2, False)
    if valj is None:
        error('输入格式错误，你应该输入 [位置] [保底次数]')
        return
    val: list[list[str]] = valj
    for i in val:
        pos = need(i[0], zint) 
        baodi = need(i[1], zint)
        if pos is  None or baodi is None:
            warn(f'{i[0]},{i[1]} 输入无效，自动跳过')
            continue
        pos -= 1
        if 0 <= pos < card['len']:
            card['baodi'][pos] = baodi
            print(f"{card['name'][pos]} 的保底已更新为 {baodi}")
        else:
            error(f"位置{pos + 1}超出范围(1-{card['len']})，自动跳过")

@login_required
def change_probability(vali: list[str] | None = None):
    """修改概率设置"""
    global card, probability_fixed
    if current_user not in card['op']:
        error('你没有操作权限')
        return
    if vali is None:
        error('你应该输入位置和概率')
        return
    valj = makesure(vali, 2, False)
    if valj is None:
        error('输入格式错误，你应该输入 [位置] [概率:0~1]')
        return
    val: list[list[str]] = valj
    temp_prob = card['probability'].copy()
    for i in val:
        pos = need(i[0], zint) 
        prob = need(i[1], zfloat)
        if pos is  None or prob is None:
            warn(f'{i[0]},{i[1]} 输入无效，自动跳过')
            continue
        pos -= 1
        if 0 <= pos < card['len']:
            temp_prob[pos] = prob
        else:
            error(f"位置{pos + 1}超出范围(1-{card['len']})，自动跳过")
    temp_prob_fixed = probability_fix(temp_prob)
    if temp_prob_fixed is not None:
        card['probability'] = temp_prob
        probability_fixed = temp_prob_fixed
    else:
        error('非法概率')

@login_required
def change_name(vali: list[str] | None = None):
    """修改名称设置"""
    global card
    if current_user not in card['op']:
        error('你没有操作权限')
        return
    if vali is None:
        error('你应该输入位置和名称')
        return
    valj = makesure(vali, 2, False)
    if valj is None:
        error('输入格式错误，你应该输入 [位置] [名称]')
        return
    val: list[list[str]] = valj
    for i in val:
        pos = need(i[0], zint) 
        nname = need(i[1], str)
        if pos is  None or nname is None:
            warn(f'{i[0]},{i[1]} 输入无效，自动跳过')
            continue
        pos -= 1
        if 0 <= pos < card['len']:
            card['name'][pos] = nname
            print(f"{card['name'][pos]} 已更新为 {nname}")
        else:
            error(f"位置{pos + 1}超出范围(1-{card['len']})，自动跳过")

def change_round(val: list[str] | None = None):
    """修改小数位数"""
    global opt_round_extent
    if val is None:
        error('你应该输入小数位数')
        return
    if makesure(val) is None:
        error('你应该输入小数位数')
        return
    i = need(val[0], zint)
    if i is None:
        error('你应该输入有效的小数位数')
        return
    opt_round_extent = i
    print(f"已设置小数位数为 {opt_round_extent}")

@login_required
def change_long(val: list[str | zint] | None = None):
    """修改卡片数量"""
    global result, card, probability_fixed
    if current_user not in card['op']:
        error('你没有操作权限')
        return 
    if val is None:
        error('你应该输入卡片数量')
        return
    if makesure(val) is None:
        error('你应该输入卡片数量')
        return
    nlen = need(val[0], zint)
    if nlen is None:
        error('你应该输入有效的卡片数量')
        return
    try:
        if nlen > card['len']:
            cpv = []
            result['use_times'] += [0] * (nlen - card['len'])
            result['result'] += [0] * (nlen - card['len'])
            result['baodi'] += [0] * (nlen - card['len'])
            card['baodi'] += [0] * (nlen - card['len'])
            card['name'] += [''] * (nlen - card['len'])
            card['probability'] += [0] * (nlen - card['len'] - 1)
            nproba = 0
            ctn = True
            for i in range(card['len'], nlen):
                while True:
                    nname = need(input(f'设置第{i + 1}项的名称:'), str)
                    if i + 1 == nlen:
                        print(f'第{nlen}项的概率:{1 - nproba}')
                        nprob = 0
                    else:
                        nprob = need(input(f'设置第{i + 1}项的概率:'), zfloat)
                    nbaodi = need(input(f'设置第{i + 1}项的保底（0为无）:'), zint)
                    if nname is None or nprob is None or nbaodi is None:
                        warn('你应该输入要求的内容')
                        ctn = boolyn(input('是否继续输入[y/n] '))
                        if ctn is None:
                            warn('你应该输入y或n,使用默认值y')
                            ctn = True
                        if not ctn:
                            break
                    else:
                        nprob = round(nprob, 15)
                        break
                if not ctn:
                    break
                nproba += nprob # type: ignore
                card['baodi'][i] = nbaodi
                card['name'][i] = nname
                if nprob != 0:
                    cpv.extend([i + 1, nprob])
            card['len'] = nlen
            change_probability(cpv)
        else:
            del card['name'][nlen:]
            del result['use_times'][nlen:]
            del result['result'][nlen:]
            del result['baodi'][nlen:]
            del card['probability'][nlen - 1:]
            probability_fixed = probability_fix(card['probability'])
            del card['baodi'][nlen:]
            card['len'] = nlen
    except (IndexError, ValueError) as e:
        error(f"卡片数量参数无效:{e}")

command_map = {}

def register_command(commands: list[str], func):
    global command_map
    for cmd in commands:
        command_map[cmd.lower()] = func

def execute_command(parts: list[str]):
    global command_map
    command = parts[0].lower()
    if len(parts) > 2:
        val = parts[1:]
    elif len(parts) > 1:
        val = [parts[1]]
    else:
        val = None
    if command in command_map:
        if val != None:
            command_map[command](val)
        else:
            command_map[command]()
    else:
        print(f"未知命令{command}：使用help/?获取帮助")

if True:
    register_command(['set', 's'], set_times)
    register_command(['drawcards','d'], drawcards)
    register_command(['help','?','？'],help_)
    register_command(['clean','c'],new_res)
    register_command(['ifPrint', 'ip', 'p'], wprint)
    register_command(['ifShowResult', 'ir'], whres)
    register_command(['setProbability', 'sprob', 'sp'], change_probability)
    register_command(['setName', 'sname', 'sn'], change_name)
    register_command(['setRound', 'sr'], change_round)
    register_command(['setBaodi', 'sb'], change_baodi)
    register_command(['setLength', 'slen', 'sl'], change_long)
    register_command(['handResult', 'hr'], show_res)
    register_command(['handCard', 'hc'], show_card)
    register_command(['handOption', 'ho'], show_option)
    register_command(['signin', 'si'], sign_in)
    register_command(['signout', 'so'], sign_out)
    register_command(['save', 'sv'], save)
    register_command(['userR', 'u'], look_user)
    register_command(['userResult', 'ur'], look_res)
    register_command(['userCard', 'uc'], look_card)
    register_command(['userUseCard', 'uuc'], use_card)
    register_command(['userUseResult', 'uur'], read_res)
    register_command(['userNewResult', 'unr'], new_res)
    register_command(['userNewCard', 'unc'], new_card)

if __name__ == "__main__":
    load_data()
    if users['later'] in users:
        a =input(f'\033[0m上次登录 {users["later"]} [y/n]')
        if need(a, boolyn) is not None and boolyn(a):
            sign_in([users['later']])
    while True:
        user_input = input("> ").split(' ')
        if user_input[0].lower() == "exit":
            if current_user:
                save()
                users['later'] = current_user
            save_data()
            print("退出中...")
            break
        execute_command(user_input)
