"""PDF generation and styling for resumes."""

import os
from pathlib import Path
from typing import Dict
import markdown

# Fix library path for weasyprint on macOS
if os.name == 'posix' and os.uname().sysname == 'Darwin':  # macOS
    homebrew_lib = '/opt/homebrew/lib'
    if homebrew_lib not in os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', ''):
        current_path = os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
        new_path = f"{homebrew_lib}:{current_path}" if current_path else homebrew_lib
        os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = new_path

from weasyprint import HTML, CSS


class PDFStyleTemplate:
    """Base class for PDF style templates."""
    
    def get_css(self) -> str:
        """Return CSS for this template."""
        raise NotImplementedError
    
    def get_name(self) -> str:
        """Return template name."""
        raise NotImplementedError


class ProfessionalTemplate(PDFStyleTemplate):
    """Professional/corporate style template."""
    
    def get_name(self) -> str:
        return "professional"
    
    def get_css(self) -> str:
        return """
        @page {
            margin: 0.75in;
            size: letter;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #333;
            max-width: none;
        }
        
        h1 {
            font-size: 24pt;
            font-weight: 600;
            margin: 0 0 8pt 0;
            color: #1a1a1a;
        }
        
        h2 {
            font-size: 14pt;
            font-weight: 600;
            margin: 16pt 0 8pt 0;
            color: #2c2c2c;
            border-bottom: 1pt solid #ddd;
            padding-bottom: 4pt;
        }
        
        h3 {
            font-size: 12pt;
            font-weight: 600;
            margin: 12pt 0 4pt 0;
            color: #333;
        }
        
        p {
            margin: 0 0 8pt 0;
        }
        
        ul {
            margin: 4pt 0 8pt 0;
            padding-left: 16pt;
        }
        
        li {
            margin: 2pt 0;
        }
        
        /* Contact info styling - assume it's the first paragraph after h1 */
        h1 + p {
            font-size: 10pt;
            color: #666;
            margin-bottom: 16pt;
        }
        
        /* Make sure content doesn't break awkwardly */
        h2, h3 {
            page-break-after: avoid;
        }
        
        li {
            page-break-inside: avoid;
        }
        """


class ModernTemplate(PDFStyleTemplate):
    """Modern/tech style template with accent colors."""
    
    def get_name(self) -> str:
        return "modern"
    
    def get_css(self) -> str:
        return """
        @page {
            margin: 0.75in;
            size: letter;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: #2d3748;
            max-width: none;
        }
        
        h1 {
            font-size: 28pt;
            font-weight: 700;
            margin: 0 0 6pt 0;
            color: #1a202c;
            letter-spacing: -0.02em;
        }
        
        h2 {
            font-size: 16pt;
            font-weight: 600;
            margin: 20pt 0 10pt 0;
            color: #2b6cb0;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 2pt solid #e2e8f0;
            padding-bottom: 6pt;
        }
        
        h3 {
            font-size: 13pt;
            font-weight: 600;
            margin: 14pt 0 6pt 0;
            color: #2d3748;
        }
        
        p {
            margin: 0 0 10pt 0;
        }
        
        ul {
            margin: 6pt 0 10pt 0;
            padding-left: 18pt;
        }
        
        li {
            margin: 3pt 0;
            position: relative;
        }
        
        li::marker {
            color: #2b6cb0;
        }
        
        /* Contact info styling */
        h1 + p {
            font-size: 10pt;
            color: #718096;
            margin-bottom: 20pt;
            font-weight: 500;
        }
        
        /* Add some visual hierarchy with background for contact */
        h1 + p {
            background-color: #f7fafc;
            padding: 8pt 12pt;
            border-radius: 4pt;
            border-left: 3pt solid #2b6cb0;
        }
        
        /* Page breaks */
        h2, h3 {
            page-break-after: avoid;
        }
        
        li {
            page-break-inside: avoid;
        }
        """


class PDFGenerator:
    """Converts markdown resume to PDF with template support."""
    
    def __init__(self):
        self.md = markdown.Markdown(extensions=['tables', 'nl2br'])
        self.templates: Dict[str, PDFStyleTemplate] = {
            'professional': ProfessionalTemplate(),
            'modern': ModernTemplate(),
        }
    
    def generate(self, content: str, output_path: Path, template: str = 'professional') -> Path:
        """Generate PDF from markdown content using specified template."""
        if template not in self.templates:
            available = ', '.join(self.templates.keys())
            raise ValueError(f"Unknown template '{template}'. Available: {available}")
        
        # Convert markdown to HTML
        html_content = self.md.convert(content)
        
        # Create full HTML document with basic styling
        full_html = self._create_html_document(html_content)
        
        # Get CSS for the template
        template_obj = self.templates[template]
        css_content = template_obj.get_css()
        
        # Generate PDF
        pdf_path = output_path.with_suffix('.pdf')
        HTML(string=full_html).write_pdf(pdf_path, stylesheets=[CSS(string=css_content)])
        
        return pdf_path
    
    def get_available_templates(self) -> list[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
    
    def _create_html_document(self, body_content: str) -> str:
        """Wrap markdown-converted content in a full HTML document."""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Resume</title>
        </head>
        <body>
            {body_content}
        </body>
        </html>
        """ 