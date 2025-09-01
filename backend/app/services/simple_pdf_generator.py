"""
Simple PDF Generator for Investment Research Reports
Uses ReportLab to create professional PDFs without LaTeX dependency
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class SimplePDFGenerator:
    """
    Simple PDF report generator using ReportLab.
    Fallback when LaTeX is not available.
    """
    
    def __init__(self, output_dir: str = "backend/reports"):
        """Initialize the PDF generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_report(self, llm_analysis: Dict[str, Any], output_filename: Optional[str] = None) -> str:
        """
        Generate investment research report as PDF.
        
        Args:
            llm_analysis: Analysis data from LLM
            output_filename: Optional custom filename
            
        Returns:
            Path to generated PDF file
        """
        print("GENERATING PDF INVESTMENT REPORT")
        print("="*60)
        
        company_name = llm_analysis.get('company_name', 'Unknown Company')
        ticker = llm_analysis.get('ticker', 'UNKNOWN')
        
        print(f"Report for: {company_name} ({ticker})")
        
        # Generate filename
        if not output_filename:
            date_str = datetime.now().strftime("%Y%m%d")
            output_filename = f"{ticker}_Investment_Research_{date_str}"
        
        pdf_file = self.output_dir / f"{output_filename}.pdf"
        
        if REPORTLAB_AVAILABLE:
            self._create_reportlab_pdf(llm_analysis, pdf_file)
        else:
            self._create_text_pdf(llm_analysis, pdf_file)
        
        print(f"PDF report generated: {pdf_file}")
        return str(pdf_file)
    
    def _create_reportlab_pdf(self, analysis: Dict[str, Any], pdf_file: Path):
        """Create PDF using ReportLab."""
        doc = SimpleDocTemplate(str(pdf_file), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Center
        )
        
        company_name = analysis.get('company_name', 'Unknown Company')
        ticker = analysis.get('ticker', 'UNKNOWN')
        
        story.append(Paragraph("INVESTMENT RESEARCH REPORT", title_style))
        story.append(Paragraph(f"{company_name} ({ticker})", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Date
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"Generated: {date_str}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", styles['Heading2']))
        
        exec_summary = analysis.get('executive_summary', {})
        summary_text = exec_summary.get('summary_text', 'Analysis summary not available.')
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Key Points
        key_points = exec_summary.get('key_points', [])
        if key_points:
            story.append(Paragraph("Key Points:", styles['Heading3']))
            for point in key_points:
                story.append(Paragraph(f"• {point}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Financial Analysis
        financial = analysis.get('financial_analysis', {})
        if financial:
            story.append(Paragraph("FINANCIAL ANALYSIS", styles['Heading2']))
            financial_text = financial.get('analysis_text', 'Financial analysis not available.')
            story.append(Paragraph(financial_text, styles['Normal']))
            
            # Key Metrics Table
            metrics = financial.get('key_metrics', {})
            if metrics:
                story.append(Spacer(1, 12))
                story.append(Paragraph("Key Financial Metrics:", styles['Heading3']))
                
                # Create table data
                table_data = [['Metric', 'Value']]
                for key, value in metrics.items():
                    formatted_key = key.replace('_', ' ').title()
                    if isinstance(value, (int, float)):
                        formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                    else:
                        formatted_value = str(value)
                    table_data.append([formatted_key, formatted_value])
                
                table = Table(table_data, colWidths=[2.5*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
            story.append(Spacer(1, 20))
        
        # Recommendation
        recommendation = analysis.get('recommendation', {})
        if recommendation:
            story.append(Paragraph("INVESTMENT RECOMMENDATION", styles['Heading2']))
            
            rec_text = recommendation.get('recommendation_text', 'No recommendation available.')
            story.append(Paragraph(rec_text, styles['Normal']))
            
            # Recommendation details
            overall_rec = recommendation.get('overall_recommendation', 'N/A')
            price_target = recommendation.get('price_target', 'N/A')
            
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>Recommendation:</b> {overall_rec}", styles['Normal']))
            story.append(Paragraph(f"<b>Price Target:</b> ${price_target}", styles['Normal']))
        
        # Risk Assessment
        risk = analysis.get('risk_assessment', {})
        if risk:
            story.append(Spacer(1, 20))
            story.append(Paragraph("RISK ASSESSMENT", styles['Heading2']))
            
            risk_text = risk.get('risk_analysis_text', 'Risk analysis not available.')
            story.append(Paragraph(risk_text, styles['Normal']))
            
            risk_level = risk.get('overall_risk_level', 'N/A')
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>Overall Risk Level:</b> {risk_level.upper()}", styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1  # Center
        )
        story.append(Paragraph("Generated by AI Investment Research Platform", footer_style))
        
        # Build PDF
        doc.build(story)
        print("PDF created using ReportLab")
    
    def _create_text_pdf(self, analysis: Dict[str, Any], pdf_file: Path):
        """Create simple text-based PDF when ReportLab is not available."""
        content = self._generate_text_report(analysis)
        
        with open(pdf_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Text-based PDF created (ReportLab not available)")
    
    def _generate_text_report(self, analysis: Dict[str, Any]) -> str:
        """Generate text-based report content."""
        company_name = analysis.get('company_name', 'Unknown Company')
        ticker = analysis.get('ticker', 'UNKNOWN')
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
INVESTMENT RESEARCH REPORT
==========================

Company: {company_name} ({ticker})
Generated: {date_str}

EXECUTIVE SUMMARY
-----------------
"""
        
        # Add executive summary
        exec_summary = analysis.get('executive_summary', {})
        summary_text = exec_summary.get('summary_text', 'Analysis summary not available.')
        report += f"{summary_text}\n\n"
        
        # Add key points
        key_points = exec_summary.get('key_points', [])
        if key_points:
            report += "Key Points:\n"
            for point in key_points:
                report += f"• {point}\n"
            report += "\n"
        
        # Add financial analysis
        financial = analysis.get('financial_analysis', {})
        if financial:
            report += "FINANCIAL ANALYSIS\n"
            report += "------------------\n"
            financial_text = financial.get('analysis_text', 'Financial analysis not available.')
            report += f"{financial_text}\n\n"
            
            # Add metrics
            metrics = financial.get('key_metrics', {})
            if metrics:
                report += "Key Financial Metrics:\n"
                for key, value in metrics.items():
                    formatted_key = key.replace('_', ' ').title()
                    report += f"• {formatted_key}: {value}\n"
                report += "\n"
        
        # Add recommendation
        recommendation = analysis.get('recommendation', {})
        if recommendation:
            report += "INVESTMENT RECOMMENDATION\n"
            report += "-------------------------\n"
            rec_text = recommendation.get('recommendation_text', 'No recommendation available.')
            report += f"{rec_text}\n\n"
            
            overall_rec = recommendation.get('overall_recommendation', 'N/A')
            price_target = recommendation.get('price_target', 'N/A')
            
            report += f"Recommendation: {overall_rec}\n"
            report += f"Price Target: ${price_target}\n\n"
        
        # Add risk assessment
        risk = analysis.get('risk_assessment', {})
        if risk:
            report += "RISK ASSESSMENT\n"
            report += "---------------\n"
            risk_text = risk.get('risk_analysis_text', 'Risk analysis not available.')
            report += f"{risk_text}\n\n"
            
            risk_level = risk.get('overall_risk_level', 'N/A')
            report += f"Overall Risk Level: {risk_level.upper()}\n\n"
        
        report += "\n" + "="*50 + "\n"
        report += "Generated by AI Investment Research Platform\n"
        
        return report
