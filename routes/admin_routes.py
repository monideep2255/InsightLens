import os
import datetime
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from models import db, ApiUsage

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/api-usage')
def api_usage():
    """Display API usage statistics"""
    # Calculate the monthly cost summary
    cost_summary = ApiUsage.get_monthly_cost_summary()
    
    # Get detailed usage data for charts
    start_of_month = datetime.datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage_data = ApiUsage.query.filter(ApiUsage.timestamp >= start_of_month).order_by(ApiUsage.timestamp).all()
    
    # Format data for charts
    usage_by_day = {}
    usage_by_api = {}
    
    for entry in usage_data:
        # Group by day
        day_key = entry.timestamp.strftime('%Y-%m-%d')
        if day_key not in usage_by_day:
            usage_by_day[day_key] = {
                'cost': 0.0,
                'requests': 0,
                'tokens': 0
            }
        
        usage_by_day[day_key]['cost'] += entry.estimated_cost_usd
        usage_by_day[day_key]['requests'] += 1
        usage_by_day[day_key]['tokens'] += entry.prompt_tokens + entry.completion_tokens
        
        # Group by API
        if entry.api_name not in usage_by_api:
            usage_by_api[entry.api_name] = {
                'cost': 0.0,
                'requests': 0,
                'tokens': 0
            }
        
        usage_by_api[entry.api_name]['cost'] += entry.estimated_cost_usd
        usage_by_api[entry.api_name]['requests'] += 1
        usage_by_api[entry.api_name]['tokens'] += entry.prompt_tokens + entry.completion_tokens
    
    # Get usage limit status
    monthly_budget = float(os.environ.get('MONTHLY_API_BUDGET', '20.0'))
    usage_status = ApiUsage.check_usage_limits(monthly_budget)
    
    # Get recent requests for the table
    recent_requests = ApiUsage.query.order_by(ApiUsage.timestamp.desc()).limit(50).all()
    
    return render_template('admin/api_usage.html', 
                          cost_summary=cost_summary,
                          usage_by_day=usage_by_day,
                          usage_by_api=usage_by_api,
                          usage_status=usage_status,
                          monthly_budget=monthly_budget,
                          recent_requests=recent_requests)


@admin_bp.route('/admin/update-budget', methods=['POST'])
def update_budget():
    """Update the monthly API budget"""
    try:
        new_budget = float(request.form.get('budget', 20.0))
        if new_budget <= 0:
            flash('Budget must be greater than zero', 'danger')
            return redirect(url_for('admin.api_usage'))
        
        # For a production app, you would store this in a database settings table
        # For this demo, we'll just use an environment variable
        os.environ['MONTHLY_API_BUDGET'] = str(new_budget)
        
        flash(f'Monthly budget updated to ${new_budget:.2f}', 'success')
    except ValueError:
        flash('Invalid budget value', 'danger')
    
    return redirect(url_for('admin.api_usage'))