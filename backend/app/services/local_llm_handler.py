"""
Local LLM Handler using Hugging Face Transformers
Provides 100% free AI analysis without external API dependencies
"""

import os
import torch
from typing import Dict, List, Optional, Union
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    pipeline,
    BitsAndBytesConfig
)
import warnings

# Suppress transformers warnings
warnings.filterwarnings("ignore", category=UserWarning)

class LocalLLMHandler:
    """
    Local LLM handler using Hugging Face models for investment analysis.
    
    Provides completely free AI analysis without external API costs.
    Supports multiple open-source models optimized for different hardware configurations.
    
    Features:
    - Multiple model support (Phi-3, Mistral, Zephyr)
    - Automatic quantization for memory efficiency
    - GPU acceleration when available
    - CPU fallback for compatibility
    """
    
    def __init__(self, model_name: str = "microsoft/Phi-3-mini-4k-instruct", device: str = "auto"):
        """
        Initialize local LLM handler.
        
        Args:
            model_name: Hugging Face model name
            device: Device to run on ('auto', 'cpu', 'cuda')
        """
        self.model_name = model_name
        self.device = self._setup_device(device)
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        
        # Model configurations
        self.model_configs = {
            "microsoft/Phi-3-mini-4k-instruct": {
                "max_length": 3072,
                "temperature": 0.3,
                "description": "Microsoft Phi-3 Mini - Efficient and capable"
            },
            "mistralai/Mistral-7B-Instruct-v0.1": {
                "max_length": 4096,
                "temperature": 0.3,
                "description": "Mistral 7B - Excellent instruction following"
            },
            "HuggingFaceH4/zephyr-7b-beta": {
                "max_length": 4096,
                "temperature": 0.3,
                "description": "Zephyr 7B - Great for structured analysis"
            },
            "microsoft/DialoGPT-medium": {
                "max_length": 1024,
                "temperature": 0.4,
                "description": "DialoGPT Medium - Lightweight option"
            }
        }
        
        print(f"🤖 Initializing Local LLM: {model_name}")
        print(f"📱 Device: {self.device}")
        
    def _setup_device(self, device: str) -> str:
        """Setup computation device."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"  # Apple Silicon
            else:
                return "cpu"
        return device
    
    def load_model(self, use_quantization: bool = True):
        """
        Load the model and tokenizer.
        
        Args:
            use_quantization: Whether to use 4-bit quantization to save memory
        """
        try:
            print(f"🔄 Loading model: {self.model_name}")
            
            # Setup quantization for memory efficiency
            quantization_config = None
            if use_quantization and self.device == "cuda":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                print(f"⚡ Using 4-bit quantization for memory efficiency")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                padding_side="left"
            )
            
            # Add pad token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            model_kwargs = {
                "trust_remote_code": True,
                "torch_dtype": torch.float16 if self.device != "cpu" else torch.float32,
            }
            
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config
            else:
                model_kwargs["device_map"] = self.device
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            # Create text generation pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map="auto" if self.device != "cpu" else None,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            )
            
            print(f"✅ Model loaded successfully on {self.device}")
            
            # Show model info
            config = self.model_configs.get(self.model_name, {})
            print(f"📊 Model: {config.get('description', 'Local LLM')}")
            print(f"🔧 Max Length: {config.get('max_length', 2048)} tokens")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print(f"💡 Try a smaller model or enable quantization")
            raise
    
    def generate_analysis(self, prompt: str, max_length: int = None, temperature: float = None) -> str:
        """
        Generate text analysis using the local model.
        
        Args:
            prompt: Input prompt for analysis
            max_length: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated analysis text
        """
        if self.pipeline is None:
            self.load_model()
        
        # Get model-specific config
        config = self.model_configs.get(self.model_name, {})
        max_length = max_length or config.get("max_length", 2048)
        temperature = temperature or config.get("temperature", 0.3)
        
        # Format prompt for instruction-following models
        formatted_prompt = self._format_prompt(prompt)
        
        try:
            # Generate response
            response = self.pipeline(
                formatted_prompt,
                max_length=max_length,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                return_full_text=False,
                num_return_sequences=1
            )
            
            # Extract generated text
            generated_text = response[0]['generated_text']
            
            # Clean up the response
            cleaned_text = self._clean_response(generated_text)
            
            return cleaned_text
            
        except Exception as e:
            print(f"❌ Error generating text: {e}")
            return f"Error generating analysis: {str(e)}"
    
    def _format_prompt(self, prompt: str) -> str:
        """Format prompt for different model types."""
        
        # Phi-3 format
        if "Phi-3" in self.model_name:
            return f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
        
        # Mistral format
        elif "Mistral" in self.model_name:
            return f"<s>[INST] {prompt} [/INST]"
        
        # Zephyr format
        elif "zephyr" in self.model_name:
            return f"<|system|>\nYou are a professional investment analyst.<|user|>\n{prompt}<|assistant|>\n"
        
        # Default format
        else:
            return f"### Instruction:\n{prompt}\n\n### Response:\n"
    
    def _clean_response(self, text: str) -> str:
        """Clean and format the model response."""
        # Remove common artifacts
        text = text.strip()
        
        # Remove instruction tokens that might leak through
        cleanup_tokens = [
            "<|end|>", "<|user|>", "<|assistant|>", "<|system|>",
            "[INST]", "[/INST]", "<s>", "</s>",
            "### Instruction:", "### Response:"
        ]
        
        for token in cleanup_tokens:
            text = text.replace(token, "")
        
        # Clean up extra whitespace
        text = " ".join(text.split())
        
        return text
    
    def analyze_investment_section(self, section_type: str, data: Dict, context: str = "") -> str:
        """
        Generate investment analysis for a specific section.
        
        Args:
            section_type: Type of analysis (executive_summary, financial, etc.)
            data: Relevant data for analysis
            context: Additional context
            
        Returns:
            Generated analysis text
        """
        prompts = {
            "executive_summary": f"""As a professional investment analyst, write a concise executive summary for this investment opportunity.

Company Data: {str(data)[:500]}
{context}

Provide a professional 2-paragraph executive summary focusing on:
1. Company overview and market position
2. Key investment highlights and recommendation rationale

Keep it concise and professional.""",

            "financial_analysis": f"""Analyze the financial performance and valuation metrics for this investment.

Financial Data: {str(data)[:500]}
{context}

Provide analysis covering:
1. Valuation assessment (attractive/fair/expensive)
2. Financial strength and performance trends
3. Key metrics interpretation

Write 2-3 paragraphs with specific insights.""",

            "sentiment_analysis": f"""Analyze the market sentiment and news coverage for this stock.

Market Data: {str(data)[:500]}
{context}

Analyze:
1. Overall media sentiment and coverage quality
2. Key themes and market perception
3. Impact on investor sentiment

Write 2 paragraphs on market sentiment.""",

            "competitive_analysis": f"""Analyze the competitive position and market standing.

Competitive Data: {str(data)[:500]}
{context}

Assess:
1. Market position within sector
2. Key competitive advantages and differentiators
3. Areas of competitive weakness

Write 2-3 paragraphs on competitive positioning.""",

            "investment_thesis": f"""Develop a clear investment thesis based on this analysis.

Investment Data: {str(data)[:500]}
{context}

Create an investment thesis covering:
1. Core investment rationale
2. Key supporting factors
3. Expected timeline and catalysts

Write a compelling 2-3 paragraph thesis.""",

            "risk_assessment": f"""Conduct a comprehensive risk assessment for this investment.

Risk Data: {str(data)[:500]}
{context}

Identify and analyze:
1. Primary risk factors
2. Market and sector risks
3. Risk mitigation strategies

Write 2-3 paragraphs on investment risks.""",

            "recommendation": f"""Provide a final investment recommendation with clear rationale.

Analysis Data: {str(data)[:500]}
{context}

Provide:
1. Clear recommendation (Strong Buy/Buy/Hold/Sell)
2. Price target rationale
3. Key conditions and timeline

Write a concise but comprehensive recommendation."""
        }
        
        prompt = prompts.get(section_type, f"Analyze this investment data: {str(data)[:500]}")
        
        return self.generate_analysis(prompt, max_length=512)
    
    def test_model(self) -> bool:
        """Test if the model is working correctly."""
        try:
            test_prompt = "Explain what makes a good investment in 2 sentences."
            response = self.generate_analysis(test_prompt, max_length=100)
            
            if len(response) > 10:  # Basic sanity check
                print(f"✅ Model test successful")
                print(f"   Sample output: {response[:100]}...")
                return True
            else:
                print(f"⚠️  Model test failed - output too short")
                return False
                
        except Exception as e:
            print(f"❌ Model test failed: {e}")
            return False
    
    @staticmethod
    def list_recommended_models() -> Dict[str, Dict]:
        """List recommended models with their characteristics."""
        return {
            "microsoft/Phi-3-mini-4k-instruct": {
                "size": "3.8B parameters",
                "memory": "~4GB RAM",
                "speed": "Fast",
                "quality": "High",
                "recommended_for": "Most users - best balance of performance and efficiency"
            },
            "mistralai/Mistral-7B-Instruct-v0.1": {
                "size": "7B parameters", 
                "memory": "~8GB RAM",
                "speed": "Medium",
                "quality": "Very High",
                "recommended_for": "Users with more RAM - excellent analysis quality"
            },
            "HuggingFaceH4/zephyr-7b-beta": {
                "size": "7B parameters",
                "memory": "~8GB RAM", 
                "speed": "Medium",
                "quality": "Very High",
                "recommended_for": "Structured analysis and instruction following"
            },
            "microsoft/DialoGPT-medium": {
                "size": "355M parameters",
                "memory": "~2GB RAM",
                "speed": "Very Fast",
                "quality": "Good",
                "recommended_for": "Low-resource environments"
            }
        }
    
    def get_model_info(self) -> Dict:
        """Get information about the current model."""
        config = self.model_configs.get(self.model_name, {})
        return {
            "model_name": self.model_name,
            "device": self.device,
            "description": config.get("description", "Local LLM"),
            "max_length": config.get("max_length", 2048),
            "temperature": config.get("temperature", 0.3),
            "loaded": self.model is not None
        } 