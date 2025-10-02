"""Script to load knowledge base into the RAG system."""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services import RAGPipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_knowledge_base():
    """Create sample knowledge base files for demonstration."""
    
    # Create directories
    kb_path = Path('knowledge_base')
    ncert_path = kb_path / 'ncert'
    formulas_path = kb_path / 'formulas'
    papers_path = kb_path / 'past_papers'
    
    for path in [ncert_path / 'physics', ncert_path / 'chemistry', ncert_path / 'mathematics', formulas_path, papers_path]:
        path.mkdir(parents=True, exist_ok=True)
    
    # Sample NCERT Physics content
    physics_chapter = {
        "chapter": "Laws of Motion",
        "passages": [
            {
                "text": "Newton's First Law of Motion states that an object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced force. This is also known as the law of inertia.",
                "page": 96,
                "topics": ["Newton's Laws", "Inertia", "Force"]
            },
            {
                "text": "Newton's Second Law of Motion states that the acceleration of an object is directly proportional to the net force acting on it and inversely proportional to its mass. Mathematically, F = ma, where F is force, m is mass, and a is acceleration.",
                "page": 98,
                "topics": ["Newton's Laws", "Force", "Acceleration", "Mass"]
            },
            {
                "text": "Newton's Third Law of Motion states that for every action, there is an equal and opposite reaction. When object A exerts a force on object B, object B exerts an equal and opposite force on object A.",
                "page": 102,
                "topics": ["Newton's Laws", "Action-Reaction", "Force Pairs"]
            }
        ]
    }
    
    with open(ncert_path / 'physics' / 'laws_of_motion.json', 'w') as f:
        json.dump(physics_chapter, f, indent=2)
    
    # Sample NCERT Chemistry content
    chemistry_chapter = {
        "chapter": "Chemical Bonding",
        "passages": [
            {
                "text": "Ionic bonds are formed when electrons are transferred from one atom to another, resulting in the formation of ions. The electrostatic attraction between oppositely charged ions holds them together.",
                "page": 45,
                "topics": ["Ionic Bonding", "Electron Transfer", "Ions"]
            },
            {
                "text": "Covalent bonds are formed when atoms share electrons to achieve a stable electron configuration. The shared electrons are counted in the valence shells of both atoms.",
                "page": 48,
                "topics": ["Covalent Bonding", "Electron Sharing", "Valence Electrons"]
            },
            {
                "text": "The octet rule states that atoms tend to gain, lose, or share electrons to achieve a configuration with eight electrons in their outermost shell, similar to noble gases.",
                "page": 43,
                "topics": ["Octet Rule", "Electron Configuration", "Chemical Stability"]
            }
        ]
    }
    
    with open(ncert_path / 'chemistry' / 'chemical_bonding.json', 'w') as f:
        json.dump(chemistry_chapter, f, indent=2)
    
    # Sample NCERT Mathematics content
    maths_chapter = {
        "chapter": "Differential Calculus",
        "passages": [
            {
                "text": "The derivative of a function f(x) at a point x is defined as the limit of the difference quotient as h approaches zero: f'(x) = lim(h→0) [f(x+h) - f(x)]/h",
                "page": 178,
                "topics": ["Derivatives", "Limits", "Differentiation"]
            },
            {
                "text": "The chain rule states that if y = f(g(x)), then dy/dx = f'(g(x)) · g'(x). This is used to find derivatives of composite functions.",
                "page": 185,
                "topics": ["Chain Rule", "Composite Functions", "Differentiation"]
            },
            {
                "text": "The product rule states that if y = u(x) · v(x), then dy/dx = u'(x) · v(x) + u(x) · v'(x). This is used for differentiating products of functions.",
                "page": 183,
                "topics": ["Product Rule", "Differentiation", "Products of Functions"]
            }
        ]
    }
    
    with open(ncert_path / 'mathematics' / 'differential_calculus.json', 'w') as f:
        json.dump(maths_chapter, f, indent=2)
    
    # Sample Physics formulas
    physics_formulas = [
        {
            "name": "Kinematic Equation 1",
            "formula": "v = u + at",
            "description": "Final velocity equals initial velocity plus acceleration times time",
            "conditions": "For constant acceleration",
            "topics": ["Kinematics", "Motion", "Acceleration"]
        },
        {
            "name": "Kinematic Equation 2",
            "formula": "s = ut + (1/2)at²",
            "description": "Displacement equals initial velocity times time plus half acceleration times time squared",
            "conditions": "For constant acceleration",
            "topics": ["Kinematics", "Displacement", "Motion"]
        },
        {
            "name": "Newton's Second Law",
            "formula": "F = ma",
            "description": "Force equals mass times acceleration",
            "conditions": "For constant mass",
            "topics": ["Force", "Newton's Laws", "Dynamics"]
        },
        {
            "name": "Work-Energy Theorem",
            "formula": "W = ΔKE = (1/2)mv² - (1/2)mu²",
            "description": "Work done equals change in kinetic energy",
            "conditions": "For conservative forces",
            "topics": ["Work", "Energy", "Kinetic Energy"]
        }
    ]
    
    with open(formulas_path / 'physics.json', 'w') as f:
        json.dump(physics_formulas, f, indent=2)
    
    # Sample Chemistry formulas
    chemistry_formulas = [
        {
            "name": "Ideal Gas Law",
            "formula": "PV = nRT",
            "description": "Pressure times volume equals moles times gas constant times temperature",
            "conditions": "For ideal gases",
            "topics": ["Gases", "Thermodynamics", "State Equations"]
        },
        {
            "name": "pH Formula",
            "formula": "pH = -log[H⁺]",
            "description": "pH is the negative logarithm of hydrogen ion concentration",
            "conditions": "For aqueous solutions",
            "topics": ["Acids and Bases", "pH", "Equilibrium"]
        },
        {
            "name": "Rate Law",
            "formula": "Rate = k[A]ᵐ[B]ⁿ",
            "description": "Reaction rate equals rate constant times concentration terms raised to their orders",
            "conditions": "For elementary reactions",
            "topics": ["Chemical Kinetics", "Reaction Rate", "Rate Laws"]
        }
    ]
    
    with open(formulas_path / 'chemistry.json', 'w') as f:
        json.dump(chemistry_formulas, f, indent=2)
    
    # Sample Mathematics formulas
    maths_formulas = [
        {
            "name": "Quadratic Formula",
            "formula": "x = [-b ± √(b² - 4ac)] / 2a",
            "description": "Solutions for quadratic equation ax² + bx + c = 0",
            "conditions": "For a ≠ 0",
            "topics": ["Quadratic Equations", "Algebra", "Roots"]
        },
        {
            "name": "Derivative of Power Function",
            "formula": "d/dx(xⁿ) = nx^(n-1)",
            "description": "Power rule for differentiation",
            "conditions": "For any real number n",
            "topics": ["Differentiation", "Calculus", "Power Rule"]
        },
        {
            "name": "Integration by Parts",
            "formula": "∫u dv = uv - ∫v du",
            "description": "Method for integrating products of functions",
            "conditions": "For differentiable functions",
            "topics": ["Integration", "Calculus", "Integration Techniques"]
        }
    ]
    
    with open(formulas_path / 'mathematics.json', 'w') as f:
        json.dump(maths_formulas, f, indent=2)
    
    # Sample past paper questions
    past_paper = {
        "year": "2023",
        "questions": [
            {
                "text": "A particle moves along a straight line with velocity v = 3t² - 6t + 2 m/s. Find the acceleration at t = 2 seconds.",
                "subject": "physics",
                "topics": ["Kinematics", "Velocity", "Acceleration"],
                "difficulty": "Medium",
                "marks": 3,
                "solution": "Given: v = 3t² - 6t + 2\nAcceleration a = dv/dt = 6t - 6\nAt t = 2s: a = 6(2) - 6 = 12 - 6 = 6 m/s²"
            },
            {
                "text": "Calculate the pH of a 0.01 M HCl solution.",
                "subject": "chemistry",
                "topics": ["Acids and Bases", "pH Calculation"],
                "difficulty": "Easy",
                "marks": 2,
                "solution": "HCl is a strong acid, so [H⁺] = 0.01 M\npH = -log[H⁺] = -log(0.01) = -log(10⁻²) = 2"
            },
            {
                "text": "Find the derivative of f(x) = sin(x²) with respect to x.",
                "subject": "mathematics",
                "topics": ["Differentiation", "Chain Rule", "Trigonometry"],
                "difficulty": "Medium",
                "marks": 3,
                "solution": "Using chain rule: f'(x) = cos(x²) · d/dx(x²) = cos(x²) · 2x = 2x·cos(x²)"
            }
        ]
    }
    
    with open(papers_path / 'jee_2023_sample.json', 'w') as f:
        json.dump(past_paper, f, indent=2)
    
    logger.info("Sample knowledge base files created successfully!")


def load_knowledge_base():
    """Load the knowledge base into the RAG system."""
    
    # Create sample knowledge base if it doesn't exist
    if not Path('knowledge_base/ncert/physics').exists():
        logger.info("Creating sample knowledge base...")
        create_sample_knowledge_base()
    
    # Initialize RAG pipeline
    logger.info("Initializing RAG pipeline...")
    rag_pipeline = RAGPipeline()
    
    # Load knowledge base
    logger.info("Loading knowledge base...")
    rag_pipeline.load_knowledge_base('knowledge_base')
    
    # Get statistics
    stats = rag_pipeline.get_stats()
    logger.info(f"Knowledge base loaded successfully!")
    logger.info(f"Total documents: {stats['total_documents']}")
    logger.info(f"Sources: {stats['sources']}")
    logger.info(f"Subjects: {stats['subjects']}")
    
    # Test search
    logger.info("\nTesting search functionality...")
    test_queries = [
        "Newton's second law",
        "pH calculation",
        "derivative chain rule"
    ]
    
    for query in test_queries:
        results = rag_pipeline.search(query, top_k=2)
        logger.info(f"\nQuery: {query}")
        for i, result in enumerate(results, 1):
            logger.info(f"  {i}. Source: {result['source']}, Score: {result['score']:.2f}")
            logger.info(f"     Text: {result['text'][:100]}...")


if __name__ == '__main__':
    load_knowledge_base()
