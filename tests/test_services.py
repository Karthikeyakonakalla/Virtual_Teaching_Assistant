"""Service tests."""

import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services import SolutionFormatter, RAGPipeline


class TestSolutionFormatter(unittest.TestCase):
    """Test solution formatting service."""
    
    def setUp(self):
        """Set up test environment."""
        self.formatter = SolutionFormatter()
    
    def test_format_simple_solution(self):
        """Test formatting a simple solution."""
        raw_solution = """
        **Step 1: Understanding the Problem**
        We need to find the acceleration.
        
        **Step 2: Apply Formula**
        Using F = ma, we get a = F/m
        
        **Step 3: Calculate**
        a = 10/2 = 5 m/s²
        
        **Final Answer**
        The acceleration is 5 m/s²
        """
        
        result = self.formatter.format_solution(raw_solution)
        
        self.assertTrue(result['success'])
        self.assertIn('steps', result)
        self.assertIsNotNone(result['final_answer'])
        self.assertGreater(result['confidence_score'], 0)
    
    def test_extract_formulas(self):
        """Test formula extraction."""
        solution = "Using the formula $F = ma$ where $F$ is force and $m$ is mass."
        
        formulas = self.formatter._extract_formulas(solution)
        
        self.assertGreater(len(formulas), 0)
        self.assertEqual(formulas[0]['latex'], 'F = ma')
    
    def test_parse_steps(self):
        """Test step parsing."""
        solution = """
        **Step 1: First Step**
        Content of first step.
        
        **Step 2: Second Step**
        Content of second step.
        """
        
        steps = self.formatter._parse_steps(solution)
        
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0]['number'], 1)
        self.assertIn('First Step', steps[0]['title'])


class TestRAGPipeline(unittest.TestCase):
    """Test RAG pipeline."""
    
    def setUp(self):
        """Set up test environment."""
        self.rag = RAGPipeline()
    
    def test_add_and_search_documents(self):
        """Test adding and searching documents."""
        # Add test documents
        documents = [
            "Newton's first law states that objects at rest stay at rest.",
            "The derivative of x² is 2x.",
            "pH is the negative logarithm of hydrogen ion concentration."
        ]
        
        metadata = [
            {"source": "Test", "subject": "physics"},
            {"source": "Test", "subject": "mathematics"},
            {"source": "Test", "subject": "chemistry"}
        ]
        
        self.rag.add_documents(documents, metadata)
        
        # Search for a physics concept
        results = self.rag.search("Newton's law", top_k=1)
        
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]['subject'], 'physics')
        self.assertIn("Newton", results[0]['text'])
    
    def test_subject_filtering(self):
        """Test search with subject filtering."""
        # Add test documents
        documents = [
            "Force equals mass times acceleration.",
            "The quadratic formula solves ax² + bx + c = 0."
        ]
        
        metadata = [
            {"source": "Test", "subject": "physics"},
            {"source": "Test", "subject": "mathematics"}
        ]
        
        self.rag.add_documents(documents, metadata)
        
        # Search with physics filter
        physics_results = self.rag.search(
            "formula",
            top_k=5,
            subject_filter="physics"
        )
        
        # Search with mathematics filter
        math_results = self.rag.search(
            "formula",
            top_k=5,
            subject_filter="mathematics"
        )
        
        # Mathematics results should include quadratic formula
        if len(math_results) > 0:
            self.assertIn("quadratic", math_results[0]['text'].lower())


if __name__ == '__main__':
    unittest.main()
