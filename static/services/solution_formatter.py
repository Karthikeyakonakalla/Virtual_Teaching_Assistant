"""Solution formatter for step-by-step presentation."""

import re
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SolutionFormatter:
    """Format solutions for clear step-by-step presentation."""
    
    def __init__(self):
        """Initialize the solution formatter."""
        self.step_pattern = re.compile(r'\*\*Step\s+(\d+)[:\s]*(.*?)\*\*', re.IGNORECASE)
        self.math_pattern = re.compile(r'\$([^$]+)\$|\$\$([^$]+)\$\$')
    
    def format_solution(
        self,
        raw_solution: str,
        query_type: str = 'general',
        include_latex: bool = True
    ) -> Dict[str, Any]:
        """Format a raw solution into structured steps.
        Args:
            raw_solution: Raw solution text from LLM
            query_type: Type of query (general, numerical, mcq, etc.)
            include_latex: Whether to include LaTeX formatting
            
        Returns:
            Formatted solution dictionary
        """
        try:
            # Parse steps from solution
            steps = self._parse_steps(raw_solution)
            
            # Extract key components
            problem_understanding = self._extract_problem_understanding(raw_solution)
            formulas = self._extract_formulas(raw_solution)
            final_answer = self._extract_final_answer(raw_solution)
            verification = self._extract_verification(raw_solution)
            
            # Format based on query type
            if query_type == 'mcq':
                formatted = self._format_mcq_solution(steps, final_answer)
            elif query_type == 'numerical':
                formatted = self._format_numerical_solution(steps, final_answer, verification)
            else:
                formatted = self._format_general_solution(steps)
            
            # Add LaTeX formatting if requested
            if include_latex:
                formatted = self._add_latex_formatting(formatted)
            
            # Create final structure
            result = {
                'success': True,
                'type': query_type,
                'problem_understanding': problem_understanding,
                'formulas_used': formulas,
                'steps': formatted['steps'],
                'final_answer': final_answer,
                'verification': verification,
                'confidence_score': self._calculate_confidence(steps, final_answer),
                'display_html': self._generate_html(formatted),
                'display_text': self._generate_plain_text(formatted)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error formatting solution: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'raw_solution': raw_solution
            }
    
    def _parse_steps(self, solution: str) -> List[Dict[str, Any]]:
        """Parse steps from solution text.
        
        Args:
            solution: Raw solution text
            
        Returns:
            List of parsed steps
        """
        steps = []
        
        # Find all step markers
        step_matches = list(self.step_pattern.finditer(solution))
        
        if step_matches:
            # Parse marked steps
            for i, match in enumerate(step_matches):
                step_num = int(match.group(1))
                step_title = match.group(2).strip()
                
                # Extract content until next step or end
                start = match.end()
                end = step_matches[i+1].start() if i+1 < len(step_matches) else len(solution)
                content = solution[start:end].strip()
                
                steps.append({
                    'number': step_num,
                    'title': self._strip_markdown_headings(step_title),
                    'content': self._strip_markdown_headings(content),
                    'collapsible': len(content) > 200
                })
        else:
            # No explicit steps, try to infer structure
            paragraphs = solution.split('\n\n')
            for i, para in enumerate(paragraphs, 1):
                if para.strip():
                    steps.append({
                        'number': i,
                        'title': f'Part {i}',
                        'content': self._strip_markdown_headings(para),
                        'collapsible': len(para) > 200
                    })
        
        return steps

    def _strip_markdown_headings(self, text: str) -> str:
        """Remove leading markdown heading markers from text."""
        if not text:
            return text

        cleaned = text.strip()
        # Remove leading markdown heading symbols like ##, ### etc.
        cleaned = re.sub(r'^#{1,6}\s*', '', cleaned)
        return cleaned.strip()
    
    def _extract_problem_understanding(self, solution: str) -> str:
        """Extract problem understanding section.
        
        Args:
            solution: Raw solution text
            
        Returns:
            Problem understanding text
        """
        patterns = [
            r'Understanding the [Pp]roblem[:\s]*(.*?)(?=Step|\n\n|$)',
            r'Given[:\s]*(.*?)(?=Step|\n\n|$)',
            r'Problem Analysis[:\s]*(.*?)(?=Step|\n\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, solution, re.DOTALL)
            if match:
                return self._strip_markdown_headings(match.group(1))
        
        # Fallback: first paragraph
        first_para = solution.split('\n\n')[0]
        if len(first_para) < 300:
            return self._strip_markdown_headings(first_para)
        
        return ""
    
    def _extract_formulas(self, solution: str) -> List[Dict[str, str]]:
        """Extract formulas from solution.
        
        Args:
            solution: Raw solution text
            
        Returns:
            List of formulas with descriptions
        """
        formulas = []
        
        # Find LaTeX formulas
        math_matches = self.math_pattern.findall(solution)
        for match in math_matches:
            formula = match[0] or match[1]
            if len(formula) > 5:  # Skip very short expressions
                formulas.append({
                    'latex': formula,
                    'type': 'display' if match[1] else 'inline'
                })
        
        # Find formula mentions
        formula_patterns = [
            r'Formula[:\s]*(.*?)(?=\n|$)',
            r'Using[:\s]*(.*?)(?=\n|$)',
            r'Apply[:\s]*(.*?)(?=\n|$)'
        ]
        
        for pattern in formula_patterns:
            matches = re.findall(pattern, solution)
            for match in matches:
                if '$' in match:
                    formulas.append({
                        'description': match.strip(),
                        'type': 'reference'
                    })
        
        return formulas
    
    def _extract_final_answer(self, solution: str) -> str:
        """Extract final answer from solution.
        
        Args:
            solution: Raw solution text
            
        Returns:
            Final answer text
        """
        patterns = [
            r'Final Answer[:\s]*(.*?)(?=\n\n|Verification|$)',
            r'Answer[:\s]*(.*?)(?=\n\n|Verification|$)',
            r'Therefore[,:\s]*(.*?)(?=\n\n|Verification|$)',
            r'Hence[,:\s]*(.*?)(?=\n\n|Verification|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, solution, re.DOTALL | re.IGNORECASE)
            if match:
                answer = match.group(1).strip()
                # Clean up answer
                answer = re.sub(r'^[:\s]*', '', answer)
                return answer
        
        # Fallback: last non-empty line
        lines = solution.strip().split('\n')
        for line in reversed(lines):
            if line.strip() and not line.startswith('Verification'):
                return line.strip()
        
        return "Solution provided above"
    
    def _extract_verification(self, solution: str) -> Optional[str]:
        """Extract verification section if present.
        
        Args:
            solution: Raw solution text
            
        Returns:
            Verification text or None
        """
        patterns = [
            r'Verification[:\s]*(.*?)(?=$)',
            r'Check[:\s]*(.*?)(?=$)',
            r'Verify[:\s]*(.*?)(?=$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, solution, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _format_mcq_solution(
        self,
        steps: List[Dict],
        final_answer: str
    ) -> Dict[str, Any]:
        """Format solution for MCQ type questions.
        
        Args:
            steps: Parsed steps
            final_answer: Final answer
            
        Returns:
            Formatted MCQ solution
        """
        # Highlight the correct option
        option_pattern = re.compile(r'\(([A-D])\)', re.IGNORECASE)
        match = option_pattern.search(final_answer)
        
        if match:
            option = match.group(1).upper()
            final_answer = f"**Option ({option})** - {final_answer}"
        
        return {
            'steps': steps,
            'answer_option': option if match else None,
            'explanation': final_answer
        }
    
    def _format_numerical_solution(
        self,
        steps: List[Dict],
        final_answer: str,
        verification: Optional[str]
    ) -> Dict[str, Any]:
        """Format solution for numerical problems.
        
        Args:
            steps: Parsed steps
            final_answer: Final answer
            verification: Verification text
            
        Returns:
            Formatted numerical solution
        """
        # Extract numerical value
        number_pattern = re.compile(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?')
        numbers = number_pattern.findall(final_answer)
        
        numerical_value = numbers[0] if numbers else None
        
        # Extract units if present
        unit_pattern = re.compile(r'\b(m/s|m|kg|N|J|W|Hz|s|A|V|Ω|mol|L|°C|K)\b')
        units = unit_pattern.findall(final_answer)
        unit = units[0] if units else None
        
        return {
            'steps': steps,
            'numerical_answer': numerical_value,
            'unit': unit,
            'complete_answer': final_answer,
            'verified': verification is not None
        }
    
    def _format_general_solution(self, steps: List[Dict]) -> Dict[str, Any]:
        """Format general solution.
        
        Args:
            steps: Parsed steps
            
        Returns:
            Formatted general solution
        """
        return {'steps': steps}
    
    def _add_latex_formatting(self, formatted: Dict) -> Dict:
        """Add LaTeX formatting to solution.
        
        Args:
            formatted: Formatted solution
            
        Returns:
            Solution with LaTeX formatting
        """
        if 'steps' in formatted:
            for step in formatted['steps']:
                step['content'] = self._format_latex_in_text(step['content'])
        
        return formatted
    
    def _format_latex_in_text(self, text: str) -> str:
        """Format LaTeX expressions in text for display.
        
        Args:
            text: Text containing LaTeX
            
        Returns:
            Formatted text
        """
        # Ensure proper LaTeX delimiters
        text = re.sub(r'(?<!\$)\$(?!\$)([^$]+)\$(?!\$)', r'\\( \1 \\)', text)
        text = re.sub(r'\$\$([^$]+)\$\$', r'\\[ \1 \\]', text)
        
        return text
    
    def _calculate_confidence(
        self,
        steps: List[Dict],
        final_answer: str
    ) -> float:
        """Calculate confidence score for solution.
        
        Args:
            steps: Solution steps
            final_answer: Final answer
            
        Returns:
            Confidence score (0-1)
        """
        confidence = 0.5  # Base confidence
        
        # Increase for structured steps
        if len(steps) > 1:
            confidence += 0.2
        
        # Increase for clear final answer
        if final_answer and len(final_answer) > 10:
            confidence += 0.15
        
        # Increase for formula usage
        if any('$' in step.get('content', '') for step in steps):
            confidence += 0.1
        
        # Cap at 0.95
        return min(confidence, 0.95)
    
    def _generate_html(self, formatted: Dict) -> str:
        """Generate HTML representation of solution.
        
        Args:
            formatted: Formatted solution
            
        Returns:
            HTML string
        """
        html_parts = ['<div class="solution">']
        
        for step in formatted.get('steps', []):
            html_parts.append(f'''
                <div class="step" data-step="{step['number']}">
                    <h3 class="step-title">
                        Step {step['number']}: {step.get('title', '')}
                    </h3>
                    <div class="step-content {'collapsible' if step.get('collapsible') else ''}">
                        {step['content']}
                    </div>
                </div>
            ''')
        
        if formatted.get('answer_option'):
            html_parts.append(f'''
                <div class="final-answer mcq">
                    <strong>Correct Option:</strong> {formatted['answer_option']}
                </div>
            ''')
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)
    
    def _generate_plain_text(self, formatted: Dict) -> str:
        """Generate plain text representation of solution.
        
        Args:
            formatted: Formatted solution
            
        Returns:
            Plain text string
        """
        text_parts = []
        
        for step in formatted.get('steps', []):
            text_parts.append(f"Step {step['number']}: {step.get('title', '')}")
            text_parts.append(step['content'])
            text_parts.append("")
        
        return '\n'.join(text_parts)
