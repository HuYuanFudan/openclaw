import os
import time
from .logger import logger
from .tokenizer import jieba_tokenize

pwd_path = os.path.abspath(os.path.dirname(__file__))
# 地址文件
place_path = os.path.join(pwd_path, 'data/china_place.txt')
# 地址补充文件，单字类
place_single_path = os.path.join(pwd_path, 'data/place_single.txt')
# 商标文件
brand_path = os.path.join(pwd_path, 'data/brand.txt')
# 行业文件
trade_path = os.path.join(pwd_path, 'data/trade.txt')
# 行业补充文件，单字类
trade_single_path = os.path.join(pwd_path, 'data/trade_single.txt')
# 后缀文件
suffix_path = os.path.join(pwd_path, 'data/suffix.txt')
# 后缀补充文件，单字类
suffix_single_path = os.path.join(pwd_path, 'data/suffix_single.txt')
# 词语分隔符，split word by comma
split_sep = ','


class Parser:
    def __init__(
            self,
            place_file=place_path,
            brand_file=brand_path,
            trade_file=trade_path,
            suffix_file=suffix_path,
            place_single_file=place_single_path,
            trade_single_file=trade_single_path,
            suffix_single_file=suffix_single_path,
            custom_name_split_file='',
    ):
        self.name = 'company_name_parser'
        self.place_file = place_file
        self.brand_file = brand_file
        self.trade_file = trade_file
        self.suffix_file = suffix_file
        self.place_single_file = place_single_file
        self.trade_single_file = trade_single_file
        self.suffix_single_file = suffix_single_file
        self.custom_name_split_file = custom_name_split_file
        self.places = None
        self.brands = None
        self.trades = None
        self.suffixes = None
        self.place_single = None
        self.trade_single = None
        self.suffix_single = None
        self.custom_name_split = None
        self.symbols = ['《', '》', '（', '）', '(', ')']
        self.inited = False
    def init(self):
        if not self.inited:
            s = time.time()
            self.places = self.load_dict(self.place_file)
            self.brands = self.load_dict(self.brand_file)
            self.trades = self.load_dict(self.trade_file)
            self.suffixes = self.load_dict(self.suffix_file)
            self.place_single = self.load_dict(self.place_single_file)
            self.trade_single = self.load_dict(self.trade_single_file)
            self.suffix_single = self.load_dict(self.suffix_single_file)
            self.custom_name_split = self.load_name_split(self.custom_name_split_file)
            self.inited = True
    def set_custom_split_file(self, file_path):
        self.custom_name_split_file = file_path
        self.custom_name_split = self.load_name_split(self.custom_name_split_file)
        logger.debug('set_custom_split_file done, custom_name_split size: {}'.format(len(self.custom_name_split)))

    @staticmethod
    def load_dict(file_path):
        res = dict()
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    terms = line.split()
                    if len(terms) == 2:
                        key = terms[0]
                        val = terms[1]
                    elif len(terms) == 1:
                        key = terms[0]
                        val = '1'
                    else:
                        continue
                    res[key] = val
        return res
    @staticmethod
    def load_name_split(file_path):
        res = dict()
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    terms = line.split(',')
                    if line.startswith('#') or len(terms) <= 1:
                        continue
                    name = terms[0]
                    place = terms[1] if len(terms) >= 2 else ''
                    brand = terms[2] if len(terms) >= 3 else ''
                    trade = terms[3] if len(terms) >= 4 else ''
                    suffix = terms[4] if len(terms) >= 5 else ''
                    symbol = terms[5] if len(terms) >= 6 else ''
                    res[name] = {'place': place,
                                 'brand': brand,
                                 'trade': trade,
                                 'suffix': suffix,
                                 'symbol': symbol}
        return res
    @staticmethod
    def findall(string, s):
        res = []
        index = 0
        while True:
            index = string.find(s, index)
            if index != -1:
                res.append(index)
                index += len(s)
            else:
                break
        return res

    @staticmethod
    def _extract_token(tokens, data_dict):
        res = []
        left_words = []
        for w, p, q in tokens:
            if w in data_dict:
                res.append((w, p, q))
            else:
                left_words.append((w, p, q))
        return res, left_words

    @staticmethod
    def link_near_words(tokens):
        new_tokens = []
        if not tokens:
            return new_tokens
        i = 0
        w, p, q = tokens[i]
        while i < len(tokens):
            i += 1
            if i == len(tokens):
                new_tokens.append((w, p, q))
            else:
                w_i, p_i, q_i = tokens[i]
                if p_i == q:
                    w = w + w_i
                    p = p
                    q = q_i
                else:
                    new_tokens.append((w, p, q))
                    w, p, q = tokens[i]
        return new_tokens
    def postprocess(self, left_words, places, brands, trades, suffixes):
        lefts = []
        for w, p, q in left_words:
            if len(w) == 1:
                if w in self.trade_single:
                    if len(left_words) == 2 and len(left_words[0][0]) == 1 and len(
                            left_words[1][0]) == 1 and not brands:
                        brands.append((w, p, q))
                    else:
                        trades.append((w, p, q))
                elif w in self.place_single:
                    places.append((w, p, q))
                elif w in self.suffix_single:
                    suffixes.append((w, p, q))
                else:
                    lefts.append((w, p, q))
            else:
                if w[-1] in self.place_single:
                    places.append((w, p, q))
                else:
                    brands.append((w, p, q))
        if len(lefts) == 1:
            if len(places) > 1 and places[0][2] == lefts[0][1] and places[1][1] == lefts[0][2]:
                places.extend(lefts)
            elif len(trades) > 1 and lefts[0][2] == trades[0][1] and not brands:
                brands.extend(lefts)
                brands.append(trades[0])
                trades.remove(trades[0])
            else:
                brands.extend(lefts)
        else:
            brands.extend(lefts)
        if len(places) > 1:
            places.sort(key=lambda k: k[1])
            places = self.link_near_words(places)  # Deal with link near words
        if len(brands) > 1:
            brands.sort(key=lambda k: k[1])
            brands = self.link_near_words(brands)
        return places, brands, trades, suffixes
    @staticmethod
    def _get_leave_tokens(tokens, start, end):
        res = []
        for w, p, q in tokens:
            if p < start:
                res.append((w, p, q))
            elif p >= end:
                res.append((w, p, q))
        return res
    def parse(self, name, pos_sensitive=False, enable_word_segment=False, **kwargs):
        name = name.strip()
        res = {'name': name, 'place': '', 'brand': '', 'trade': '', 'suffix': '', 'symbol': ''}
        # Not Chinese company name
        if (not name) or (not is_chinese(name[0])):
            return res
        self.init()
        places, brands, trades, suffixes, symbols = [], [], [], [], []
        tokens = jieba_tokenize(name)
        if self.custom_name_split:
            for k, v in self.custom_name_split.items():
                start = name.find(k)
                if start > -1:
                    end = start + len(k)
                    tokens = self._get_leave_tokens(tokens, start, end)
                    place_len = len(v['place'])
                    brand_len = len(v['brand'])
                    trade_len = len(v['trade'])
                    suffix_len = len(v['suffix'])
                    c_places = [(v['place'], start, start + place_len)] if place_len > 0 else []
                    c_brands = [(v['brand'], start + place_len, start + place_len + brand_len)] if brand_len > 0 else []
                    c_trades = [(v['trade'], start + place_len + brand_len,
                                 start + place_len + brand_len + trade_len)] if trade_len > 0 else []
                    c_suffixes = [(v['suffix'], start + place_len + brand_len + trade_len,
                                   start + place_len + brand_len + trade_len + suffix_len)] if suffix_len > 0 else []
                    places.extend(c_places)
                    brands.extend(c_brands)
                    trades.extend(c_trades)
                    suffixes.extend(c_suffixes)
                    break
        if tokens:
            t_symbols, left_words = self._extract_token(tokens, self.symbols)
            t_places, left_words = self._extract_token(left_words, self.places)
            t_suffixes, left_words = self._extract_token(left_words, self.suffixes)
            t_trades, left_words = self._extract_token(left_words, self.trades)
            t_brands, left_words = self._extract_token(left_words, self.brands)
            t_places, t_brands, t_trades, t_suffixes = self.postprocess(left_words, t_places, t_brands, t_trades,
                                                                        t_suffixes)
            places.extend(t_places)
            brands.extend(t_brands)
            trades.extend(t_trades)
            suffixes.extend(t_suffixes)
            symbols.extend(t_symbols)
        if len(places) > 1:
            places.sort(key=lambda k: k[1])
        if len(brands) > 1:
            brands.sort(key=lambda k: k[1])
        if len(trades) > 1:
            trades.sort(key=lambda k: k[1])
        if len(suffixes) > 1:
            suffixes.sort(key=lambda k: k[1])
        if not enable_word_segment:
            places = self.link_near_words(places)
            brands = self.link_near_words(brands)
            trades = self.link_near_words(trades)
            suffixes = self.link_near_words(suffixes)
        res['place'] = places if pos_sensitive else split_sep.join([w[0] for w in places])
        res['brand'] = brands if pos_sensitive else split_sep.join([w[0] for w in brands])
        res['trade'] = trades if pos_sensitive else split_sep.join([w[0] for w in trades])
        res['suffix'] = suffixes if pos_sensitive else split_sep.join([w[0] for w in suffixes])
        res['symbol'] = symbols if pos_sensitive else split_sep.join([w[0] for w in symbols])
        return res
def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    return '\u4e00' <= uchar <= '\u9fa5'
def is_number(uchar):
    """判断一个unicode是否是数字"""
    return '\u0030' <= uchar <= '\u0039'
def is_alphabet(uchar):
    """判断一个unicode是否是英文字母"""
    return '\u0041' <= uchar <= '\u005a' or '\u0061' <= uchar <= '\u007a'
def is_other(uchar):
    """判断是否非汉字，数字和英文字符"""
    return not (is_chinese(uchar) or is_number(uchar) or is_alphabet(uchar))
