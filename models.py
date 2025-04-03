import datetime
import json
from app import db

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(512), nullable=True)
    title = db.Column(db.String(255), nullable=True)
    content_type = db.Column(db.String(64), nullable=False)  # 'pdf', 'url', 'edgar', or 'demo'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    use_demo_mode = db.Column(db.Boolean, default=False)  # For demo mode processing without API calls
    use_local_processing = db.Column(db.Boolean, default=False)  # For local rule-based processing
    company_name = db.Column(db.String(255), nullable=True)  # For storing company name
    cik = db.Column(db.String(20), nullable=True)  # For SEC Edgar CIK
    use_buffett_mode = db.Column(db.Boolean, default=False)  # For Warren Buffett analysis style
    use_biotech_mode = db.Column(db.Boolean, default=False)  # For scientific/biotech company analysis mode
    industry_type = db.Column(db.String(64), nullable=True)  # Store the industry for specialized analysis
    insights = db.relationship('Insight', backref='document', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Document {self.filename or self.url}>'


class Insight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    # Insight categories:
    # Core insights: 'business_summary', 'moat', 'financial', 'management'
    # Phase 2 value investing lens: 'moat_analysis', 'red_flags', 'margin_of_safety', 'buffett_analysis', 'biotech_analysis'
    category = db.Column(db.String(64), nullable=False)
    content = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=True)  # For red flags: 'low', 'medium', 'high'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<Insight {self.category} for Document {self.document_id}>'
    
    def to_dict(self):
        result = {
            'id': self.id,
            'document_id': self.document_id,
            'category': self.category,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }
        if self.severity:
            result['severity'] = self.severity
        return result


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


class ApiUsage(db.Model):
    """Tracks API usage for cost management"""
    id = db.Column(db.Integer, primary_key=True)
    api_name = db.Column(db.String(64), nullable=False)  # 'openai', 'huggingface', 'deepseek'
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=True)
    prompt_tokens = db.Column(db.Integer, default=0)
    completion_tokens = db.Column(db.Integer, default=0)
    estimated_cost_usd = db.Column(db.Float, default=0.0)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<ApiUsage {self.api_name} - Doc {self.document_id} - Cost ${self.estimated_cost_usd:.4f}>'
    
    @staticmethod
    def calculate_openai_cost(prompt_tokens, completion_tokens, model="gpt-4o"):
        """Calculate the estimated cost for OpenAI API usage"""
        # Current pricing for gpt-4o (as of April 2025)
        costs = {
            "gpt-4o": {"prompt": 0.01, "completion": 0.03},  # per 1K tokens
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002}  # per 1K tokens
        }
        
        model_costs = costs.get(model, costs["gpt-4o"])
        prompt_cost = (prompt_tokens / 1000) * model_costs["prompt"]
        completion_cost = (completion_tokens / 1000) * model_costs["completion"]
        
        return prompt_cost + completion_cost
    
    @staticmethod
    def get_monthly_usage():
        """Get the total API usage for the current month"""
        start_of_month = datetime.datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return ApiUsage.query.filter(ApiUsage.timestamp >= start_of_month).all()
