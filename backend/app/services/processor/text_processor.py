"""
数据预处理模块
"""
import re
import hashlib
from typing import List, Optional, Set, Dict
from loguru import logger
import jieba
import jieba.analyse


class TextProcessor:
    """文本预处理器"""
    
    def __init__(self):
        # 停用词
        self.stopwords: Set[str] = set()
        self._load_stopwords()
        
        # 加载自定义词典
        self._load_custom_dict()
        
        # 编译正则表达式
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式"""
        # HTML标签
        self.html_pattern = re.compile(r'<[^>]+>')
        
        # URL
        self.url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+'
        )
        
        # 表情符号 [xxx]
        self.emoji_pattern = re.compile(r'\[[^\]]+\]')
        
        # @用户
        self.at_pattern = re.compile(r'@[\w\u4e00-\u9fa5]+')
        
        # #话题#
        self.topic_pattern = re.compile(r'#[^#]+#')
        
        # 特殊字符（保留中英文、数字、常用标点）
        self.special_char_pattern = re.compile(
            r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？、；：""''（）【】《》…—\-,\.!?;:\'"()\[\]]'
        )
        
        # 多余空白
        self.whitespace_pattern = re.compile(r'\s+')
        
        # 股票代码
        self.stock_code_pattern = re.compile(r'\$([A-Z]{2}\d{6})\$|\b(\d{6})\b')
        
        # 数字金额（保留有意义的数字）
        self.number_pattern = re.compile(r'\d+\.?\d*[万亿元%]+|\d{1,3}(,\d{3})*(\.\d+)?')
    
    def _load_stopwords(self):
        """加载停用词表"""
        # 基础停用词
        basic_stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '什么', '这个', '那个', '哪', '怎么', '为什么', '如何',
            '吗', '呢', '吧', '啊', '哦', '嗯', '哈', '呀', '么', '哪里', '怎样',
            '可以', '可能', '应该', '需要', '能够', '已经', '正在', '将要', '曾经',
            '或者', '而且', '但是', '因为', '所以', '如果', '虽然', '即使', '无论',
            '还是', '不过', '然后', '接着', '首先', '其次', '最后', '另外', '此外',
            '总之', '总的来说', '换句话说', '也就是说', '比如', '例如', '譬如'
        }
        self.stopwords.update(basic_stopwords)
        
        # 尝试加载停用词文件
        try:
            import os
            stopwords_file = os.path.join(
                os.path.dirname(__file__), 
                '../../data/lexicon/stopwords.txt'
            )
            if os.path.exists(stopwords_file):
                with open(stopwords_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip()
                        if word:
                            self.stopwords.add(word)
        except Exception as e:
            logger.debug(f"Load stopwords file error: {e}")
    
    def _load_custom_dict(self):
        """加载自定义词典"""
        # 金融领域词汇
        finance_words = [
            '涨停', '跌停', '涨停板', '跌停板', '牛市', '熊市', '震荡市',
            '利好', '利空', '重大利好', '重大利空',
            '主力', '庄家', '散户', '韭菜', '割韭菜',
            '建仓', '加仓', '减仓', '清仓', '满仓', '半仓', '轻仓', '重仓',
            '抄底', '逃顶', '追高', '杀跌', '补仓', '止损', '止盈',
            '放量', '缩量', '天量', '地量', '量能',
            '突破', '回调', '反弹', '回踩', '支撑', '压力', '阻力',
            '均线', '金叉', '死叉', 'MACD', 'KDJ', 'RSI', 'BOLL',
            '北向资金', '南向资金', '融资', '融券', '融资融券',
            '龙头股', '妖股', '概念股', '题材股', '蓝筹股', '白马股',
            '科创板', '创业板', '主板', '北交所', '新三板',
            '定增', '增发', '配股', '送股', '转股', '分红', '派息',
            '业绩预告', '业绩快报', '年报', '季报', '中报',
            '市盈率', '市净率', '市销率', 'PE', 'PB', 'PS', 'ROE',
            '大盘', '指数', '沪指', '深指', '创指', '上证指数', '深证成指',
            '开盘', '收盘', '高开', '低开', '高走', '低走', '冲高回落',
            '一字板', '炸板', '烂板', '换手', '换手率',
            'T+0', 'T+1', '做T', '打板', '排板', '封板',
            '游资', '机构', '基金', '私募', '公募', '险资', '社保',
            '解禁', '减持', '增持', '回购', '质押', '平仓'
        ]
        
        for word in finance_words:
            jieba.add_word(word)
        
        # 尝试加载自定义词典文件
        try:
            import os
            dict_file = os.path.join(
                os.path.dirname(__file__),
                '../../data/lexicon/finance_dict.txt'
            )
            if os.path.exists(dict_file):
                jieba.load_userdict(dict_file)
        except Exception as e:
            logger.debug(f"Load custom dict error: {e}")
    
    def clean_html(self, text: str) -> str:
        """清除HTML标签"""
        return self.html_pattern.sub('', text)
    
    def clean_url(self, text: str) -> str:
        """清除URL"""
        return self.url_pattern.sub('', text)
    
    def clean_emoji(self, text: str) -> str:
        """处理表情符号"""
        # 可以选择移除或转换
        return self.emoji_pattern.sub('', text)
    
    def clean_at(self, text: str) -> str:
        """清除@用户"""
        return self.at_pattern.sub('', text)
    
    def clean_topic(self, text: str) -> str:
        """清除#话题#"""
        return self.topic_pattern.sub('', text)
    
    def clean_special_chars(self, text: str) -> str:
        """清除特殊字符"""
        return self.special_char_pattern.sub(' ', text)
    
    def normalize_whitespace(self, text: str) -> str:
        """规范化空白字符"""
        return self.whitespace_pattern.sub(' ', text).strip()
    
    def clean(self, text: str) -> str:
        """
        文本清洗主函数
        
        处理流程：
        1. 清除HTML标签
        2. 清除URL
        3. 处理表情符号
        4. 清除@用户
        5. 清除话题标签
        6. 清除特殊字符
        7. 规范化空白
        """
        if not text:
            return ""
        
        text = self.clean_html(text)
        text = self.clean_url(text)
        text = self.clean_emoji(text)
        text = self.clean_at(text)
        text = self.clean_topic(text)
        text = self.clean_special_chars(text)
        text = self.normalize_whitespace(text)
        
        return text
    
    def tokenize(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """
        中文分词
        
        Args:
            text: 输入文本
            remove_stopwords: 是否移除停用词
            
        Returns:
            分词结果列表
        """
        if not text:
            return []
        
        # 使用jieba精确模式分词
        words = jieba.cut(text, cut_all=False)
        
        result = []
        for word in words:
            word = word.strip()
            if not word:
                continue
            if remove_stopwords and word in self.stopwords:
                continue
            if len(word) == 1 and not word.isalnum():
                continue
            result.append(word)
        
        return result
    
    def extract_keywords(self, text: str, topk: int = 10) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 输入文本
            topk: 返回前K个关键词
            
        Returns:
            关键词列表
        """
        if not text:
            return []
        
        # 使用TF-IDF提取关键词
        keywords = jieba.analyse.extract_tags(text, topK=topk)
        return keywords
    
    def extract_stock_codes(self, text: str) -> List[str]:
        """提取文本中的股票代码"""
        if not text:
            return []
        
        codes = set()
        matches = self.stock_code_pattern.findall(text)
        for match in matches:
            for code in match:
                if code and len(code) == 6 and code.isdigit():
                    codes.add(code)
        
        return list(codes)
    
    def compute_hash(self, text: str) -> str:
        """计算文本hash（用于去重）"""
        if not text:
            return ""
        
        # 清洗并分词后计算hash
        clean_text = self.clean(text)
        words = self.tokenize(clean_text, remove_stopwords=True)
        content = ''.join(sorted(words))
        
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def is_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """
        判断两个文本是否相似（用于去重）
        
        使用Jaccard相似度
        """
        words1 = set(self.tokenize(text1))
        words2 = set(self.tokenize(text2))
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold
    
    def process(self, text: str) -> Dict:
        """
        完整的文本预处理流程
        
        Returns:
            {
                'original': 原始文本,
                'cleaned': 清洗后文本,
                'tokens': 分词结果,
                'keywords': 关键词,
                'stock_codes': 股票代码,
                'hash': 文本hash
            }
        """
        cleaned = self.clean(text)
        tokens = self.tokenize(cleaned)
        keywords = self.extract_keywords(cleaned)
        stock_codes = self.extract_stock_codes(text)
        text_hash = self.compute_hash(text)
        
        return {
            'original': text,
            'cleaned': cleaned,
            'tokens': tokens,
            'keywords': keywords,
            'stock_codes': stock_codes,
            'hash': text_hash
        }


# 单例
_processor = None


def get_processor() -> TextProcessor:
    """获取文本处理器单例"""
    global _processor
    if _processor is None:
        _processor = TextProcessor()
    return _processor
