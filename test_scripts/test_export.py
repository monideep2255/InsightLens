import os
import time
import unittest
from flask_testing import TestCase
from app import app, db
from models import Document, Insight

class ExportTestCase(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
        return app
    
    def setUp(self):
        db.create_all()
        # Create a test document and insights for testing
        self.test_doc = Document(
            title="Test Document for Export",
            content_type="demo",
            company_name="Test Company",
            processed=True
        )
        db.session.add(self.test_doc)
        db.session.commit()
        
        # Add test insights
        insights = [
            Insight(document_id=self.test_doc.id, category="business_summary", content="<p>Test business summary</p>"),
            Insight(document_id=self.test_doc.id, category="financial", content="<p>Test financial analysis</p>"),
            Insight(document_id=self.test_doc.id, category="moat", content="<p>Test competitive moat</p>")
        ]
        for insight in insights:
            db.session.add(insight)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
    
    def test_pdf_export(self):
        """Test PDF export functionality"""
        # Export the document to PDF
        response = self.client.get(f'/document/{self.test_doc.id}/export/pdf')
        
        # Check that the response is a file download
        self.assertEqual(response.status_code, 200)
        self.assertTrue('attachment' in response.headers.get('Content-Disposition', ''))
        self.assertEqual(response.mimetype, 'application/pdf')
        
        # The content should be a PDF (starts with %PDF-)
        self.assertTrue(response.data.startswith(b'%PDF-'))

    def test_api_export(self):
        """Test the API endpoint for PDF export"""
        response = self.client.post(f'/api/document/{self.test_doc.id}/export/pdf')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertTrue(data['success'])
        self.assertTrue('pdf_url' in data)

    def test_regenerate_insight(self):
        """Test regenerating a specific insight"""
        # This test may not work in isolation as it requires AI services
        # But we can test the route response
        response = self.client.post(f'/document/{self.test_doc.id}/regenerate/business_summary')
        
        # Should redirect back to insights page
        self.assertEqual(response.status_code, 302)

if __name__ == '__main__':
    unittest.main()
