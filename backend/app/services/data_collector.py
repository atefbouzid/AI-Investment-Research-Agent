import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
# For environment variables
from dotenv import load_dotenv
load_dotenv()


class StockDataCollector:
    """
    A comprehensive stock data collector that fetches financial information from Yahoo Finance.
    
    This class provides methods to collect basic company information and financial metrics
    for any given stock ticker. It includes error handling and formatted output for debugging.
    
    Attributes:
        ticker (str): The stock ticker symbol (e.g., 'AAPL', 'TSLA')
        stock (yfinance.Ticker): Yahoo Finance ticker object
    """

    def __init__(self, ticker):
        """
        Initialize the StockDataCollector with a stock ticker.
        
        Args:
            ticker (str): Stock ticker symbol to analyze
        """
        self.ticker = ticker
        self.stock = yf.Ticker(self.ticker)

    def get_stock_info(self):
        """
        Fetch comprehensive company information and metadata.
        
        Collects essential company details including financial metrics,
        business description, and organizational information.
        
        Returns:
            dict: Dictionary containing company information, None if error occurs
        """
        try:
            info = self.stock.info
            basic_data = {
                'company_name': info.get('longName', 'N/A'),
                'current_price': info.get('currentPrice', 0),  # Real-time stock price
                'market_cap': info.get('marketCap', 0),  # Total company valuation
                'pe_ratio': info.get('trailingPE', 0),  # Price-to-earnings ratio
                'sector': info.get('sector', 'N/A'),  # Business sector classification
                'industry': info.get('industry', 'N/A'),  # Specific industry category
                'short_name': info.get('shortName', 'N/A'),
                'country': info.get('country', 'N/A'),  # Company headquarters location
                'employee_count': info.get('fullTimeEmployees', 0),  # Total workforce size
                'long_business_summary': info.get('longBusinessSummary', 'N/A'),  # Company description
                'company_website': info.get('website', 'N/A')  # Official website URL
            }

            print("Basic info Collected :")
            for key, value in basic_data.items():
                print(f"    {key}:  {value}")
            print()
            return basic_data
        except Exception as e:
            print(f"Error getting stock info: {e}")
            return None
        

    def get_financial_data(self):
        """
        Fetch recent financial performance metrics and price data.
        
        Analyzes 1-month historical data to calculate key financial indicators
        including price ranges and volatility measures.
        
        Returns:
            dict: Dictionary containing financial metrics, None if error occurs
        """
        try:
            hist = self.stock.history(period='1mo')

            if not hist.empty:
                current_price = hist['Close'].iloc[-1]  # Most recent closing price
                month_high = hist['High'].max()  # Highest price in past month
                month_low = hist['Low'].min()  # Lowest price in past month
                volatility = hist['Close'].pct_change().std()*100  # Price volatility percentage
                
                financial_data = {
                    'current_price': current_price,
                    'month_high': month_high,
                    'month_low': month_low,
                    'volatility': volatility,
                }
                
                print("Financial data collected :")
                for key, value in financial_data.items():
                    print(f"    {key}:  {value}")
                print()
                return financial_data
        except Exception as e:
            print(f"Error getting financial data: {e}")
            return None

    def get_news_data(self) -> Dict:
        """
        Collect recent news articles (raw data for LLM analysis).
        
        Fetches clean, structured news data that will be analyzed by LLM later.
        No sentiment analysis here - just clean data collection.
        
        Returns:
            dict: Dictionary containing raw news articles ready for LLM analysis
        """
        try:
            print(f"📰 Collecting news data for {self.ticker}...")
            
            # Get API key from environment
            news_api_key = os.getenv('NEWS_API_KEY')
            if not news_api_key:
                print("⚠️  NEWS_API_KEY not found in environment variables")
                return self._get_fallback_news()
            
            # Get company name for better search
            try:
                company_name = self.stock.info.get('longName', self.ticker)
            except:
                company_name = self.ticker
                
            search_query = f'"{company_name}" OR "{self.ticker}"'
            
            # NewsAPI endpoint
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': search_query,
                'apiKey': news_api_key,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 15,  # Get 15 most recent articles
                'from': (datetime.now() - timedelta(days=7)).isoformat(),  # Last 7 days
                'excludeDomains': 'yahoo.com'  # Avoid duplicate content
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            news_data = response.json()
            articles = news_data.get('articles', [])
            
            if not articles:
                print("📰 No recent news found")
                return self._get_fallback_news()
            
            # Process and clean articles (no sentiment analysis)
            processed_articles = []
            
            for article in articles:
                # Clean and validate article data
                if self._is_valid_article(article):
                    clean_article = {
                        'title': article['title'].strip(),
                        'description': article.get('description', '').strip(),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'published_at': article['publishedAt'],
                        'url': article['url'],
                        'relevance_score': self._calculate_relevance(article, self.ticker, company_name)
                    }
                    processed_articles.append(clean_article)
            
            # Sort by relevance and recency
            processed_articles = sorted(
                processed_articles, 
                key=lambda x: (x['relevance_score'], x['published_at']), 
                reverse=True
            )[:10]  # Keep top 10 most relevant articles
            
            news_summary = {
                'ticker': self.ticker,
                'company_name': company_name,
                'articles': processed_articles,
                'total_articles': len(processed_articles),
                'collection_date': datetime.now().isoformat(),
                'date_range': {
                    'from': (datetime.now() - timedelta(days=7)).isoformat(),
                    'to': datetime.now().isoformat()
                },
                'ready_for_llm_analysis': True  # Flag for LLM processing
            }
            
            print(f"✅ Collected {len(processed_articles)} relevant news articles")
            print(f"📊 Ready for LLM analysis")
            
            return news_summary
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching news: {e}")
            return self._get_fallback_news()
        except Exception as e:
            print(f"❌ Error processing news: {e}")
            return self._get_fallback_news()
    
    def _is_valid_article(self, article: Dict) -> bool:
        """Check if article has minimum required data quality."""
        return (
            article.get('title') and 
            len(article['title'].strip()) > 2 and
            article.get('description') and
            len(article['description'].strip()) > 20 and
            article.get('publishedAt') and
            article.get('url')
        )
    
    def _calculate_relevance(self, article: Dict, ticker: str, company_name: str) -> float:
        """
        Calculate relevance score for article (0.0 to 1.0).
        Higher score = more relevant to the stock.
        """
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        text = f"{title} {description}"
        
        score = 0.0
        
        # Ticker mentions (highest priority)
        if ticker.lower() in text:
            score += 0.3
        
        # Company name mentions
        if company_name.lower() in text:
            score += 0.3
        
        # Financial keywords
        financial_keywords = [
            'earnings', 'revenue', 'profit', 'sales', 'quarterly', 
            'financial', 'stock', 'shares', 'market', 'investors',
            'analyst', 'upgrade', 'downgrade', 'target price'
        ]
        for keyword in financial_keywords:
            if keyword in text:
                score += 0.05
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def _get_fallback_news(self) -> Dict:
        """Fallback news data when API is unavailable."""
        return {
            'ticker': getattr(self, 'ticker', 'N/A'),
            'company_name': 'Unknown',
            'articles': [],
            'total_articles': 0,
            'collection_date': datetime.now().isoformat(),
            'ready_for_llm_analysis': False,
            'note': 'News API unavailable - using fallback data'
        }
    

















    ###
    def get_peer_comparison_data(self) -> Dict:
        """
        Collect peer comparison data for competitive analysis.
        
        Finds similar companies in the same sector and compares key metrics.
        Essential for relative valuation and market positioning.
        
        Returns:
            dict: Dictionary containing peer comparison analysis
        """
        try:
            print(f"🏢 Collecting peer comparison data for {self.ticker}...")
            
            # Get basic info to identify sector
            try:
                info = self.stock.info
                sector = info.get('sector', 'Unknown')
                industry = info.get('industry', 'Unknown')
                market_cap = info.get('marketCap', 0)
            except:
                print("⚠️  Could not get company info for peer analysis")
                return self._get_fallback_peers()
            
            # Define peer companies by sector (we can expand this)
            peer_map = {
                'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'TSLA'],
                'Healthcare': ['JNJ', 'PFE', 'UNH', 'ABBV', 'MRK'],
                'Financial Services': ['JPM', 'BAC', 'WFC', 'GS', 'MS'],
                'Consumer Cyclical': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE'],
                'Energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB'],
                'Industrials': ['BA', 'CAT', 'GE', 'MMM', 'HON']
            }
            
            # Get potential peers from sector
            potential_peers = peer_map.get(sector, [])
            
            # Remove self from peers list
            if self.ticker in potential_peers:
                potential_peers.remove(self.ticker)
            
            # Limit to top 4 peers for API efficiency
            selected_peers = potential_peers[:4]
            
            if not selected_peers:
                print(f"⚠️  No peers found for sector: {sector}")
                return self._get_fallback_peers()
            
            print(f"📊 Analyzing peers: {', '.join(selected_peers)}")
            
            # Collect peer data
            peer_data = []
            comparison_metrics = {}
            
            for peer_ticker in selected_peers:
                try:
                    peer_stock = yf.Ticker(peer_ticker)
                    peer_info = peer_stock.info
                    
                    peer_metrics = {
                        'ticker': peer_ticker,
                        'company_name': peer_info.get('longName', peer_ticker),
                        'market_cap': peer_info.get('marketCap', 0),
                        'pe_ratio': peer_info.get('trailingPE', 0),
                        'price_to_book': peer_info.get('priceToBook', 0),
                        'profit_margin': peer_info.get('profitMargins', 0),
                        'debt_to_equity': peer_info.get('debtToEquity', 0),
                        'return_on_equity': peer_info.get('returnOnEquity', 0),
                        'current_price': peer_info.get('currentPrice', 0)
                    }
                    
                    peer_data.append(peer_metrics)
                    
                except Exception as e:
                    print(f"⚠️  Could not get data for peer {peer_ticker}: {e}")
                    continue
            
            if not peer_data:
                print("❌ No peer data collected")
                return self._get_fallback_peers()
            
            # Calculate sector averages
            sector_averages = self._calculate_sector_averages(peer_data)
            
            # Get current company metrics for comparison
            current_metrics = {
                'market_cap': market_cap,
                'pe_ratio': info.get('trailingPE', 0),
                'price_to_book': info.get('priceToBook', 0),
                'profit_margin': info.get('profitMargins', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'return_on_equity': info.get('returnOnEquity', 0)
            }
            
            # Calculate relative positioning
            relative_metrics = self._calculate_relative_positioning(current_metrics, sector_averages)
            
            peer_analysis = {
                'ticker': self.ticker,
                'sector': sector,
                'industry': industry,
                'peer_companies': peer_data,
                'sector_averages': sector_averages,
                'current_company_metrics': current_metrics,
                'relative_positioning': relative_metrics,
                'peer_count': len(peer_data),
                'collection_date': datetime.now().isoformat(),
                'ready_for_llm_analysis': True
            }
            
            print(f"✅ Collected peer data for {len(peer_data)} companies")
            print(f"📊 Sector: {sector} | Relative P/E: {relative_metrics.get('pe_ratio_vs_sector', 'N/A')}")
            
            return peer_analysis
            
        except Exception as e:
            print(f"❌ Error collecting peer data: {e}")
            return self._get_fallback_peers()
    
    def _calculate_sector_averages(self, peer_data: List[Dict]) -> Dict:
        """Calculate average metrics across peer companies."""
        if not peer_data:
            return {}
        
        metrics_to_average = ['market_cap', 'pe_ratio', 'price_to_book', 'profit_margin', 'debt_to_equity', 'return_on_equity']
        averages = {}
        
        for metric in metrics_to_average:
            values = [peer.get(metric, 0) for peer in peer_data if peer.get(metric, 0) > 0]
            if values:
                averages[f'avg_{metric}'] = sum(values) / len(values)
                averages[f'median_{metric}'] = sorted(values)[len(values) // 2]
            else:
                averages[f'avg_{metric}'] = 0
                averages[f'median_{metric}'] = 0
        
        return averages
    
    def _calculate_relative_positioning(self, current: Dict, averages: Dict) -> Dict:
        """Calculate how current company compares to sector averages."""
        relative = {}
        
        for metric in current:
            current_value = current.get(metric, 0)
            avg_value = averages.get(f'avg_{metric}', 0)
            
            if avg_value > 0 and current_value > 0:
                ratio = current_value / avg_value
                relative[f'{metric}_vs_sector'] = round(ratio, 2)
                
                # Categorize relative performance
                if ratio > 1.2:
                    relative[f'{metric}_category'] = 'above_average'
                elif ratio < 0.8:
                    relative[f'{metric}_category'] = 'below_average'
                else:
                    relative[f'{metric}_category'] = 'average'
            else:
                relative[f'{metric}_vs_sector'] = None
                relative[f'{metric}_category'] = 'unknown'
        
        return relative
    
    def _get_fallback_peers(self) -> Dict:
        """Fallback peer data when analysis is unavailable."""
        return {
            'ticker': getattr(self, 'ticker', 'N/A'),
            'sector': 'Unknown',
            'industry': 'Unknown',
            'peer_companies': [],
            'sector_averages': {},
            'current_company_metrics': {},
            'relative_positioning': {},
            'peer_count': 0,
            'collection_date': datetime.now().isoformat(),
            'ready_for_llm_analysis': False,
            'note': 'Peer analysis unavailable - using fallback data'
        }
    
    def collect_complete_dataset(self) -> Dict:
        """
        Collect complete dataset for comprehensive stock analysis.
        
        This is the main method that collects ALL data types needed
        for generating investment research reports.
        
        Returns:
            dict: Complete dataset ready for cleaning and LLM analysis
        """
        print(f"\n🚀 COLLECTING COMPLETE DATASET FOR {self.ticker}")
        print("="*60)
        
        # Collect all data types
        basic_info = self.get_stock_info()
        financial_data = self.get_financial_data()
        news_data = self.get_news_data()
        peer_data = self.get_peer_comparison_data()
        
        # Combine into complete dataset
        complete_dataset = {
            'ticker': self.ticker,
            'collection_timestamp': datetime.now().isoformat(),
            'data_sources': {
                'basic_info': basic_info,
                'financial_data': financial_data,
                'news_data': news_data,
                'peer_comparison': peer_data
            },
            'data_quality': {
                'basic_info_available': basic_info is not None,
                'financial_data_available': financial_data is not None,
                'news_data_available': news_data is not None and news_data.get('total_articles', 0) > 0,
                'peer_data_available': peer_data is not None and peer_data.get('peer_count', 0) > 0
            },
            'ready_for_cleaning': True,
            'collection_summary': {
                'total_data_sources': 4,
                'successful_collections': sum([
                    basic_info is not None,
                    financial_data is not None,
                    news_data is not None and news_data.get('total_articles', 0) > 0,
                    peer_data is not None and peer_data.get('peer_count', 0) > 0
                ]),
                'news_articles_collected': news_data.get('total_articles', 0) if news_data else 0,
                'peer_companies_analyzed': peer_data.get('peer_count', 0) if peer_data else 0
            }
        }
        
        # Show collection summary
        summary = complete_dataset['collection_summary']
        print(f"\n📊 COLLECTION COMPLETE:")
        print(f"✅ Data sources: {summary['successful_collections']}/{summary['total_data_sources']}")
        print(f"📰 News articles: {summary['news_articles_collected']}")
        print(f"🏢 Peer companies: {summary['peer_companies_analyzed']}")
        print(f"✅ Ready for data cleaning pipeline")
        
        return complete_dataset
                