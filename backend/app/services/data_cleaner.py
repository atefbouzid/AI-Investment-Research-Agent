"""
Data Cleaning Pipeline for Investment Analysis
Transforms raw data from 4 sources into clean, LLM-ready features
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class InvestmentDataCleaner:
    """
    Professional data cleaner for investment analysis.
    
    Transforms raw data from data collector into clean, structured features
    optimized for LLM analysis and report generation.
    
    Input: Raw data from StockDataCollector.collect_complete_dataset()
    Output: Clean, structured data ready for LLM analysis
    """
    
    def __init__(self):
        """Initialize the data cleaner."""
        self.cleaning_log = []
        self.feature_weights = {
            'financial_health': 0.3,
            'market_sentiment': 0.25,
            'peer_performance': 0.25,
            'market_position': 0.2
        }
    
    def process_complete_dataset(self, raw_dataset: Dict) -> Dict:
        """
        Main pipeline: Process complete raw dataset into clean features.
        
        Args:
            raw_dataset: Output from StockDataCollector.collect_complete_dataset()
            
        Returns:
            Dict: Clean, structured dataset ready for LLM analysis
        """
        self.cleaning_log = []
        
        print(f"\n🧹 STARTING DATA CLEANING PIPELINE")
        print("="*60)
        
        ticker = raw_dataset.get('ticker', 'UNKNOWN')
        sources = raw_dataset.get('data_sources', {})
        
        # Clean each data source
        clean_basic = self._clean_basic_info(sources.get('basic_info'), ticker)
        clean_financial = self._clean_financial_data(sources.get('financial_data'), ticker)
        clean_news = self._clean_news_data(sources.get('news_data'), ticker)
        clean_peers = self._clean_peer_data(sources.get('peer_comparison'), ticker)
        
        # Create comprehensive analysis features
        analysis_features = self._create_analysis_features(
            clean_basic, clean_financial, clean_news, clean_peers
        )
        
        # Generate investment scores
        investment_scores = self._calculate_investment_scores(
            clean_basic, clean_financial, clean_news, clean_peers
        )
        
        # Create final clean dataset
        clean_dataset = {
            'ticker': ticker,
            'company_name': clean_basic.get('company_name', 'Unknown'),
            'processing_timestamp': datetime.now().isoformat(),
            
            # Clean data by source
            'company_overview': clean_basic,
            'financial_metrics': clean_financial,
            'market_sentiment': clean_news,
            'competitive_position': clean_peers,
            
            # Analysis-ready features
            'investment_analysis': analysis_features,
            'investment_scores': investment_scores,
            
            # LLM optimization
            'llm_context': self._create_llm_context(
                clean_basic, clean_financial, clean_news, clean_peers, analysis_features
            ),
            
            # Quality metadata
            'data_quality': self._assess_data_quality(
                clean_basic, clean_financial, clean_news, clean_peers
            ),
            'cleaning_log': self.cleaning_log,
            'ready_for_llm': True
        }
        
        # Show cleaning summary
        self._show_cleaning_summary(clean_dataset)
        
        return clean_dataset
    
    def _clean_basic_info(self, raw_basic: Optional[Dict], ticker: str) -> Dict:
        """Clean and structure basic company information."""
        if not raw_basic:
            self.cleaning_log.append(f"No basic info available for {ticker}")
            return self._get_empty_basic()
        
        print(f"INFO: Cleaning basic company info...")
        
        clean_basic = {
            'ticker': ticker,
            'company_name': self._clean_text(raw_basic.get('company_name', 'Unknown')),
            'sector': self._standardize_sector(raw_basic.get('sector')),
            'industry': self._clean_text(raw_basic.get('industry', 'Unknown')),
            'country': raw_basic.get('country', 'Unknown'),
            
            # Financial metrics (standardized)
            'current_price': self._safe_float(raw_basic.get('current_price')),
            'market_cap': self._safe_float(raw_basic.get('market_cap')),
            'market_cap_billions': self._convert_to_billions(raw_basic.get('market_cap')),
            'market_cap_category': self._categorize_market_cap(raw_basic.get('market_cap')),
            
            # Valuation metrics
            'pe_ratio': self._safe_float(raw_basic.get('pe_ratio')),
            'pe_category': self._categorize_pe_ratio(raw_basic.get('pe_ratio')),
            
            # Company details
            'employee_count': self._safe_int(raw_basic.get('employee_count')),
            'business_description': self._clean_description(raw_basic.get('long_business_summary')),
            'website': raw_basic.get('company_website', 'N/A')
        }
        
        self.cleaning_log.append(f"INFO: Basic info cleaned: {clean_basic['company_name']} ({clean_basic['sector']})")
        return clean_basic
    
    def _clean_financial_data(self, raw_financial: Optional[Dict], ticker: str) -> Dict:
        """Clean and enhance financial performance data."""
        if not raw_financial:
            self.cleaning_log.append(f"No financial data available for {ticker}")
            return self._get_empty_financial()
        
        print(f"INFO: Cleaning financial data...")
        
        # Extract base metrics
        current_price = self._safe_float(raw_financial.get('current_price'))
        month_high = self._safe_float(raw_financial.get('month_high'))
        month_low = self._safe_float(raw_financial.get('month_low'))
        volatility = self._safe_float(raw_financial.get('volatility'))
        
        clean_financial = {
            # Price metrics
            'current_price': current_price,
            'month_high': month_high,
            'month_low': month_low,
            'price_range': round(month_high - month_low, 2) if month_high and month_low else 0,
            
            # Performance indicators
            'price_position_in_range': self._calculate_price_position(current_price, month_high, month_low),
            'distance_from_high': self._calculate_distance_from_high(current_price, month_high),
            'distance_from_low': self._calculate_distance_from_low(current_price, month_low),
            
            # Volatility analysis
            'volatility_percent': round(volatility, 2) if volatility else 0,
            'volatility_category': self._categorize_volatility(volatility),
            'risk_level': self._assess_risk_level(volatility),
            
            # Derived scores
            'momentum_score': self._calculate_momentum_score(current_price, month_high, month_low),
            'stability_score': self._calculate_stability_score(volatility),
            'price_strength': self._assess_price_strength(current_price, month_high, month_low)
        }
        
        self.cleaning_log.append(f"INFO: Financial data cleaned: Price ${current_price:.2f}, Vol {volatility:.1f}%")
        return clean_financial
    
    def _clean_news_data(self, raw_news: Optional[Dict], ticker: str) -> Dict:
        """Clean and analyze news sentiment data."""
        if not raw_news or not raw_news.get('articles'):
            self.cleaning_log.append(f"No news data available for {ticker}")
            return self._get_empty_news()
        
        print(f"INFO: Cleaning news data...")
        
        articles = raw_news.get('articles', [])
        
        # Process articles
        processed_articles = []
        sentiment_scores = []
        sources = {}
        
        for article in articles:
            clean_article = {
                'title': self._clean_text(article.get('title', '')),
                'description': self._clean_text(article.get('description', '')),
                'source': article.get('source', 'Unknown'),
                'published_date': article.get('published_at', ''),
                'relevance_score': self._safe_float(article.get('relevance_score', 0.5)),
                'url': article.get('url', '')
            }
            
            # Track sources
            source = clean_article['source']
            sources[source] = sources.get(source, 0) + 1
            
            processed_articles.append(clean_article)
        
        # Calculate news metrics
        avg_relevance = sum(a['relevance_score'] for a in processed_articles) / len(processed_articles)
        top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:3]
        
        clean_news = {
            'total_articles': len(processed_articles),
            'articles': processed_articles[:10],  # Keep top 10 for LLM
            'average_relevance': round(avg_relevance, 3),
            'news_coverage': self._categorize_news_coverage(len(processed_articles)),
            'top_sources': [source[0] for source in top_sources],
            'source_diversity': len(sources),
            'recent_news_summary': self._create_news_summary(processed_articles[:5]),
            'news_freshness': self._assess_news_freshness(processed_articles),
            'media_attention_score': self._calculate_media_attention_score(len(processed_articles), avg_relevance)
        }
        
        self.cleaning_log.append(f"INFO: News data cleaned: {len(processed_articles)} articles, avg relevance {avg_relevance:.2f}")
        return clean_news
    
    def _clean_peer_data(self, raw_peers: Optional[Dict], ticker: str) -> Dict:
        """Clean and analyze peer comparison data."""
        if not raw_peers or not raw_peers.get('peer_companies'):
            self.cleaning_log.append(f"No peer data available for {ticker}")
            return self._get_empty_peers()
        
        print(f"INFO: Cleaning peer comparison data...")
        
        sector = raw_peers.get('sector', 'Unknown')
        peer_companies = raw_peers.get('peer_companies', [])
        current_metrics = raw_peers.get('current_company_metrics', {})
        relative_positioning = raw_peers.get('relative_positioning', {})
        
        # Clean peer companies
        clean_peers_list = []
        for peer in peer_companies:
            clean_peer = {
                'ticker': peer.get('ticker', ''),
                'company_name': self._clean_text(peer.get('company_name', '')),
                'market_cap': self._safe_float(peer.get('market_cap')),
                'pe_ratio': self._safe_float(peer.get('pe_ratio')),
                'profit_margin': self._safe_float(peer.get('profit_margin')),
                'debt_to_equity': self._safe_float(peer.get('debt_to_equity')),
                'return_on_equity': self._safe_float(peer.get('return_on_equity'))
            }
            clean_peers_list.append(clean_peer)
        
        # Calculate competitive position
        competitive_scores = self._calculate_competitive_scores(current_metrics, relative_positioning)
        
        clean_peers = {
            'sector': sector,
            'industry': raw_peers.get('industry', 'Unknown'),
            'peer_count': len(clean_peers_list),
            'peer_companies': clean_peers_list,
            'current_company_metrics': current_metrics,
            'sector_positioning': self._analyze_sector_positioning(relative_positioning),
            'competitive_advantages': self._identify_competitive_advantages(relative_positioning),
            'competitive_weaknesses': self._identify_competitive_weaknesses(relative_positioning),
            'overall_competitive_score': competitive_scores['overall'],
            'valuation_vs_peers': competitive_scores['valuation'],
            'profitability_vs_peers': competitive_scores['profitability'],
            'financial_strength_vs_peers': competitive_scores['financial_strength']
        }
        
        self.cleaning_log.append(f"INFO: Peer data cleaned: {len(clean_peers_list)} peers in {sector}")
        return clean_peers
    
    def _create_analysis_features(self, basic: Dict, financial: Dict, news: Dict, peers: Dict) -> Dict:
        """Create high-level analysis features for investment evaluation."""
        
        analysis = {
            # Company fundamentals
            'company_size': basic.get('market_cap_category', 'unknown'),
            'valuation_attractiveness': self._assess_valuation_attractiveness(
                basic.get('pe_ratio'), peers.get('valuation_vs_peers', 50)
            ),
            'financial_stability': financial.get('stability_score', 50),
            'growth_momentum': financial.get('momentum_score', 50),
            
            # Market perception
            'media_coverage_quality': news.get('media_attention_score', 50),
            'news_sentiment_trend': 'neutral',  # Will be enhanced with LLM
            
            # Competitive position
            'market_position_strength': peers.get('overall_competitive_score', 50),
            'sector_leadership': self._assess_sector_leadership(peers.get('sector_positioning', {})),
            
            # Risk factors
            'volatility_risk': self._convert_volatility_to_risk_score(financial.get('volatility_percent', 0)),
            'competitive_risk': self._assess_competitive_risk(peers.get('competitive_weaknesses', [])),
            
            # Investment thesis elements
            'key_strengths': self._identify_key_strengths(basic, financial, news, peers),
            'key_risks': self._identify_key_risks(basic, financial, news, peers),
            'investment_highlights': self._create_investment_highlights(basic, financial, news, peers)
        }
        
        return analysis
    
    def _calculate_investment_scores(self, basic: Dict, financial: Dict, news: Dict, peers: Dict) -> Dict:
        """Calculate comprehensive investment scores."""
        
        # Individual component scores (0-100)
        financial_score = self._calculate_financial_score(basic, financial)
        sentiment_score = self._calculate_sentiment_score(news)
        competitive_score = peers.get('overall_competitive_score', 50)
        momentum_score = financial.get('momentum_score', 50)
        
        # Weighted overall score
        overall_score = (
            financial_score * self.feature_weights['financial_health'] +
            sentiment_score * self.feature_weights['market_sentiment'] +
            competitive_score * self.feature_weights['peer_performance'] +
            momentum_score * self.feature_weights['market_position']
        )
        
        scores = {
            'overall_investment_score': round(overall_score, 1),
            'financial_health_score': round(financial_score, 1),
            'market_sentiment_score': round(sentiment_score, 1),
            'competitive_position_score': round(competitive_score, 1),
            'momentum_score': round(momentum_score, 1),
            
            # Letter grades
            'overall_grade': self._score_to_grade(overall_score),
            'financial_grade': self._score_to_grade(financial_score),
            'sentiment_grade': self._score_to_grade(sentiment_score),
            'competitive_grade': self._score_to_grade(competitive_score),
            
            # Investment recommendation
            'recommendation': self._score_to_recommendation(overall_score),
            'confidence_level': self._calculate_confidence_level(basic, financial, news, peers)
        }
        
        return scores
    
    def _create_llm_context(self, basic: Dict, financial: Dict, news: Dict, peers: Dict, analysis: Dict) -> Dict:
        """Create optimized context for LLM analysis."""
        
        # Create concise, structured context for LLM
        llm_context = {
            'executive_summary': {
                'company': f"{basic.get('company_name')} ({basic.get('ticker')})",
                'sector': f"{basic.get('sector')} - {basic.get('industry')}",
                'market_cap': f"${basic.get('market_cap_billions', 0):.1f}B ({basic.get('market_cap_category')})",
                'current_price': f"${basic.get('current_price', 0):.2f}",
                'key_metrics': {
                    'pe_ratio': basic.get('pe_ratio', 0),
                    'volatility': f"{financial.get('volatility_percent', 0):.1f}%",
                    'price_momentum': financial.get('price_strength', 'neutral')
                }
            },
            
            'financial_highlights': {
                'valuation': f"P/E {basic.get('pe_ratio', 0):.1f} ({basic.get('pe_category', 'unknown')})",
                'performance': f"Price at {financial.get('price_position_in_range', 0.5):.0%} of 30-day range",
                'risk_profile': financial.get('risk_level', 'unknown'),
                'stability': financial.get('volatility_category', 'unknown')
            },
            
            'market_context': {
                'recent_news_count': news.get('total_articles', 0),
                'media_attention': news.get('news_coverage', 'low'),
                'news_quality': f"Avg relevance {news.get('average_relevance', 0):.2f}",
                'top_sources': news.get('top_sources', [])[:3]
            },
            
            'competitive_position': {
                'sector': peers.get('sector', 'Unknown'),
                'peer_count': peers.get('peer_count', 0),
                'competitive_score': f"{peers.get('overall_competitive_score', 50):.0f}/100",
                'advantages': peers.get('competitive_advantages', [])[:3],
                'challenges': peers.get('competitive_weaknesses', [])[:3]
            },
            
            'investment_thesis': {
                'overall_score': analysis.get('investment_thesis_score', 50),
                'key_strengths': analysis.get('key_strengths', [])[:3],
                'key_risks': analysis.get('key_risks', [])[:3],
                'investment_highlights': analysis.get('investment_highlights', [])[:3]
            }
        }
        
        return llm_context
    
    # Helper methods for data cleaning and calculation
    def _safe_float(self, value, default: float = 0.0) -> float:
        """Safely convert value to float."""
        try:
            return float(value) if value and str(value).lower() != 'n/a' else default
        except (ValueError, TypeError):
            return default
    
    def _safe_int(self, value, default: int = 0) -> int:
        """Safely convert value to integer."""
        try:
            return int(value) if value and str(value).lower() != 'n/a' else default
        except (ValueError, TypeError):
            return default
    
    def _clean_text(self, text: Optional[str]) -> str:
        """Clean and standardize text fields."""
        if not text or text == 'N/A':
            return 'Unknown'
        return str(text).strip()
    
    def _convert_to_billions(self, value) -> float:
        """Convert large numbers to billions."""
        try:
            return round(float(value) / 1_000_000_000, 2) if value else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _categorize_market_cap(self, market_cap) -> str:
        """Categorize company by market cap."""
        if not market_cap:
            return 'unknown'
        
        cap_billions = self._convert_to_billions(market_cap)
        if cap_billions >= 200:
            return 'mega_cap'
        elif cap_billions >= 10:
            return 'large_cap'
        elif cap_billions >= 2:
            return 'mid_cap'
        elif cap_billions >= 0.3:
            return 'small_cap'
        else:
            return 'micro_cap'
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numerical score to letter grade."""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        else:
            return 'D'
    
    def _score_to_recommendation(self, score: float) -> str:
        """Convert score to investment recommendation."""
        if score >= 80:
            return 'STRONG BUY'
        elif score >= 70:
            return 'BUY'
        elif score >= 60:
            return 'HOLD'
        elif score >= 50:
            return 'WEAK HOLD'
        else:
            return 'SELL'
    
    # Placeholder methods for empty data
    def _get_empty_basic(self) -> Dict:
        return {'ticker': 'UNKNOWN', 'company_name': 'Unknown', 'sector': 'Unknown'}
    
    def _get_empty_financial(self) -> Dict:
        return {'current_price': 0, 'volatility_percent': 0, 'risk_level': 'unknown'}
    
    def _get_empty_news(self) -> Dict:
        return {'total_articles': 0, 'articles': [], 'news_coverage': 'none'}
    
    def _get_empty_peers(self) -> Dict:
        return {'sector': 'Unknown', 'peer_count': 0, 'peer_companies': []}
    
    def _show_cleaning_summary(self, clean_dataset: Dict):
        """Show summary of cleaning process."""
        scores = clean_dataset.get('investment_scores', {})
        quality = clean_dataset.get('data_quality', {})
        
        print(f"\nINFO: Data cleaning completed")
        print(f"Company: {clean_dataset.get('company_name')}")
        print(f"Overall Score: {scores.get('overall_investment_score', 0):.1f}/100 ({scores.get('overall_grade', 'N/A')})")
        print(f"Recommendation: {scores.get('recommendation', 'UNKNOWN')}")
        print(f"Data Quality: {sum(quality.values())}/{len(quality)} sources clean")
        print(f"INFO: Ready for LLM analysis and report generation")
    
    # Missing helper methods implementation
    def _standardize_sector(self, sector):
        """Standardize sector names."""
        if not sector or sector == 'N/A':
            return 'Unknown'
        return str(sector).strip().title()
    
    def _categorize_pe_ratio(self, pe_ratio):
        """Categorize P/E ratio."""
        if not pe_ratio or pe_ratio <= 0:
            return 'negative_or_none'
        elif pe_ratio < 15:
            return 'undervalued'
        elif pe_ratio < 25:
            return 'fair_value'
        elif pe_ratio < 40:
            return 'overvalued'
        else:
            return 'highly_overvalued'
    
    def _clean_description(self, description):
        """Clean business description."""
        if not description or description == 'N/A':
            return 'No description available'
        desc = str(description).strip()
        return desc[:300] + '...' if len(desc) > 300 else desc
    
    def _calculate_price_position(self, current, high, low):
        """Calculate price position in range (0-1)."""
        if not all([current, high, low]) or high == low:
            return 0.5
        return (current - low) / (high - low)
    
    def _calculate_distance_from_high(self, current, high):
        """Calculate distance from 52-week high."""
        if not current or not high:
            return 0
        return round((high - current) / high * 100, 1)
    
    def _calculate_distance_from_low(self, current, low):
        """Calculate distance from 52-week low."""
        if not current or not low:
            return 0
        return round((current - low) / low * 100, 1)
    
    def _categorize_volatility(self, volatility):
        """Categorize volatility level."""
        if not volatility:
            return 'unknown'
        if volatility < 15:
            return 'low'
        elif volatility < 30:
            return 'medium'
        else:
            return 'high'
    
    def _assess_risk_level(self, volatility):
        """Assess overall risk level."""
        if not volatility:
            return 'unknown'
        if volatility < 20:
            return 'conservative'
        elif volatility < 35:
            return 'moderate'
        else:
            return 'aggressive'
    
    def _calculate_momentum_score(self, current, high, low):
        """Calculate momentum score (0-100)."""
        position = self._calculate_price_position(current, high, low)
        return round(position * 100, 1)
    
    def _calculate_stability_score(self, volatility):
        """Calculate stability score (0-100)."""
        if not volatility:
            return 50
        if volatility < 15:
            return 90
        elif volatility < 25:
            return 70
        elif volatility < 35:
            return 50
        else:
            return 25
    
    def _assess_price_strength(self, current, high, low):
        """Assess price strength."""
        position = self._calculate_price_position(current, high, low)
        if position > 0.8:
            return 'strong'
        elif position > 0.6:
            return 'moderate'
        elif position > 0.4:
            return 'neutral'
        elif position > 0.2:
            return 'weak'
        else:
            return 'very_weak'
    
    def _categorize_news_coverage(self, article_count):
        """Categorize news coverage level."""
        if article_count >= 10:
            return 'high'
        elif article_count >= 5:
            return 'medium'
        elif article_count >= 1:
            return 'low'
        else:
            return 'none'
    
    def _create_news_summary(self, articles):
        """Create summary of recent news."""
        if not articles:
            return 'No recent news available'
        titles = [article.get('title', '') for article in articles[:3]]
        return '; '.join(titles)
    
    def _assess_news_freshness(self, articles):
        """Assess how fresh the news is."""
        if not articles:
            return 'no_news'
        # Simplified freshness assessment
        return 'recent'
    
    def _calculate_media_attention_score(self, article_count, avg_relevance):
        """Calculate media attention score (0-100)."""
        coverage_score = min(article_count * 5, 50)  # Max 50 for coverage
        relevance_score = avg_relevance * 50  # Max 50 for relevance
        return round(coverage_score + relevance_score, 1)
    
    def _calculate_competitive_scores(self, current_metrics, relative_positioning):
        """Calculate competitive positioning scores."""
        scores = {
            'overall': 60,  # Default neutral score
            'valuation': 50,
            'profitability': 50,
            'financial_strength': 50
        }
        
        # Enhance based on relative positioning
        if relative_positioning:
            pe_vs_sector = relative_positioning.get('pe_ratio_vs_sector', 1.0)
            if pe_vs_sector and pe_vs_sector < 1.0:  # Lower P/E is better
                scores['valuation'] = min(75, 50 + (1.0 - pe_vs_sector) * 50)
        
        return scores
    
    def _analyze_sector_positioning(self, relative_positioning):
        """Analyze sector positioning."""
        return {
            'overall_position': 'average',
            'strengths': [],
            'weaknesses': []
        }
    
    def _identify_competitive_advantages(self, relative_positioning):
        """Identify competitive advantages."""
        advantages = []
        if relative_positioning.get('pe_ratio_vs_sector', 1.0) < 0.9:
            advantages.append('Attractive valuation vs peers')
        return advantages
    
    def _identify_competitive_weaknesses(self, relative_positioning):
        """Identify competitive weaknesses."""
        weaknesses = []
        if relative_positioning.get('pe_ratio_vs_sector', 1.0) > 1.3:
            weaknesses.append('Premium valuation vs peers')
        return weaknesses
    
    def _assess_valuation_attractiveness(self, pe_ratio, peer_valuation_score):
        """Assess valuation attractiveness."""
        if not pe_ratio:
            return 50
        if pe_ratio < 15:
            return 85
        elif pe_ratio < 25:
            return 70
        else:
            return 40
    
    def _assess_sector_leadership(self, sector_positioning):
        """Assess sector leadership."""
        return 60  # Default score
    
    def _convert_volatility_to_risk_score(self, volatility):
        """Convert volatility to risk score."""
        if not volatility:
            return 50
        return min(100, volatility * 2)  # Higher volatility = higher risk score
    
    def _assess_competitive_risk(self, weaknesses):
        """Assess competitive risk."""
        return len(weaknesses) * 15  # Higher risk with more weaknesses
    
    def _identify_key_strengths(self, basic, financial, news, peers):
        """Identify key investment strengths."""
        strengths = []
        
        if basic.get('market_cap_category') in ['large_cap', 'mega_cap']:
            strengths.append('Large, established company')
        
        if financial.get('volatility_category') == 'low':
            strengths.append('Low volatility profile')
        
        if news.get('media_attention_score', 0) > 60:
            strengths.append('Strong media coverage')
        
        return strengths[:3]
    
    def _identify_key_risks(self, basic, financial, news, peers):
        """Identify key investment risks."""
        risks = []
        
        if financial.get('volatility_category') == 'high':
            risks.append('High price volatility')
        
        if basic.get('pe_category') == 'highly_overvalued':
            risks.append('Very high valuation metrics')
        
        if news.get('total_articles', 0) < 3:
            risks.append('Limited recent news coverage')
        
        return risks[:3]
    
    def _create_investment_highlights(self, basic, financial, news, peers):
        """Create investment highlights."""
        highlights = []
        
        company_name = basic.get('company_name', 'Company')
        sector = basic.get('sector', 'Unknown')
        
        highlights.append(f"{company_name} operates in {sector} sector")
        
        price = basic.get('current_price', 0)
        if price:
            highlights.append(f"Current price: ${price:.2f}")
        
        market_cap = basic.get('market_cap_category', '')
        if market_cap:
            highlights.append(f"{market_cap.replace('_', ' ').title()} company")
        
        return highlights[:3]
    
    def _calculate_financial_score(self, basic, financial):
        """Calculate overall financial health score."""
        score = 50  # Base score
        
        # PE ratio scoring
        pe_ratio = basic.get('pe_ratio', 0)
        if pe_ratio and 10 < pe_ratio < 25:
            score += 15
        elif pe_ratio and pe_ratio > 40:
            score -= 15
        
        # Volatility scoring
        volatility = financial.get('volatility_percent', 0)
        if volatility < 20:
            score += 10
        elif volatility > 40:
            score -= 15
        
        # Market cap scoring
        market_cap_cat = basic.get('market_cap_category', '')
        if market_cap_cat in ['large_cap', 'mega_cap']:
            score += 10
        
        return max(0, min(100, score))
    
    def _calculate_sentiment_score(self, news):
        """Calculate sentiment score based on news."""
        if not news or news.get('total_articles', 0) == 0:
            return 50  # Neutral when no news
        
        # Base score from media attention
        base_score = news.get('media_attention_score', 50)
        
        # Adjust for coverage quality
        coverage = news.get('news_coverage', 'none')
        if coverage == 'high':
            base_score += 10
        elif coverage == 'low':
            base_score -= 5
        
        return max(0, min(100, base_score))
    
    def _calculate_confidence_level(self, basic, financial, news, peers):
        """Calculate confidence level in analysis."""
        confidence_factors = 0
        total_factors = 4
        
        if basic and basic.get('company_name') != 'Unknown':
            confidence_factors += 1
        if financial and financial.get('current_price', 0) > 0:
            confidence_factors += 1
        if news and news.get('total_articles', 0) > 0:
            confidence_factors += 1
        if peers and peers.get('peer_count', 0) > 0:
            confidence_factors += 1
        
        confidence = (confidence_factors / total_factors) * 100
        
        if confidence >= 75:
            return 'high'
        elif confidence >= 50:
            return 'medium'
        else:
            return 'low'
    
    def _assess_data_quality(self, basic, financial, news, peers):
        """Assess overall data quality."""
        return {
            'basic_info_quality': basic.get('company_name') != 'Unknown',
            'financial_data_quality': financial.get('current_price', 0) > 0,
            'news_data_quality': news.get('total_articles', 0) > 0,
            'peer_data_quality': peers.get('peer_count', 0) > 0
        } 
    