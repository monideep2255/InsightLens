import os
import time
import unittest
from flask_testing import TestCase
from app import app, db
from models import Document, Insight, ShareableLink
from datetime import datetime, timedelta

class ShareTestCase(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
        return app
    
    def setUp(self):
        db.create_all()
        # Create a test document and insights for testing
        self.test_doc = Document(
            title="Test Document for Sharing",
            content_type="demo",
            company_name="Test Company",
            processed=True
        )
        db.session.add(self.test_doc)
        db.session.commit()
        
        # Add test insights
        insights = [
            Insight(document_id=self.test_doc.id, category="business_summary", content="<p>Test business summary</p>"),
            Insight(document_id=self.test_doc.id, category="financial", content="<p>Test financial analysis</p>")
        ]
        for insight in insights:
            db.session.add(insight)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
    
    def test_create_link_form(self):
        """Test the form for creating shareable links"""
        response = self.client.get(f'/document/{self.test_doc.id}/share')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Shareable Link', response.data)
    
    def test_create_link(self):
        """Test creating a shareable link"""
        # Create a link that never expires
        response = self.client.post(
            f'/document/{self.test_doc.id}/share',
            data={'name': 'Test Link', 'expires_days': ''}
        )
        
        # Should redirect to manage links page
        self.assertEqual(response.status_code, 302)
        
        # Check that link was created
        link = ShareableLink.query.filter_by(document_id=self.test_doc.id).first()
        self.assertIsNotNone(link)
        self.assertEqual(link.name, 'Test Link')
        self.assertIsNone(link.expires_at)  # No expiration
    
    def test_create_expiring_link(self):
        """Test creating a link with expiration"""
        response = self.client.post(
            f'/document/{self.test_doc.id}/share',
            data={'name': 'Expiring Link', 'expires_days': '7'}
        )
        
        # Check that link was created with expiration
        link = ShareableLink.query.filter_by(document_id=self.test_doc.id).first()
        self.assertIsNotNone(link)
        self.assertEqual(link.name, 'Expiring Link')
        self.assertIsNotNone(link.expires_at)
        
        # Expiration should be approximately 7 days from now
        delta = link.expires_at - datetime.utcnow()
        self.assertTrue(6 <= delta.days <= 7)  # Allow for a few seconds of test execution
    
    def test_manage_links(self):
        """Test the link management page"""
        # Create a link first
        link = ShareableLink(
            document_id=self.test_doc.id,
            token="test_token_123",
            name="Test Link",
            is_active=True
        )
        db.session.add(link)
        db.session.commit()
        
        # Test the manage links page
        response = self.client.get(f'/document/{self.test_doc.id}/manage-links')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Link', response.data)
        self.assertIn(b'test_token_123', response.data)
    
    def test_view_shared_document(self):
        """Test viewing a document via a shareable link"""
        # Create a link
        link = ShareableLink(
            document_id=self.test_doc.id,
            token="view_test_token",
            name="View Test Link",
            is_active=True
        )
        db.session.add(link)
        db.session.commit()
        
        # View the shared document
        response = self.client.get(f'/shared/view_test_token')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Shared View', response.data)
        self.assertIn(b'Test business summary', response.data)
    
    def test_expired_link(self):
        """Test handling of expired links"""
        # Create an expired link
        expired_date = datetime.utcnow() - timedelta(days=1)
        link = ShareableLink(
            document_id=self.test_doc.id,
            token="expired_token",
            name="Expired Link",
            is_active=True,
            expires_at=expired_date
        )
        db.session.add(link)
        db.session.commit()
        
        # Try to view the expired document
        response = self.client.get(f'/shared/expired_token')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Link Expired or Deactivated', response.data)
    
    def test_deactivate_link(self):
        """Test deactivating a link"""
        # Create a link
        link = ShareableLink(
            document_id=self.test_doc.id,
            token="deactivate_token",
            name="Deactivate Test",
            is_active=True
        )
        db.session.add(link)
        db.session.commit()
        
        # Deactivate the link
        response = self.client.post(f'/document/{self.test_doc.id}/deactivate-link/{link.id}')
        
        # Should redirect to manage links page
        self.assertEqual(response.status_code, 302)
        
        # Check link status
        link = ShareableLink.query.filter_by(token="deactivate_token").first()
        self.assertFalse(link.is_active)
        
        # Try to view the deactivated document
        response = self.client.get(f'/shared/deactivate_token')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Link Expired or Deactivated', response.data)


if __name__ == '__main__':
    unittest.main()
