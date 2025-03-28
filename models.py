import datetime
import json
from app import db

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(512), nullable=True)
    title = db.Column(db.String(255), nullable=True)
    content_type = db.Column(db.String(64), nullable=False)  # 'pdf' or 'url'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    insights = db.relationship('Insight', backref='document', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Document {self.filename or self.url}>'


class Insight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    category = db.Column(db.String(64), nullable=False)  # 'business_summary', 'moat', 'financial', 'management'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<Insight {self.category} for Document {self.document_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'category': self.category,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }


class Processing(db.Model):
    """Stores the status of document processing jobs"""
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    status = db.Column(db.String(32), default='pending')  # pending, processing, completed, failed
    error = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Processing {self.id} for Document {self.document_id} ({self.status})>'
