"""
金融情感词典管理器
"""
import os
from typing import Dict, Set, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class LexiconWord:
    """词典词条"""
    word: str
    weight: float
    category: str  # positive, negative, degree, negation


class FinanceLexicon:
    """
    金融领域情感词典
    
    包含：
    - 积极词典
    - 消极词典
    - 程度词典
    - 否定词典
    """
    
    def __init__(self, lexicon_dir: Optional[str] = None):
        if lexicon_dir is None:
            lexicon_dir = os.path.join(os.path.dirname(__file__), '../../data/lexicon')
        
        self.lexicon_dir = lexicon_dir
        
        # 词典存储
        self.positive_words: Dict[str, float] = {}
        self.negative_words: Dict[str, float] = {}
        self.degree_words: Dict[str, float] = {}
        self.negation_words: Set[str] = set()
        
        # 加载词典
        self._load_lexicons()
    
    def _load_lexicons(self):
        """加载所有词典"""
        self._load_sentiment_dict(
            os.path.join(self.lexicon_dir, 'positive.txt'),
            self.positive_words
        )
        self._load_sentiment_dict(
            os.path.join(self.lexicon_dir, 'negative.txt'),
            self.negative_words
        )
        self._load_sentiment_dict(
            os.path.join(self.lexicon_dir, 'degree.txt'),
            self.degree_words
        )
        self._load_negation_dict(
            os.path.join(self.lexicon_dir, 'negation.txt')
        )
        
        logger.info(f"Loaded lexicons: {len(self.positive_words)} positive, "
                   f"{len(self.negative_words)} negative, "
                   f"{len(self.degree_words)} degree, "
                   f"{len(self.negation_words)} negation words")
    
    def _load_sentiment_dict(self, filepath: str, target_dict: Dict[str, float]):
        """加载情感词典"""
        if not os.path.exists(filepath):
            logger.warning(f"Lexicon file not found: {filepath}")
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        word = parts[0].strip()
                        try:
                            weight = float(parts[1].strip())
                        except ValueError:
                            weight = 1.0 if 'positive' in filepath else -1.0
                    else:
                        word = parts[0].strip()
                        weight = 1.0 if 'positive' in filepath else -1.0
                    
                    if word:
                        target_dict[word] = weight
                        
        except Exception as e:
            logger.error(f"Load lexicon error {filepath}: {e}")
    
    def _load_negation_dict(self, filepath: str):
        """加载否定词典"""
        if not os.path.exists(filepath):
            logger.warning(f"Negation file not found: {filepath}")
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    self.negation_words.add(line)
        except Exception as e:
            logger.error(f"Load negation dict error: {e}")
    
    def get_word_sentiment(self, word: str) -> Tuple[str, float]:
        """
        获取词语的情感极性和权重
        
        Returns:
            (category, weight): 类别和权重
            category: 'positive', 'negative', 'neutral'
        """
        if word in self.positive_words:
            return 'positive', self.positive_words[word]
        elif word in self.negative_words:
            return 'negative', self.negative_words[word]
        else:
            return 'neutral', 0.0
    
    def get_degree_weight(self, word: str) -> float:
        """获取程度词权重"""
        return self.degree_words.get(word, 1.0)
    
    def is_negation(self, word: str) -> bool:
        """判断是否为否定词"""
        return word in self.negation_words
    
    def analyze_text(self, words: List[str]) -> Dict:
        """
        基于词典分析文本情感
        
        Args:
            words: 分词后的词语列表
            
        Returns:
            {
                'score': 综合得分,
                'positive_count': 积极词数量,
                'negative_count': 消极词数量,
                'positive_words': 匹配的积极词,
                'negative_words': 匹配的消极词
            }
        """
        positive_count = 0
        negative_count = 0
        positive_matches = []
        negative_matches = []
        total_score = 0.0
        
        # 当前修饰状态
        current_degree = 1.0
        is_negated = False
        
        for i, word in enumerate(words):
            # 检查程度词
            if word in self.degree_words:
                current_degree = self.degree_words[word]
                continue
            
            # 检查否定词
            if word in self.negation_words:
                is_negated = not is_negated
                continue
            
            # 检查情感词
            if word in self.positive_words:
                weight = self.positive_words[word] * current_degree
                if is_negated:
                    weight = -weight
                    negative_count += 1
                    negative_matches.append(word)
                else:
                    positive_count += 1
                    positive_matches.append(word)
                total_score += weight
                
            elif word in self.negative_words:
                weight = self.negative_words[word] * current_degree
                if is_negated:
                    weight = -weight
                    positive_count += 1
                    positive_matches.append(word)
                else:
                    negative_count += 1
                    negative_matches.append(word)
                total_score += weight
            
            # 重置修饰状态
            current_degree = 1.0
            is_negated = False
        
        return {
            'score': total_score,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'positive_words': positive_matches,
            'negative_words': negative_matches
        }
    
    def add_word(self, word: str, category: str, weight: float):
        """
        添加新词到词典
        
        Args:
            word: 词语
            category: 类别 (positive/negative/degree/negation)
            weight: 权重
        """
        if category == 'positive':
            self.positive_words[word] = weight
        elif category == 'negative':
            self.negative_words[word] = weight
        elif category == 'degree':
            self.degree_words[word] = weight
        elif category == 'negation':
            self.negation_words.add(word)
    
    def remove_word(self, word: str, category: str):
        """从词典中删除词语"""
        if category == 'positive' and word in self.positive_words:
            del self.positive_words[word]
        elif category == 'negative' and word in self.negative_words:
            del self.negative_words[word]
        elif category == 'degree' and word in self.degree_words:
            del self.degree_words[word]
        elif category == 'negation' and word in self.negation_words:
            self.negation_words.remove(word)
    
    def save_lexicon(self, category: str):
        """保存词典到文件"""
        filename_map = {
            'positive': 'positive.txt',
            'negative': 'negative.txt',
            'degree': 'degree.txt',
            'negation': 'negation.txt'
        }
        
        if category not in filename_map:
            return
        
        filepath = os.path.join(self.lexicon_dir, filename_map[category])
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if category == 'negation':
                    for word in sorted(self.negation_words):
                        f.write(f"{word}\n")
                else:
                    words_dict = getattr(self, f"{category}_words")
                    for word, weight in sorted(words_dict.items()):
                        f.write(f"{word}\t{weight}\n")
            
            logger.info(f"Saved {category} lexicon to {filepath}")
        except Exception as e:
            logger.error(f"Save lexicon error: {e}")
    
    def get_statistics(self) -> Dict:
        """获取词典统计信息"""
        return {
            'positive_count': len(self.positive_words),
            'negative_count': len(self.negative_words),
            'degree_count': len(self.degree_words),
            'negation_count': len(self.negation_words),
            'total_count': (len(self.positive_words) + len(self.negative_words) + 
                          len(self.degree_words) + len(self.negation_words))
        }


# 全局词典实例
_lexicon: Optional[FinanceLexicon] = None


def get_lexicon() -> FinanceLexicon:
    """获取词典单例"""
    global _lexicon
    if _lexicon is None:
        _lexicon = FinanceLexicon()
    return _lexicon
