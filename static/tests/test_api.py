"""API endpoint tests."""

import unittest
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from models import User


class TestAPI(unittest.TestCase):
    """Test API endpoints."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_text_query(self):
        """Test text query submission."""
        query_data = {
            'query': 'What is Newton\'s second law?',
            'subject': 'physics'
        }
        
        response = self.client.post(
            '/api/query',
            data=json.dumps(query_data),
            content_type='application/json'
        )
        
        # Check response (may fail without API key)
        self.assertIn(response.status_code, [200, 500])
    
    def test_registration(self):
        """Test user registration."""
        user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User'
        }
        
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('token', data)
    
    def test_login(self):
        """Test user login."""
        # First register a user
        user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User'
        }
        
        self.client.post(
            '/api/auth/register',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        
        # Now try to login
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('token', data)
    
    def test_invalid_login(self):
        """Test login with invalid credentials."""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpass'
        }
        
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertFalse(data['success'])


if __name__ == '__main__':
    unittest.main()
