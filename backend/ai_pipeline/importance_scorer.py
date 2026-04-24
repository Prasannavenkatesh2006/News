import re
from datetime import datetime, timedelta
import numpy as np

class ImportanceScorer:
    
    # Category weights (higher = more important)
    CATEGORY_WEIGHTS = {
        'Politics': 0.95,
        'Economy': 0.90,
        'Natural Disasters': 1.0,
        'Health': 0.85,
        'Technology': 0.70,
        'Sports': 0.40,
        'Entertainment': 0.30,
        'Climate': 0.80,
    }
    
    # High-importance keywords
    CRITICAL_KEYWORDS = [
        'breaking', 'urgent', 'emergency', 'crisis', 'disaster',
        'earthquake', 'flood', 'fire', 'explosion', 'attack',
        'election', 'vote', 'parliament', 'supreme court',
        'pandemic', 'outbreak', 'vaccine', 'death toll',
        'stock market', 'crash', 'inflation', 'gdp', 'recession',
        'war', 'conflict', 'military', 'peace talks'
    ]
    
    # Trusted sources (higher credibility)
    TRUSTED_SOURCES = {
        'BBC News': 0.95,
        'Reuters': 0.95,
        'The Hindu': 0.90,
        'Times of India': 0.85,
        'NDTV': 0.85,
        'Al Jazeera': 0.85,
        'Wikipedia': 0.80,
        'Economic Times': 0.85,
    }
    
    def calculate_importance(self, article):
        """Calculate 0-100 importance score"""
        
        # Ensure 'metadata' exists
        meta = article.get('metadata', {})
        if meta is None:
            meta = {}
            
        published_at = article.get('published_at') or datetime.utcnow().isoformat()
        content = article.get('content', '') or ''
        title = article.get('title', '')
        source_name = article.get('source_name', article.get('source', ''))
        topic = article.get('topic', article.get('topic_hint', ''))
        sentiment_score = article.get('sentiment_score', 0)
        
        scores = {
            'recency': self._recency_score(published_at),
            'engagement': self._engagement_score(meta),
            'credibility': self._source_credibility(source_name),
            'entities': self._entity_relevance(title, content),
            'category': self._category_weight(topic),
            'sentiment': self._sentiment_intensity(sentiment_score),
            'keywords': self._keyword_matching(title, content)
        }
        
        # Weighted average
        importance = (
            0.25 * scores['recency'] +
            0.20 * scores['engagement'] +
            0.15 * scores['credibility'] +
            0.15 * scores['entities'] +
            0.10 * scores['category'] +
            0.10 * scores['sentiment'] +
            0.05 * scores['keywords']
        )
        
        return round(importance * 100), scores
    
    def _recency_score(self, published_at):
        """Score based on how recent (1.0 = just now, 0.0 = 7+ days)"""
        try:
            if not published_at:
                return 0.5
            # Handling Z offset issues
            pub_time = datetime.fromisoformat(str(published_at).replace('Z', '+00:00'))
            # Force naive to naive subtraction or aware to aware
            if pub_time.tzinfo is not None:
                # convert to naive utc
                pub_time = pub_time.astimezone(datetime.utcnow().astimezone().tzinfo).replace(tzinfo=None)
            
            age_hours = (datetime.utcnow() - pub_time).total_seconds() / 3600
            
            if age_hours < 1:
                return 1.0
            elif age_hours < 6:
                return 0.9
            elif age_hours < 24:
                return 0.7
            elif age_hours < 72:
                return 0.5
            else:
                return 0.2
        except Exception:
            return 0.5
    
    def _engagement_score(self, metadata):
        """Score based on upvotes, shares, comments"""
        upvotes = metadata.get('original_engagement', 0)
        if hasattr(metadata, 'get') is False:
            upvotes = 0
            
        try:
            upvotes = int(upvotes)
        except (ValueError, TypeError):
            upvotes = 0
            
        if upvotes > 10000:
            return 1.0
        elif upvotes > 1000:
            return 0.8
        elif upvotes > 100:
            return 0.6
        elif upvotes > 10:
            return 0.4
        else:
            return 0.2
    
    def _source_credibility(self, source_name):
        """Score based on source trustworthiness"""
        return self.TRUSTED_SOURCES.get(source_name, 0.5)
    
    def _entity_relevance(self, title, content):
        """Score based on important named entities"""
        text = f"{title} {content}".lower()
        
        # Government entities
        gov_entities = ['modi', 'parliament', 'supreme court', 'rbi', 'government']
        gov_score = sum(1 for e in gov_entities if e in text) * 0.2
        
        # Corporate entities
        corp_entities = ['google', 'microsoft', 'apple', 'amazon', 'tata', 'reliance']
        corp_score = sum(1 for e in corp_entities if e in text) * 0.1
        
        # International entities
        intl_entities = ['un', 'world bank', 'who', 'nato', 'china', 'usa', 'russia']
        intl_score = sum(1 for e in intl_entities if e in text) * 0.15
        
        return min(1.0, gov_score + corp_score + intl_score)
    
    def _category_weight(self, topic):
        """Score based on topic category"""
        return self.CATEGORY_WEIGHTS.get(topic, 0.5)
    
    def _sentiment_intensity(self, sentiment_score):
        """Extreme sentiment = higher importance"""
        try:
            abs_score = abs(float(sentiment_score))
        except (ValueError, TypeError):
            abs_score = 0
        
        if abs_score > 0.8:
            return 1.0
        elif abs_score > 0.6:
            return 0.7
        else:
            return 0.5
    
    def _keyword_matching(self, title, content):
        """Score based on critical keywords"""
        text = f"{title} {content}".lower()
        matches = sum(1 for keyword in self.CRITICAL_KEYWORDS if keyword in text)
        
        return min(1.0, matches * 0.2)
