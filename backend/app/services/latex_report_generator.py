"""
LaTeX Report Generator for Investment Research
Converts LLM analysis into professional PDF reports using LaTeX
"""

import os
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class LaTeXReportGenerator:
    """
    Professional LaTeX report generator for investment research.
    
    Takes LLM analysis output and generates institutional-quality
    PDF reports that look like Goldman Sachs or JPMorgan research.
    
    Features:
    - Professional document layout
    - Custom styling and branding
    - Financial tables and metrics
    - Executive summary format
    - Risk assessment sections
    """
    
    def __init__(self, output_dir: str = "./reports"):
        """
        Initialize the LaTeX report generator.
        
        Args:
            output_dir: Directory to save generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # LaTeX template configuration
        self.latex_config = {
            'document_class': 'article',
            'font_size': '11pt',
            'paper_size': 'letterpaper',
            'margins': '1in',
            'line_spacing': '1.2'
        }
        
        # Report styling
        self.style_config = {
            'primary_color': '0.2,0.4,0.6',  # RGB for blue headers
            'secondary_color': '0.8,0.8,0.8',  # RGB for light gray
            'accent_color': '0.0,0.6,0.0',  # RGB for green (positive)
            'warning_color': '0.8,0.2,0.0'  # RGB for red (negative)
        }
    
    def generate_report(self, llm_analysis: Dict, output_filename: Optional[str] = None, progress_callback=None) -> tuple[Optional[str], str]:
        """
        Generate complete investment research report.
        
        Args:
            llm_analysis: Output from InvestmentAnalysisAgent.analyze_investment()
            output_filename: Optional custom filename (without extension)
            progress_callback: Optional function to call with progress updates
            
        Returns:
            tuple: (pdf_path, tex_path) - pdf_path may be None if compilation fails
        """
        if progress_callback:
            progress_callback("Starting LaTeX report generation...")
        print("GENERATING LATEX INVESTMENT REPORT")
        print("="*60)
        
        company_name = llm_analysis.get('company_name', 'Unknown Company')
        ticker = llm_analysis.get('ticker', 'UNKNOWN')
        
        print(f"Report for: {company_name} ({ticker})")
        
        # Generate filename
        if not output_filename:
            date_str = datetime.now().strftime("%Y%m%d")
            output_filename = f"{ticker}_Investment_Research_{date_str}"
        
        if progress_callback:
            progress_callback("Creating LaTeX document structure...")
        
        # Create LaTeX document
        latex_content = self._create_latex_document(llm_analysis)
        
        if progress_callback:
            progress_callback("Saving LaTeX source file...")
        
        # Save LaTeX file (ALWAYS save this, regardless of PDF compilation success)
        tex_file = self.output_dir / f"{output_filename}.tex"
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        print(f"LaTeX source saved: {tex_file}")
        tex_path = str(tex_file)
        
        if progress_callback:
            progress_callback("Compiling LaTeX to PDF...")
        
        # Compile to PDF
        try:
            pdf_file = self._compile_to_pdf(tex_file)
            
            if pdf_file and pdf_file.exists():
                print(f"PDF report generated: {pdf_file}")
                print("Report contains: Executive Summary, Financial Analysis, Recommendations")
                if progress_callback:
                    progress_callback("PDF compilation successful!")
                return str(pdf_file), tex_path
            else:
                # Check if we have just warnings (PDF might still exist)
                potential_pdf = tex_file.with_suffix('.pdf')
                if potential_pdf.exists():
                    print("PDF exists despite compilation warnings - using it anyway")
                    if progress_callback:
                        progress_callback("PDF compilation completed with warnings")
                    return str(potential_pdf), tex_path
                else:
                    if progress_callback:
                        progress_callback("PDF compilation failed, but LaTeX source is available for download")
                    print("ERROR: PDF compilation failed!")
                    print(f"LaTeX source saved at: {tex_file}")
                    return None, tex_path
        except Exception as e:
            if progress_callback:
                progress_callback(f"PDF compilation failed: {str(e)}, but LaTeX source is available for download")
            print(f"ERROR: PDF compilation failed with exception: {e}")
            print(f"LaTeX source saved at: {tex_file}")
            return None, tex_path
    
    def _create_latex_document(self, analysis: Dict) -> str:
        """Create complete LaTeX document from analysis."""
        
        # Document header
        latex_doc = self._create_document_header()
        
        # Title page
        latex_doc += self._create_title_page(analysis)
        
        # Table of contents
        latex_doc += self._create_table_of_contents()
        
        # Executive summary
        latex_doc += self._create_executive_summary(analysis)
        
        # Financial analysis section
        latex_doc += self._create_financial_analysis_section(analysis)
        
        # Market sentiment section
        latex_doc += self._create_sentiment_analysis_section(analysis)
        
        # Competitive analysis section
        latex_doc += self._create_competitive_analysis_section(analysis)
        
        # Investment thesis section
        latex_doc += self._create_investment_thesis_section(analysis)
        
        # Risk assessment section
        latex_doc += self._create_risk_assessment_section(analysis)
        
        # Final recommendation section
        latex_doc += self._create_recommendation_section(analysis)
        
        # Appendix with detailed metrics
        latex_doc += self._create_appendix_section(analysis)
        
        # Document footer
        latex_doc += self._create_document_footer()
        
        return latex_doc
    
    def _create_document_header(self) -> str:
        """Create LaTeX document header with packages and styling."""
        return f"""\\documentclass[{self.latex_config['font_size']},{self.latex_config['paper_size']}]{{article}}

% Essential packages
\\usepackage[margin={self.latex_config['margins']}]{{geometry}}
\\usepackage{{amsmath,amsfonts,amssymb}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\usepackage{{array}}
\\usepackage{{longtable}}
\\usepackage{{xcolor}}
\\usepackage{{fancyhdr}}
\\usepackage{{titlesec}}
\\usepackage{{setspace}}
\\usepackage{{enumitem}}
\\usepackage{{hyperref}}
\\usepackage{{caption}}
\\usepackage{{float}}

% Custom colors
\\definecolor{{primarycolor}}{{rgb}}{{{self.style_config['primary_color']}}}
\\definecolor{{secondarycolor}}{{rgb}}{{{self.style_config['secondary_color']}}}
\\definecolor{{accentcolor}}{{rgb}}{{{self.style_config['accent_color']}}}
\\definecolor{{warningcolor}}{{rgb}}{{{self.style_config['warning_color']}}}

% Page styling
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[L]{{\\textcolor{{primarycolor}}{{Investment Research Report}}}}
\\fancyhead[R]{{\\textcolor{{primarycolor}}{{\\thepage}}}}
\\renewcommand{{\\headrulewidth}}{{0.5pt}}

% Section styling
\\titleformat{{\\section}}
  {{\\color{{primarycolor}}\\Large\\bfseries}}
  {{\\thesection}}
  {{1em}}
  {{}}
\\titleformat{{\\subsection}}
  {{\\color{{primarycolor}}\\large\\bfseries}}
  {{\\thesubsection}}
  {{1em}}
  {{}}

% Line spacing
\\setstretch{{{self.latex_config['line_spacing']}}}

% Hyperlink setup
\\hypersetup{{
    colorlinks=true,
    linkcolor=primarycolor,
    urlcolor=primarycolor,
    citecolor=primarycolor
}}

% Custom commands
\\newcommand{{\\recommendation}}[1]{{\\textcolor{{accentcolor}}{{\\textbf{{#1}}}}}}
\\newcommand{{\\risk}}[1]{{\\textcolor{{warningcolor}}{{\\textbf{{#1}}}}}}
\\newcommand{{\\metric}}[2]{{\\textbf{{#1:}} #2}}

\\begin{{document}}

"""
    
    def _create_title_page(self, analysis: Dict) -> str:
        """Create professional title page."""
        company_name = analysis.get('company_name', 'Unknown Company')
        ticker = analysis.get('ticker', 'UNKNOWN')
        analysis_date = analysis.get('analysis_timestamp', datetime.now().isoformat())[:10]
        recommendation = analysis.get('recommendation', {}).get('action', 'HOLD')
        price_target = analysis.get('recommendation', {}).get('price_target', 0)
        overall_score = analysis.get('overall_score', 0)
        
        return f"""
% Title Page
\\begin{{titlepage}}
\\centering

{{\\Huge\\textcolor{{primarycolor}}{{\\textbf{{Investment Research Report}}}}}}

\\vspace{{1cm}}

{{\\LARGE\\textbf{{{company_name}}}}}

{{\\Large\\textcolor{{primarycolor}}{{({ticker})}}}}

\\vspace{{1.5cm}}

\\begin{{tabular}}{{c}}
\\toprule
\\textbf{{Analysis Summary}} \\\\
\\midrule
\\metric{{Date}}{{{analysis_date}}} \\\\
\\metric{{Overall Score}}{{{overall_score:.1f}/100}} \\\\
\\metric{{Recommendation}}{{\\recommendation{{{recommendation}}}}} \\\\
\\metric{{Price Target}}{{\\${price_target:.2f}}} \\\\
\\bottomrule
\\end{{tabular}}

\\vspace{{2cm}}

{{\\large\\textcolor{{primarycolor}}{{\\textbf{{Professional Investment Analysis}}}}}}

\\vspace{{0.5cm}}

{{\\textit{{This report provides comprehensive analysis based on financial metrics, market sentiment, competitive positioning, and risk assessment.}}}}

\\vfill

{{\\large\\textcolor{{secondarycolor}}{{Generated on {datetime.now().strftime("%B %d, %Y")}}}}}

\\end{{titlepage}}

\\newpage

"""
    
    def _create_table_of_contents(self) -> str:
        """Create table of contents."""
        return """
% Table of Contents
\\tableofcontents
\\newpage

"""
    
    def _create_executive_summary(self, analysis: Dict) -> str:
        """Create executive summary section."""
        exec_summary = analysis.get('executive_summary', {})
        summary_text = exec_summary.get('summary_text', 'No executive summary available.')
        key_points = exec_summary.get('key_points', [])
        investment_thesis = exec_summary.get('investment_thesis', '')
        
        # Clean text for LaTeX
        summary_text = self._clean_latex_text(summary_text)
        investment_thesis = self._clean_latex_text(investment_thesis)
        
        key_points_latex = ""
        for point in key_points:
            clean_point = self._clean_latex_text(str(point))
            key_points_latex += f"\\item {clean_point}\n"
        
        # If no key points, add placeholder
        if not key_points_latex.strip():
            key_points_latex = "\\item Analysis of key investment points is incorporated in the executive summary above.\n"
        
        return f"""
\\section{{Executive Summary}}

{summary_text}

\\subsection{{Key Investment Points}}

\\begin{{itemize}}
{key_points_latex}
\\end{{itemize}}

\\subsection{{Investment Thesis}}

\\textit{{{investment_thesis}}}

\\newpage

"""
    
    def _create_financial_analysis_section(self, analysis: Dict) -> str:
        """Create financial analysis section."""
        financial = analysis.get('financial_analysis', {})
        analysis_text = self._clean_latex_text(financial.get('analysis_text', 'No financial analysis available.'))
        valuation = self._safe_title(financial.get('valuation_assessment', 'unknown'))
        momentum = self._safe_title(financial.get('momentum_trend', 'neutral'))
        strength = self._safe_title(financial.get('financial_strength', 'moderate'))
        key_metrics = financial.get('key_metrics', {})
        
        # Create metrics table
        metrics_table = "\\begin{table}[H]\n\\centering\n\\begin{tabular}{lr}\n\\toprule\n\\textbf{Metric} & \\textbf{Value} \\\\\n\\midrule\n"
        
        for metric, value in key_metrics.items():
            if isinstance(value, (int, float)):
                formatted_value = f"{value:.2f}"
            else:
                formatted_value = self._clean_latex_text(str(value))
            metric_name = self._clean_latex_text(metric.replace('_', ' ').title())
            metrics_table += f"{metric_name} & {formatted_value} \\\\\n"
        
        metrics_table += "\\bottomrule\n\\end{tabular}\n\\caption{{Key Financial Metrics}}\n\\end{table}\n"
        
        return f"""
\\section{{Financial Analysis}}

{analysis_text}

\\subsection{{Financial Metrics Summary}}

{metrics_table}

\\subsection{{Assessment Summary}}

\\begin{{itemize}}
\\item \\metric{{Valuation Assessment}}{{{valuation}}}
\\item \\metric{{Price Momentum}}{{{momentum}}}
\\item \\metric{{Financial Strength}}{{{strength}}}
\\end{{itemize}}

\\newpage

"""
    
    def _create_sentiment_analysis_section(self, analysis: Dict) -> str:
        """Create market sentiment analysis section."""
        sentiment = analysis.get('sentiment_analysis', {})
        analysis_text = self._clean_latex_text(sentiment.get('analysis_text', 'No sentiment analysis available.'))
        sentiment_score = sentiment.get('sentiment_score', 50)
        coverage_quality = self._safe_title(sentiment.get('coverage_quality', 'unknown'))
        key_themes = sentiment.get('key_themes', [])
        news_impact = self._safe_title(sentiment.get('news_impact', 'neutral'))
        
        themes_latex = ""
        for theme in key_themes:
            themes_latex += f"\\item {self._clean_latex_text(str(theme))}\n"
        
        # If no themes, add placeholder
        if not themes_latex.strip():
            themes_latex = "\\item No specific market themes identified in the current analysis.\n"
        
        return f"""
\\section{{Market Sentiment Analysis}}

{analysis_text}

\\subsection{{Sentiment Metrics}}

\\begin{{itemize}}
\\item \\metric{{Media Attention Score}}{{{sentiment_score:.1f}/100}}
\\item \\metric{{Coverage Quality}}{{{coverage_quality}}}
\\item \\metric{{News Impact}}{{{news_impact}}}
\\end{{itemize}}

\\subsection{{Key Market Themes}}

\\begin{{itemize}}
{themes_latex}
\\end{{itemize}}

\\newpage

"""
    
    def _create_competitive_analysis_section(self, analysis: Dict) -> str:
        """Create competitive analysis section."""
        competitive = analysis.get('competitive_analysis', {})
        analysis_text = self._clean_latex_text(competitive.get('analysis_text', 'No competitive analysis available.'))
        competitive_strength = self._safe_title(competitive.get('competitive_strength', 'moderate'))
        market_position = self._safe_title(competitive.get('market_position', 'unknown'))
        advantages = competitive.get('key_advantages', [])
        challenges = competitive.get('key_challenges', [])
        sector_ranking = self._safe_title(competitive.get('sector_ranking', 'unknown'))
        
        advantages_latex = ""
        for advantage in advantages:
            advantages_latex += f"\\item {self._clean_latex_text(str(advantage))}\n"
        
        # If no advantages, add placeholder
        if not advantages_latex.strip():
            advantages_latex = "\\item No specific competitive advantages identified in the analysis.\n"
        
        challenges_latex = ""
        for challenge in challenges:
            challenges_latex += f"\\item {self._clean_latex_text(str(challenge))}\n"
        
        # If no challenges, add placeholder
        if not challenges_latex.strip():
            challenges_latex = "\\item No major challenges identified in the analysis.\n"
        
        return f"""
\\section{{Competitive Analysis}}

{analysis_text}

\\subsection{{Competitive Position Summary}}

\\begin{{itemize}}
\\item \\metric{{Competitive Strength}}{{{competitive_strength}}}
\\item \\metric{{Market Position}}{{{market_position}}}
\\item \\metric{{Sector Ranking}}{{{sector_ranking}}}
\\end{{itemize}}

\\subsection{{Competitive Advantages}}

\\begin{{itemize}}
{advantages_latex}
\\end{{itemize}}

\\subsection{{Key Challenges}}

\\begin{{itemize}}
{challenges_latex}
\\end{{itemize}}

\\newpage

"""
    
    def _create_investment_thesis_section(self, analysis: Dict) -> str:
        """Create investment thesis section."""
        thesis = analysis.get('investment_thesis', {})
        thesis_text = self._clean_latex_text(thesis.get('thesis_text', 'No investment thesis available.'))
        investment_rationale = self._clean_latex_text(str(thesis.get('investment_rationale', '')))
        expected_timeline = self._clean_latex_text(str(thesis.get('expected_timeline', '6-12 months')))
        key_catalysts = thesis.get('key_catalysts', [])
        success_probability = self._safe_title(thesis.get('success_probability', 'medium'))
        
        catalysts_latex = ""
        for catalyst in key_catalysts:
            catalysts_latex += f"\\item {self._clean_latex_text(str(catalyst))}\n"
        
        # If no catalysts, add placeholder
        if not catalysts_latex.strip():
            catalysts_latex = "\\item Key investment catalysts are incorporated in the investment thesis above.\n"
        
        return f"""
\\section{{Investment Thesis}}

{thesis_text}

\\subsection{{Investment Framework}}

\\begin{{itemize}}
\\item \\metric{{Investment Rationale}}{{{investment_rationale}}}
\\item \\metric{{Expected Timeline}}{{{expected_timeline}}}
\\item \\metric{{Success Probability}}{{{success_probability}}}
\\end{{itemize}}

\\subsection{{Key Catalysts}}

\\begin{{itemize}}
{catalysts_latex}
\\end{{itemize}}

\\newpage

"""
    
    def _create_risk_assessment_section(self, analysis: Dict) -> str:
        """Create risk assessment section."""
        risk = analysis.get('risk_assessment', {})
        risk_text = self._clean_latex_text(risk.get('risk_analysis_text', 'No risk assessment available.'))
        overall_risk = self._safe_title(risk.get('overall_risk_level', 'medium'))
        primary_risks = risk.get('primary_risks', [])
        risk_mitigation = risk.get('risk_mitigation', [])
        volatility_risk = self._safe_title(risk.get('volatility_risk', 'medium'))
        
        risks_latex = ""
        for risk_item in primary_risks:
            risks_latex += f"\\item \\risk{{{self._clean_latex_text(str(risk_item))}}}\n"
        
        # If no specific risks, add placeholder
        if not risks_latex.strip():
            risks_latex = "\\item No specific risk factors identified beyond general market risks.\n"
        
        mitigation_latex = ""
        for mitigation in risk_mitigation:
            mitigation_latex += f"\\item {self._clean_latex_text(str(mitigation))}\n"
        
        # If no mitigation strategies, add placeholder
        if not mitigation_latex.strip():
            mitigation_latex = "\\item Standard portfolio diversification and position sizing recommended.\n"
        
        return f"""
\\section{{Risk Assessment}}

{risk_text}

\\subsection{{Risk Profile}}

\\begin{{itemize}}
\\item \\metric{{Overall Risk Level}}{{\\risk{{{overall_risk}}}}}
\\item \\metric{{Volatility Risk}}{{\\risk{{{volatility_risk}}}}}
\\end{{itemize}}

\\subsection{{Primary Risk Factors}}

\\begin{{itemize}}
{risks_latex}
\\end{{itemize}}

\\subsection{{Risk Mitigation Strategies}}

\\begin{{itemize}}
{mitigation_latex}
\\end{{itemize}}

\\newpage

"""
    
    def _create_recommendation_section(self, analysis: Dict) -> str:
        """Create final recommendation section."""
        recommendation = analysis.get('recommendation', {})
        recommendation_text = self._clean_latex_text(recommendation.get('recommendation_text', 'No recommendation available.'))
        action = self._clean_latex_text(str(recommendation.get('action', 'HOLD')))
        current_price = float(recommendation.get('current_price', 0))
        price_target = float(recommendation.get('price_target', 0))
        upside_potential = float(recommendation.get('upside_potential', 0))
        timeline = self._clean_latex_text(str(recommendation.get('timeline', '6-12 months')))
        conviction_level = self._safe_title(recommendation.get('conviction_level', 'medium'))
        
        return f"""
\\section{{Investment Recommendation}}

{recommendation_text}

\\subsection{{Recommendation Summary}}

\\begin{{table}}[H]
\\centering
\\begin{{tabular}}{{lr}}
\\toprule
\\textbf{{Metric}} & \\textbf{{Value}} \\\\
\\midrule
Action & \\recommendation{{{action}}} \\\\
Current Price & \\${current_price:.2f} \\\\
Price Target & \\${price_target:.2f} \\\\
Upside Potential & {upside_potential:.1f}\\% \\\\
Timeline & {timeline} \\\\
Conviction Level & {conviction_level} \\\\
\\bottomrule
\\end{{tabular}}
\\caption{{Investment Recommendation Summary}}
\\end{{table}}

\\newpage

"""
    
    def _create_appendix_section(self, analysis: Dict) -> str:
        """Create appendix with detailed metrics."""
        overall_score = float(analysis.get('overall_score', 0))
        confidence_level = self._safe_title(analysis.get('confidence_level', 'medium'))
        analysis_quality = self._safe_title(analysis.get('analysis_quality', 'medium'))
        model_used = self._clean_latex_text(str(analysis.get('model_used', 'unknown')))
        
        return f"""
\\section{{Appendix}}

\\subsection{{Analysis Methodology}}

This investment research report was generated using a comprehensive analytical framework that incorporates:

\\begin{{itemize}}
\\item Financial metrics analysis and valuation assessment
\\item Market sentiment analysis from news and social media sources
\\item Competitive positioning within sector peer group
\\item Risk assessment covering multiple risk factors
\\item Quantitative scoring methodology for objective evaluation
\\end{{itemize}}

\\subsection{{Analysis Quality Metrics}}

\\begin{{table}}[H]
\\centering
\\begin{{tabular}}{{lr}}
\\toprule
\\textbf{{Quality Metric}} & \\textbf{{Assessment}} \\\\
\\midrule
Overall Score & {overall_score:.1f}/100 \\\\
Analysis Quality & {analysis_quality} \\\\
Confidence Level & {confidence_level} \\\\
Model Used & {model_used} \\\\
\\bottomrule
\\end{{tabular}}
\\caption{{Analysis Quality Assessment}}
\\end{{table}}

\\subsection{{Disclaimer}}

\\textit{{This report is for informational purposes only and should not be considered as investment advice. Past performance does not guarantee future results. Please consult with a qualified financial advisor before making investment decisions.}}

"""
    
    def _create_document_footer(self) -> str:
        """Create document footer."""
        return """
\\end{document}
"""
    
    def _clean_latex_text(self, text: str) -> str:
        """Clean text for LaTeX compilation by escaping special characters."""
        if not text:
            return ""
        
        # Convert to string first
        cleaned_text = str(text)
        
        # Step 1: Handle markdown-style formatting BEFORE escaping
        import re
        
        # Convert markdown headers to LaTeX sections first (to avoid # escaping issues)
        cleaned_text = re.sub(r'####\s*(.*?)(?=\n|$)', r'\\subsubsection{\1}', cleaned_text, flags=re.MULTILINE)
        cleaned_text = re.sub(r'###\s*(.*?)(?=\n|$)', r'\\subsection{\1}', cleaned_text, flags=re.MULTILINE)
        cleaned_text = re.sub(r'##\s*(.*?)(?=\n|$)', r'\\subsection{\1}', cleaned_text, flags=re.MULTILINE)
        cleaned_text = re.sub(r'#\s*(.*?)(?=\n|$)', r'\\section{\1}', cleaned_text, flags=re.MULTILINE)
        
        # Convert markdown horizontal rules to LaTeX
        cleaned_text = re.sub(r'^---+\s*$', r'\\hrule', cleaned_text, flags=re.MULTILINE)
        
        # Step 2: Protect existing LaTeX commands FIRST (before adding new ones)
        protected_commands = []
        
        # Find all existing LaTeX commands (starting with backslash)
        latex_command_pattern = r'\\[a-zA-Z]+(?:\{[^}]*\})?'
        for match in re.finditer(latex_command_pattern, cleaned_text):
            placeholder = f"XXXLATEXCMDXXX{len(protected_commands)}XXXLATEXCMDXXX"
            protected_commands.append(match.group())
            cleaned_text = cleaned_text.replace(match.group(), placeholder, 1)
        
        # Step 2b: Now safely convert **text** to \textbf{text} for bold
        # This is done after protecting existing commands to avoid conflicts
        # Use non-greedy matching and exclude line breaks to avoid paragraph issues
        cleaned_text = re.sub(r'\*\*([^*\n]+?)\*\*', r'\\textbf{\1}', cleaned_text)
        
        # Step 3: Escape special characters (but NOT backslashes since we protected commands)
        latex_replacements = [
            # Note: We don't escape backslashes here to avoid interfering with LaTeX commands
            ('{', '\\{'),
            ('}', '\\}'),
            ('$', '\\$'),
            ('&', '\\&'),
            ('%', '\\%'),
            ('#', '\\#'),
            ('^', '\\textasciicircum{}'),
            ('_', '\\_'),
            ('~', '\\textasciitilde{}'),
        ]
        
        # Apply replacements
        for char, replacement in latex_replacements:
            cleaned_text = cleaned_text.replace(char, replacement)
        
        # Step 4: Restore protected LaTeX commands
        for i, command in enumerate(protected_commands):
            placeholder = f"XXXLATEXCMDXXX{i}XXXLATEXCMDXXX"
            cleaned_text = cleaned_text.replace(placeholder, command)
        
        # Step 5: Final cleanup - ensure no unmatched braces for \textbf commands
        # Find any incomplete \textbf commands and remove them
        cleaned_text = re.sub(r'\\textbf\s*$', '', cleaned_text)  # Remove trailing \textbf
        cleaned_text = re.sub(r'\\textbf\s+(?![{])', '\\textbf{} ', cleaned_text)  # Fix \textbf without opening brace
        
        return cleaned_text
    def _safe_title(self, value) -> str:
        """Safely convert value to title case string."""
        if value is None:
            return "Unknown"
        
        # Convert to string first
        str_value = str(value)
        
        # Replace underscores with spaces and apply title case
        return str_value.replace('_', ' ').title()
    
    def _compile_to_pdf(self, tex_file: Path) -> Optional[Path]:
        """Compile LaTeX file to PDF."""
        try:
            print("Compiling LaTeX to PDF...")
            
            # Change to the output directory for compilation
            original_cwd = os.getcwd()
            os.chdir(self.output_dir)
            
            # Run pdflatex twice for proper cross-references
            for i in range(2):
                result = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', tex_file.name],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    print(f"LaTeX compilation failed on pass {i+1}")
                    print(f"Return code: {result.returncode}")
                    if result.stdout:
                        print(f"STDOUT:\n{result.stdout}")
                    if result.stderr:
                        print(f"STDERR:\n{result.stderr}")
                    
                    # Save the error log for debugging
                    log_file = tex_file.with_suffix('.log')
                    if log_file.exists():
                        print(f"\nLaTeX log file content:")
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            log_content = f.read()
                            # Show last 50 lines of log which usually contain the error
                            log_lines = log_content.split('\n')
                            print('\n'.join(log_lines[-50:]))
                    
                    os.chdir(original_cwd)
                    return None
            
            # Check if PDF was created (while still in output directory)
            pdf_filename = tex_file.stem + '.pdf'
            pdf_file_in_output = Path(pdf_filename)  # Just filename, relative to current dir
            
            print(f"DEBUG: Checking for PDF: {pdf_file_in_output.absolute()}")
            print(f"DEBUG: Current directory: {os.getcwd()}")
            print(f"DEBUG: PDF exists check: {pdf_file_in_output.exists()}")
            
            # Also check if file was created but with compilation warnings
            if pdf_file_in_output.exists():
                file_size = pdf_file_in_output.stat().st_size
                print(f"PDF compiled successfully: {pdf_file_in_output.absolute()} ({file_size} bytes)")
                # Return to original directory
                os.chdir(original_cwd)
                # Return the full path to the PDF
                return self.output_dir / pdf_filename
            else:
                print("PDF file not found after compilation")
                print(f"Expected: {pdf_file_in_output.absolute()}")
                
                # List all files in current directory for debugging
                import glob
                all_files = glob.glob("*.*")
                print(f"DEBUG: Files in current directory: {all_files}")
                
                # Return to original directory
                os.chdir(original_cwd)
                return None
                
        except subprocess.TimeoutExpired:
            print("LaTeX compilation timed out")
            os.chdir(original_cwd)
            return None
        except FileNotFoundError:
            print(f"WARNING: pdflatex not found. Install LaTeX distribution (e.g., MiKTeX, TeX Live)")
            print(f"   LaTeX source file saved: {tex_file}")
            os.chdir(original_cwd)
            return None
        except Exception as e:
            print(f"WARNING: Error during PDF compilation: {e}")
            os.chdir(original_cwd)
            return None
    
    def inspect_sections(self, analysis_data: Dict) -> None:
        """Inspect each section's input data and LaTeX output."""
        print("\nINFO: LaTeX Section Inspector")
        print("=" * 80)
        
        sections = [
            ("Executive Summary", "executive_summary", self._create_executive_summary),
            ("Financial Analysis", "financial_analysis", self._create_financial_analysis_section),
            ("Sentiment Analysis", "sentiment_analysis", self._create_sentiment_analysis_section),
            ("Competitive Analysis", "competitive_analysis", self._create_competitive_analysis_section),
            ("Investment Thesis", "investment_thesis", self._create_investment_thesis_section),
            ("Risk Assessment", "risk_assessment", self._create_risk_assessment_section),
            ("Recommendation", "recommendation", self._create_recommendation_section),
            ("Appendix", "appendix", self._create_appendix_section)
        ]
        
        for section_name, data_key, section_method in sections:
            print(f"\n{'='*60}")
            print(f"SECTION: {section_name}")
            print(f"{'='*60}")
            
            # Show input data
            if data_key in analysis_data:
                print(f"\nINPUT DATA ({data_key}):")
                print("-" * 40)
                section_data = analysis_data[data_key]
                for key, value in section_data.items():
                    if isinstance(value, list):
                        print(f"  {key}: {len(value)} items")
                        for i, item in enumerate(value):
                            print(f"    [{i}] {item}")
                    elif isinstance(value, dict):
                        print(f"  {key}: {len(value)} metrics")
                        for k, v in value.items():
                            print(f"    {k}: {v}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print(f"\nINPUT DATA: Using default values (no {data_key} in analysis)")
            
            # Show LaTeX output
            print(f"\nGENERATED LATEX:")
            print("-" * 40)
            try:
                latex_output = section_method(analysis_data)
                # Show first 500 chars to avoid overwhelming output
                if len(latex_output) > 500:
                    print(latex_output[:500] + "\n... (truncated)")
                    print(f"Full length: {len(latex_output)} characters")
                else:
                    print(latex_output)
                    
                # Save to file
                filename = f"debug_{data_key}.tex"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(latex_output)
                print(f"INFO: Full output saved to: {filename}")
                
            except Exception as e:
                print(f"ERROR: Error generating section: {e}")
                import traceback
                traceback.print_exc()
    
    def create_sample_report(self) -> str:
        """Create a sample report for testing purposes."""
        sample_analysis = {
            'company_name': 'Apple Inc.',
            'ticker': 'AAPL',
            'analysis_timestamp': datetime.now().isoformat(),
            'overall_score': 78.5,
            'confidence_level': 'high',
            'analysis_quality': 'high',
            'model_used': 'sample_analysis',
            'executive_summary': {
                'summary_text': 'Apple Inc. represents a compelling investment opportunity with strong fundamentals and market position. The company continues to demonstrate innovation leadership and financial strength.',
                'key_points': ['Market leader in technology sector', 'Strong financial performance', 'Innovative product portfolio'],
                'investment_thesis': 'BUY recommendation based on comprehensive analysis'
            },
            'financial_analysis': {
                'analysis_text': 'Apple shows robust financial metrics with consistent revenue growth and strong profitability. The company maintains healthy cash flows and demonstrates efficient capital allocation.',
                'valuation_assessment': 'fair',
                'momentum_trend': 'positive',
                'financial_strength': 'strong',
                'key_metrics': {'pe_ratio': 28.5, 'volatility': 22.3, 'momentum_score': 75.2, 'stability_score': 82.1}
            },
            'sentiment_analysis': {
                'analysis_text': 'Market sentiment remains positive with strong media coverage and analyst support. Recent product launches have been well-received by consumers and investors.',
                'sentiment_score': 72.5,
                'coverage_quality': 'high',
                'key_themes': ['Product Innovation', 'Market Expansion', 'Financial Performance'],
                'news_impact': 'positive'
            },
            'competitive_analysis': {
                'analysis_text': 'Apple maintains strong competitive positioning with significant market share and brand loyalty. The company continues to differentiate through innovation and ecosystem integration.',
                'competitive_strength': 'strong',
                'market_position': 'market_leader',
                'key_advantages': ['Brand Recognition', 'Innovation Leadership', 'Ecosystem Integration'],
                'key_challenges': ['Market Saturation', 'Regulatory Pressure'],
                'sector_ranking': 'top_quartile'
            },
            'investment_thesis': {
                'thesis_text': 'Our investment thesis is based on Apple\'s continued innovation leadership, strong financial performance, and expanding market opportunities in services and emerging technologies.',
                'investment_rationale': 'Strong fundamentals with attractive growth prospects',
                'expected_timeline': '6-12 months',
                'key_catalysts': ['New Product Launches', 'Services Growth', 'Market Expansion'],
                'success_probability': 'high'
            },
            'risk_assessment': {
                'risk_analysis_text': 'Primary risks include market volatility, competitive pressure, and regulatory challenges. However, these risks are mitigated by strong fundamentals and market position.',
                'overall_risk_level': 'medium',
                'primary_risks': ['Market Volatility', 'Competitive Pressure', 'Regulatory Risk'],
                'risk_mitigation': ['Diversification', 'Strong Balance Sheet', 'Innovation Pipeline'],
                'volatility_risk': 'medium'
            },
            'recommendation': {
                'recommendation_text': 'We recommend a BUY rating with a price target based on discounted cash flow analysis and peer comparison methodology.',
                'action': 'BUY',
                'current_price': 185.50,
                'price_target': 205.00,
                'upside_potential': 10.5,
                'timeline': '6-12 months',
                'conviction_level': 'high'
            }
        }
        
        return self.generate_report(sample_analysis, "Sample_Investment_Report") 