import datetime
import json
import uuid
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
    model_name = db.Column(db.String(64), nullable=True)  # Store the model name used (gpt-4o, mixtral, etc.)
    request_successful = db.Column(db.Boolean, default=True)  # Track if the API request was successful
    error_message = db.Column(db.Text, nullable=True)  # Store any error messages
    
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
    def calculate_huggingface_cost(prompt_tokens, completion_tokens, model="mistral"):
        """Calculate the estimated cost for Hugging Face API usage"""
        # Approximate pricing for Hugging Face Inference API
        costs = {
            "mistral": {"prompt": 0.0000025, "completion": 0.0000025},  # per token
            "llama3": {"prompt": 0.000003, "completion": 0.000003},     # per token
            "deepseek": {"prompt": 0.000004, "completion": 0.000004}    # per token
        }
        
        model_costs = costs.get(model, costs["mistral"])
        prompt_cost = prompt_tokens * model_costs["prompt"]
        completion_cost = completion_tokens * model_costs["completion"]
        
        return prompt_cost + completion_cost
    
    @staticmethod
    def get_monthly_usage():
        """Get the total API usage for the current month"""
        start_of_month = datetime.datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return ApiUsage.query.filter(ApiUsage.timestamp >= start_of_month).all()
    
    @staticmethod
    def get_monthly_cost_summary():
        """Get a summary of API costs for the current month"""
        start_of_month = datetime.datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage = ApiUsage.query.filter(ApiUsage.timestamp >= start_of_month).all()
        
        summary = {
            "total_cost": sum(entry.estimated_cost_usd for entry in usage),
            "total_requests": len(usage),
            "by_api": {},
            "successful_requests": sum(1 for entry in usage if entry.request_successful),
            "failed_requests": sum(1 for entry in usage if not entry.request_successful)
        }
        
        # Group by API provider
        for entry in usage:
            if entry.api_name not in summary["by_api"]:
                summary["by_api"][entry.api_name] = {
                    "cost": 0,
                    "requests": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0
                }
            
            api_summary = summary["by_api"][entry.api_name]
            api_summary["cost"] += entry.estimated_cost_usd
            api_summary["requests"] += 1
            api_summary["prompt_tokens"] += entry.prompt_tokens
            api_summary["completion_tokens"] += entry.completion_tokens
        
        return summary
    
    @staticmethod
    def check_usage_limits(monthly_budget=20.0):
        """Check if we are approaching or have exceeded usage limits
        
        Returns:
            dict: Status of API usage containing keys:
                - within_budget: Boolean indicating if usage is within budget
                - usage_percent: Percentage of budget used
                - remaining_budget: Amount of budget remaining
                - total_cost: Total cost incurred this month
        """
        summary = ApiUsage.get_monthly_cost_summary()
        total_cost = summary["total_cost"]
        
        return {
            "within_budget": total_cost < monthly_budget,
            "usage_percent": (total_cost / monthly_budget) * 100 if monthly_budget > 0 else 0,
            "remaining_budget": monthly_budget - total_cost,
            "total_cost": total_cost
        }


class ShareableLink(db.Model):
    """Model for creating shareable links to document insights"""
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # If NULL, link never expires
    is_active = db.Column(db.Boolean, default=True)
    name = db.Column(db.String(128), nullable=True)  # Optional name/description for the link
    
    # Relationship with Document
    document = db.relationship('Document', backref=db.backref('shareable_links', lazy=True))
    
    def __repr__(self):
        return f'<ShareableLink {self.token[:8]}... for Document {self.document_id}>'
    
    @staticmethod
    def generate_token():
        """Generate a unique token for a shareable link"""
        return uuid.uuid4().hex
    
    @staticmethod
    def create_for_document(document_id, name=None, expires_days=None):
        """Create a new shareable link for a document
        
        Args:
            document_id (int): ID of the document to share
            name (str, optional): Name/description for the link
            expires_days (int, optional): Number of days until link expires
            
        Returns:
            ShareableLink: Newly created shareable link
        """
        # Generate a unique token
        token = ShareableLink.generate_token()
        
        # Calculate expiration date if provided
        expires_at = None
        if expires_days:
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=expires_days)
        
        # Create and save the link
        link = ShareableLink(
            document_id=document_id,
            token=token,
            name=name,
            expires_at=expires_at
        )
        
        db.session.add(link)
        db.session.commit()
        
        return link
    
    def is_expired(self):
        """Check if the link has expired"""
        if not self.expires_at:
            return False
        
        return datetime.datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if the link is valid (active and not expired)"""
        return self.is_active and not self.is_expired()
