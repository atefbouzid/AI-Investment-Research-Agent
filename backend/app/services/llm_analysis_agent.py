"""
LLM Analysis Agent for Investment Research
Takes clean data and generates comprehensive investment insights using AI
Supports BOTH local models and API calls with smart fallback
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import requests

class InvestmentAnalysisAgent:
    """
    AI-powered investment analysis agent.
    
    Supports flexible AI backends:
    - Local models (100% free, private)
    - API calls (OpenAI, OpenRouter, DeepSeek)
    - Smart fallback between them
    """
    
    def __init__(self, use_local_llm: bool = False):
        """
        Simple initialization: Local LLM or DeepSeek API.
        
        Args:
            use_local_llm: True = local models, False = DeepSeek API
        """
        self.use_local_llm = False  # Always use OpenRouter API
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.backend = None
        self.local_llm = None
        
        # Setup AI backend
        if use_local_llm:
            self._setup_local_llm()
        else:
            self._setup_api()
        
        print(f"Investment Agent ready: {self.backend}")

    def _setup_local_llm(self):
        """Setup local LLM if possible, fallback to API."""
        try:
            from .local_llm_handler import LocalLLMHandler
            self.local_llm = LocalLLMHandler()
            self.local_llm.load_model(use_quantization=True)
            self.backend = "local_llm"
        except:
            self._setup_api()
        
    def _setup_api(self):
        """Setup DeepSeek API."""
        if self.api_key:
            self.backend = "deepseek_api"
        else:
            self.backend = "none"

    def _call_api(self, prompt: str) -> str:
        """
        Simple API call to DeepSeek.
        
        Args:
            prompt: Question for the AI
            
        Returns:
            AI response text
        """
        if not self.api_key:
            return "❌ No API key"
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are a professional investment analyst with deep expertise in financial markets."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
            else:
                return f"API Error: {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_model_name(self) -> str:
        """Get the actual model name being used."""
        if self.backend == "local_llm" and self.local_llm:
            # Get model name from local LLM handler
            if hasattr(self.local_llm, 'current_model_name'):
                return self.local_llm.current_model_name
            elif hasattr(self.local_llm, 'model_name'):
                return self.local_llm.model_name
            else:
                return "Local LLM (Unknown Model)"
        elif self.backend == "deepseek_api":
            return "deepseek-chat"
        else:
            return "No Model"
    
    def generate_analysis(self, prompt: str) -> str:
        """
        Generate investment analysis using available AI backend.
        
        Args:
            prompt: Analysis question
            
        Returns:
            Analysis response
        """
        if self.backend == "local_llm":
            return self.local_llm.generate_text(prompt)
        elif self.backend == "deepseek_api":
            return self._call_api(prompt)
        else:
            return "❌ No AI backend available"
        
    def analyze_investment(self, clean_data: Dict) -> Dict:
        """
        Main method: Generate complete investment analysis from clean data.
        
        Args:
            clean_data: Output from InvestmentDataCleaner
            
        Returns:
            Complete investment analysis ready for reports
        """
        ticker = clean_data.get('ticker', 'UNKNOWN')
        company_name = clean_data.get('company_name', 'Unknown Company')
        
        print(f"🎯 Analyzing {company_name} ({ticker}) with {self.backend}")
        
        # Generate different analysis sections
        analysis = {
            'ticker': ticker,
            'company_name': company_name,
            'analysis_timestamp': datetime.now().isoformat(),
            'backend_used': self.backend,
            'model_used': self._get_model_name()
        }
        
        # 1. Executive Summary
        analysis['executive_summary'] = self._generate_executive_summary(clean_data)
        
        # 2. Financial Analysis  
        analysis['financial_analysis'] = self._generate_financial_analysis(clean_data)
        
        # 3. Market Sentiment
        analysis['sentiment_analysis'] = self._generate_sentiment_analysis(clean_data)
        
        # 4. Competitive Analysis
        analysis['competitive_analysis'] = self._generate_competitive_analysis(clean_data)
        
        # 5. Investment Thesis
        analysis['investment_thesis'] = self._generate_investment_thesis(clean_data)
        
        # 6. Risk Assessment
        analysis['risk_assessment'] = self._generate_risk_assessment(clean_data)
        
        # 7. Investment Recommendation
        analysis['recommendation'] = self._generate_recommendation(clean_data)
        
        # Calculate overall score
        analysis['overall_score'] = self._calculate_overall_score(clean_data)
        
        self._show_analysis_summary(analysis)
        
        return analysis
    
    def _generate_executive_summary(self, clean_data: Dict) -> Dict:
        """Generate executive summary of the investment."""
        
        # Extract key info for the prompt
        company_overview = clean_data.get('company_overview', {})
        investment_scores = clean_data.get('investment_scores', {})
        
        company_name = company_overview.get('company_name', 'Unknown')
        sector = company_overview.get('sector', 'Unknown')
        current_price = company_overview.get('current_price', 0)
        overall_score = investment_scores.get('overall_investment_score', 0)
        recommendation = investment_scores.get('recommendation', 'HOLD')
        
        # Create AI prompt
        prompt = f"""
        Write a professional executive summary for {company_name}:
        
        Company Details:
        - Sector: {sector}
        - Current Price: ${current_price:.2f}
        - Overall Investment Score: {overall_score:.1f}/100
        - Recommendation: {recommendation}
        
        Write 2-3 paragraphs covering:
        1. Company overview and market position
        2. Key investment highlights and value proposition
        3. Overall recommendation rationale
        
        Keep it professional, concise, and investor-focused.
        """
        
        # Generate analysis using AI
        summary_text = self.generate_analysis(prompt)
        
        return {
            'summary_text': summary_text,
            'overall_score': overall_score,
            'recommendation': recommendation,
            'key_metrics': {
                'current_price': current_price,
                'sector': sector,
                'overall_score': overall_score
            }
        }

    def _generate_financial_analysis(self, clean_data: Dict) -> Dict:
        """
        Generate financial performance analysis.
        
        Args:
            clean_data: Clean dataset from data cleaner
            
        Returns:
            Financial analysis section
        """
        # Extract financial data
        company_overview = clean_data.get('company_overview', {})
        financial_metrics = clean_data.get('financial_metrics', {})
        
        current_price = company_overview.get('current_price', 0)
        pe_ratio = company_overview.get('pe_ratio', 0)
        market_cap_billions = company_overview.get('market_cap_billions', 0)
        volatility = financial_metrics.get('volatility_percent', 0)
        momentum_score = financial_metrics.get('momentum_score', 0)
        
        # Create AI prompt
        prompt = f"""
        Analyze the financial performance and valuation:
        
        Financial Metrics:
        - Current Price: ${current_price:.2f}
        - P/E Ratio: {pe_ratio:.1f}
        - Market Cap: ${market_cap_billions:.1f}B
        - Volatility: {volatility:.1f}%
        - Momentum Score: {momentum_score:.1f}/100
        
        Provide analysis covering:
        1. Valuation assessment (attractive/fair/expensive with rationale)
        2. Financial strength and performance trends
        3. Risk factors and volatility analysis
        4. Momentum and technical indicators
        
        Write 3-4 professional paragraphs with specific financial insights.
        """
        
        # Generate analysis
        analysis_text = self.generate_analysis(prompt)
        
        # Determine momentum trend
        momentum_trend = 'strong' if momentum_score > 70 else 'weak' if momentum_score < 40 else 'neutral'
        
        return {
            'analysis_text': analysis_text,
            'valuation_assessment': 'fair' if 15 < pe_ratio < 25 else 'expensive' if pe_ratio > 25 else 'attractive',
            'risk_level': 'high' if volatility > 30 else 'medium' if volatility > 20 else 'low',
            'momentum_trend': momentum_trend,
            'key_metrics': {
                'pe_ratio': pe_ratio,
                'volatility': volatility,
                'momentum_score': momentum_score,
                'market_cap_billions': market_cap_billions
            }
        }

    def _generate_sentiment_analysis(self, clean_data: Dict) -> Dict:
        """
        Generate market sentiment analysis.
        
        Args:
            clean_data: Clean dataset from data cleaner
            
        Returns:
            Sentiment analysis section
        """
        # Extract sentiment data
        market_sentiment = clean_data.get('market_sentiment', {})
        company_name = clean_data.get('company_name', 'Unknown Company')
        
        total_articles = market_sentiment.get('total_articles', 0)
        media_attention_score = market_sentiment.get('media_attention_score', 50)
        top_sources = market_sentiment.get('top_sources', [])
        articles = market_sentiment.get('articles', [])
        
        # Get recent headlines
        recent_headlines = []
        for article in articles[:3]:
            if article.get('title'):
                recent_headlines.append(article['title'])
        
        # Create AI prompt
        prompt = f"""
        Analyze market sentiment for {company_name}:
        
        Media Coverage:
        - Total Recent Articles: {total_articles}
        - Media Attention Score: {media_attention_score:.1f}/100
        - Top Sources: {', '.join(top_sources[:3])}
        
        Recent Headlines:
        {chr(10).join([f"- {headline}" for headline in recent_headlines])}
        
        Provide analysis covering:
        1. Overall media sentiment and coverage quality
        2. Key themes and market perception
        3. Impact on investor sentiment and stock performance
        4. Social media and retail investor sentiment
        
        Write 2-3 professional paragraphs.
        """
        
        # Generate analysis
        sentiment_text = self.generate_analysis(prompt)
        
        return {
            'analysis_text': sentiment_text,
            'media_attention_score': media_attention_score,
            'coverage_quality': 'high' if total_articles > 10 else 'medium' if total_articles > 5 else 'low',
            'recent_headlines': recent_headlines,
            'sentiment_trend': 'positive' if media_attention_score > 60 else 'neutral' if media_attention_score > 40 else 'negative'
        }

    def _generate_competitive_analysis(self, clean_data: Dict) -> Dict:
        """Generate competitive landscape analysis."""
        company_overview = clean_data.get('company_overview', {})
        company_name = company_overview.get('company_name', 'Unknown')
        sector = company_overview.get('sector', 'Unknown')
        market_cap_billions = company_overview.get('market_cap_billions', 0)
        
        prompt = f"""
        Analyze the competitive position of {company_name} in the {sector} sector:
        
        Company Profile:
        - Market Cap: ${market_cap_billions:.1f}B
        - Sector: {sector}
        
        Provide analysis covering:
        1. Competitive positioning and market share
        2. Key competitive advantages and moats
        3. Main competitors and threats
        4. Industry trends and outlook
        
        Write 2-3 professional paragraphs.
        """
        
        analysis_text = self.generate_analysis(prompt)
        
        # Determine competitive strength based on market cap
        if market_cap_billions > 100:
            competitive_strength = 'strong'
        elif market_cap_billions > 10:
            competitive_strength = 'moderate'
        else:
            competitive_strength = 'weak'
        
        return {
            'analysis_text': analysis_text,
            'competitive_strength': competitive_strength,
            'market_position': 'leader' if market_cap_billions > 50 else 'follower'
        }

    def _generate_investment_thesis(self, clean_data: Dict) -> Dict:
        """Generate investment thesis."""
        company_overview = clean_data.get('company_overview', {})
        investment_scores = clean_data.get('investment_scores', {})
        
        company_name = company_overview.get('company_name', 'Unknown')
        overall_score = investment_scores.get('overall_investment_score', 0)
        
        prompt = f"""
        Develop a clear investment thesis for {company_name}:
        
        Investment Context:
        - Overall Investment Score: {overall_score:.1f}/100
        
        Create a compelling investment thesis covering:
        1. Core investment opportunity and value drivers
        2. Key catalysts for growth and performance
        3. Why this investment makes sense now
        4. Long-term value creation potential
        
        Write a strong, persuasive investment case in 3-4 paragraphs.
        """
        
        thesis_text = self.generate_analysis(prompt)
        
        return {
            'thesis_text': thesis_text,
            'investment_appeal': 'high' if overall_score > 70 else 'medium' if overall_score > 50 else 'low'
        }

    def _generate_risk_assessment(self, clean_data: Dict) -> Dict:
        """Generate risk assessment."""
        company_overview = clean_data.get('company_overview', {})
        financial_metrics = clean_data.get('financial_metrics', {})
        
        company_name = company_overview.get('company_name', 'Unknown')
        sector = company_overview.get('sector', 'Unknown')
        volatility = financial_metrics.get('volatility_percent', 0)
        
        prompt = f"""
        Assess investment risks for {company_name}:
        
        Risk Context:
        - Sector: {sector}
        - Volatility: {volatility:.1f}%
        
        Analyze key risks including:
        1. Company-specific operational risks
        2. Sector and industry risks
        3. Market and economic risks
        4. Risk mitigation factors
        
        Provide balanced risk assessment in 2-3 paragraphs.
        """
        
        risk_text = self.generate_analysis(prompt)
        
        risk_level = 'high' if volatility > 30 else 'medium' if volatility > 20 else 'low'
        
        return {
            'risk_text': risk_text,
            'overall_risk_level': risk_level,
            'volatility_risk': volatility
        }
    
    def _generate_recommendation(self, clean_data: Dict) -> Dict:
        """
        Generate final investment recommendation.
        
        Args:
            clean_data: Clean dataset from data cleaner
            
        Returns:
            Investment recommendation section
        """
        # Extract key data for recommendation
        investment_scores = clean_data.get('investment_scores', {})
        company_overview = clean_data.get('company_overview', {})
        
        overall_score = investment_scores.get('overall_investment_score', 0)
        recommendation = investment_scores.get('recommendation', 'HOLD')
        current_price = company_overview.get('current_price', 0)
        confidence_level = investment_scores.get('confidence_level', 'medium')
        
        # Calculate price target using enhanced logic
        price_target = self._calculate_price_target(clean_data)
        upside_potential = ((price_target - current_price) / current_price * 100) if current_price > 0 else 0
        
        # Create AI prompt
        prompt = f"""
        Provide final investment recommendation:
        
        Analysis Summary:
        - Overall Investment Score: {overall_score:.1f}/100
        - Current Recommendation: {recommendation}
        - Current Price: ${current_price:.2f}
        - Price Target: ${price_target:.2f}
        - Upside Potential: {upside_potential:.1f}%
        - Confidence Level: {confidence_level}
        
        Provide recommendation covering:
        1. Clear investment action (Buy/Hold/Sell) with rationale
        2. Price target methodology and rationale
        3. Key catalysts and expected timeline
        4. Risk considerations and position sizing
        5. Exit strategy considerations
        
        Write a comprehensive but concise recommendation.
        """
        
        # Generate recommendation
        recommendation_text = self.generate_analysis(prompt)
        
        return {
            'recommendation_text': recommendation_text,
            'action': recommendation,
            'current_price': current_price,
            'price_target': round(price_target, 2),
            'upside_potential': round(upside_potential, 1),
            'confidence_level': confidence_level,
            'timeline': '6-12 months',
            'overall_score': overall_score
        }

    def _calculate_price_target(self, clean_data: Dict) -> float:
        """Calculate price target based on multiple factors."""
        company_overview = clean_data.get('company_overview', {})
        investment_scores = clean_data.get('investment_scores', {})
        financial_metrics = clean_data.get('financial_metrics', {})
        
        current_price = company_overview.get('current_price', 0)
        overall_score = investment_scores.get('overall_investment_score', 0)
        momentum_score = financial_metrics.get('momentum_score', 0)
        
        # Base multiplier from overall score
        if overall_score > 80:
            multiplier = 1.20
        elif overall_score > 70:
            multiplier = 1.15
        elif overall_score > 60:
            multiplier = 1.10
        elif overall_score > 50:
            multiplier = 1.05
        elif overall_score > 40:
            multiplier = 1.00
        else:
            multiplier = 0.95
        
        # Adjust for momentum
        if momentum_score > 70:
            multiplier += 0.05
        elif momentum_score < 40:
            multiplier -= 0.05
        
        return round(current_price * multiplier, 2)

    def _calculate_overall_score(self, clean_data: Dict) -> float:
        """Calculate overall investment score."""
        investment_scores = clean_data.get('investment_scores', {})
        return investment_scores.get('overall_investment_score', 0)

    def _show_analysis_summary(self, analysis: Dict):
        """Show summary of generated analysis."""
        print(f"\n🎯 LLM ANALYSIS COMPLETE:")
        print(f"✅ Company: {analysis.get('company_name')} ({analysis.get('ticker')})")
        print(f"🤖 Backend: {analysis.get('model_used')}")
        print(f"📊 Overall Score: {analysis.get('overall_score', 0):.1f}/100")
        print(f"🎯 Recommendation: {analysis.get('recommendation', {}).get('action', 'HOLD')}")
        print(f"💰 Price Target: ${analysis.get('recommendation', {}).get('price_target', 0):.2f}")
        print(f"📈 Upside Potential: {analysis.get('recommendation', {}).get('upside_potential', 0):.1f}%")
        print(f"✅ Ready for LaTeX report generation!")