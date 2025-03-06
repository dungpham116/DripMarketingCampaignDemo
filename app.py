from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from dotenv import load_dotenv
import os
import requests
import json
import pandas as pd
import io
import pytz
from werkzeug.middleware.proxy_fix import ProxyFix
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app)

# Authentication check decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'api_key' not in session:
            flash('Please log in first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Helper function to refresh campaign data
def refresh_campaign_data(campaign_id):
    """Helper function to refresh campaign data in Smartlead"""
    try:
        response = requests.post(
            f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/refresh?api_key={session['api_key']}"
        )
        return response.status_code == 200
    except Exception as e:
        app.logger.error(f"Error refreshing campaign data: {str(e)}")
        return False

# Centralized API request handler
def api_request(method, endpoint, data=None, params=None):
    """Centralized API request handler to ensure consistent behavior"""
    base_url = "https://server.smartlead.ai/api/v1"
    url = f"{base_url}/{endpoint}"
    
    # Ensure we have the API key
    if 'api_key' not in session:
        raise Exception("API key not found in session")
        
    # Set up headers with API key
    headers = {
        "X-API-KEY": session['api_key'],
        "Content-Type": "application/json",
        "Accept": "application/json",
        # Add Cache-Control header instead of query param
        "Cache-Control": "no-cache, no-store, must-revalidate"
    }
    
    # Build params with API key
    if params is None:
        params = {}
    
    # Add API key as query param
    params['api_key'] = session['api_key']
    
    try:
        app.logger.info(f"Making {method} request to: {endpoint}")
        
        if method.lower() == 'get':
            response = requests.get(url, headers=headers, params=params)
        elif method.lower() == 'post':
            response = requests.post(url, headers=headers, params=params, json=data)
        elif method.lower() == 'put':
            response = requests.put(url, headers=headers, params=params, json=data)
        elif method.lower() == 'delete':
            response = requests.delete(url, headers=headers, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        # Log the response status
        app.logger.info(f"Response status: {response.status_code}")
        
        # Check for errors
        if response.status_code >= 400:
            app.logger.error(f"API Error: {response.status_code}, Response: {response.text}")
            
        return response
        
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request error: {str(e)}")
        raise

# Add this improved extraction function that logs and handles more edge cases
# Update the extract_field_value function to better handle nested fields
def extract_field_value(lead, possible_fields, nested_paths=None, idx=None):
    """Extract a value from a lead dict with detailed logging for troubleshooting."""
    if nested_paths is None:
        nested_paths = ['contact', 'person', 'profile', 'user', 'details', 'info', 'lead']  # Added 'lead' to check
    
    if not isinstance(lead, dict):
        if idx is not None:
            app.logger.warning(f"Lead {idx} is not a dictionary: {lead}")
        return ""
    
    # Log the lead structure to understand what we're working with
    if idx is not None and idx < 3:  # Log only first few leads to avoid flooding
        app.logger.debug(f"Lead {idx} structure: {lead.keys()}")
    
    # First try direct access
    for field in possible_fields:
        if field in lead:
            value = lead[field]
            if value: # Make sure it's not empty
                if idx is not None and idx < 3:
                    app.logger.debug(f"Found direct field '{field}' in lead {idx}: {value}")
                return value
    
    # Then try nested paths - enhance this section to handle discovered nested paths
    for path in nested_paths:
        if path in lead and isinstance(lead[path], dict):
            nested_obj = lead[path]
            for field in possible_fields:
                if field in nested_obj and nested_obj[field]:
                    value = nested_obj[field]
                    if idx is not None and idx < 3:
                        app.logger.debug(f"Found field '{field}' in nested path '{path}' for lead {idx}: {value}")
                    return value
    
    # Last resort: try to match field substring
    for key, value in lead.items():
        if isinstance(value, str) and value:
            for field_name in possible_fields:
                if field_name.lower() in key.lower():
                    if idx is not None and idx < 3:
                        app.logger.debug(f"Found match by key name similarity '{key}' for lead {idx}: {value}")
                    return value
    
    # Special case for email fields: try to find anything that looks like an email
    if 'email' in possible_fields[0].lower():
        for key, value in lead.items():
            if isinstance(value, str) and '@' in value and '.' in value:
                if idx is not None and idx < 3:
                    app.logger.debug(f"Found email-like value in field '{key}' for lead {idx}: {value}")
                return value
    
    # Special case for company name - sometimes stored in unexpected fields
    if 'company' in possible_fields[0].lower():
        # Common variations of company field names
        company_indicators = ['company', 'organization', 'employer', 'firm', 'workplace', 'business']
        
        # Try to find any field containing these indicators
        for key, value in lead.items():
            if isinstance(value, str) and value:
                for indicator in company_indicators:
                    if indicator.lower() in key.lower():
                        if idx is not None and idx < 3:
                            app.logger.debug(f"Found company by field name match '{key}': {value}")
                        return value
    
    # Return empty string as fallback
    return ""

# Routes
@app.route('/')
def index():
    if 'api_key' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        
        # Validate the API key by making a test call
        try:
            response = requests.get(f"https://server.smartlead.ai/api/v1/campaigns?api_key={api_key}")
            if response.status_code == 200:
                session['api_key'] = api_key
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid API key', 'danger')
        except Exception as e:
            flash(f'Error connecting to Smartlead: {str(e)}', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('api_key', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get campaigns with fresh data
        response = api_request('get', "campaigns")
        campaigns = response.json() if response.status_code == 200 else []
        
        # Update lead counts for each campaign by fetching individual details
        for i, campaign in enumerate(campaigns):
            try:
                # Make an explicit request to get lead count for this campaign
                campaign_detail_response = api_request('get', f"campaigns/{campaign['id']}") 
                if campaign_detail_response.status_code == 200:
                    campaign_detail = campaign_detail_response.json()
                    
                    # If lead_count is not available in details, try to count the actual leads
                    if 'lead_count' not in campaign_detail or not campaign_detail['lead_count']:
                        app.logger.info(f"Campaign {campaign['id']} missing lead_count, fetching leads directly")
                        # Try to get leads to count them
                        leads_response = api_request('get', f"campaigns/{campaign['id']}/leads")
                        if leads_response.status_code == 200:
                            leads_data = leads_response.json()
                            if isinstance(leads_data, dict) and 'data' in leads_data:
                                campaigns[i]['lead_count'] = len(leads_data.get('data', []))
                                app.logger.info(f"Found {campaigns[i]['lead_count']} leads via data field")
                            elif isinstance(leads_data, list):
                                campaigns[i]['lead_count'] = len(leads_data)
                                app.logger.info(f"Found {campaigns[i]['lead_count']} leads via direct list")
                            elif isinstance(leads_data, dict) and 'total_leads' in leads_data:
                                campaigns[i]['lead_count'] = leads_data['total_leads']
                                app.logger.info(f"Found {campaigns[i]['lead_count']} leads via total_leads field")
                    else:
                        campaigns[i]['lead_count'] = campaign_detail.get('lead_count', 0)
                        app.logger.info(f"Campaign {campaign['id']} reports {campaigns[i]['lead_count']} leads")
            except Exception as e:
                app.logger.error(f"Error updating lead count for campaign {campaign['id']}: {str(e)}")
                # Ensure we have a default value
                if 'lead_count' not in campaigns[i]:
                    campaigns[i]['lead_count'] = 0
        
        # Get email accounts
        email_accounts_response = api_request('get', "email-accounts")
        email_accounts = email_accounts_response.json() if email_accounts_response.status_code == 200 else []
        
        # Calculate total leads across all campaigns using updated counts
        total_leads = sum(campaign.get('lead_count', 0) for campaign in campaigns)
        
        return render_template('dashboard.html', 
                              campaigns=campaigns, 
                              email_accounts=email_accounts,
                              total_leads=total_leads)
    except Exception as e:
        app.logger.error(f"Dashboard error: {str(e)}")
        flash(f'Error fetching campaigns: {str(e)}', 'danger')
        return render_template('dashboard.html', 
                              campaigns=[], 
                              email_accounts=[],
                              total_leads=0)

@app.route('/campaigns')
@login_required
def campaigns():
    try:
        # Get campaigns
        response = api_request('get', "campaigns")
        campaigns = response.json() if response.status_code == 200 else []
        
        # Fetch individual campaign details to get accurate lead counts
        for i, campaign in enumerate(campaigns):
            try:
                campaign_detail_response = api_request('get', f"campaigns/{campaign['id']}")
                if campaign_detail_response.status_code == 200:
                    campaign_detail = campaign_detail_response.json()
                    # Update the lead count
                    campaigns[i]['lead_count'] = campaign_detail.get('lead_count', 0)
            except Exception as e:
                app.logger.error(f"Error fetching campaign details for ID {campaign['id']}: {str(e)}")
        
        # Find the max lead count for progress bar display
        max_leads = max((campaign.get('lead_count', 0) for campaign in campaigns), default=1)
        
        # Fetch email accounts for each campaign
        for campaign in campaigns:
            try:
                # Get email accounts for this campaign
                accounts_response = api_request('get', f"campaigns/{campaign['id']}/email-accounts")
                if accounts_response.status_code == 200:
                    email_accounts = accounts_response.json()
                    campaign['email_accounts'] = email_accounts
                    app.logger.info(f"Campaign {campaign['id']} has {len(email_accounts)} email accounts")
                else:
                    campaign['email_accounts'] = []
            except Exception as e:
                app.logger.error(f"Error fetching email accounts for campaign {campaign['id']}: {str(e)}")
                campaign['email_accounts'] = []
        
        return render_template('campaigns.html', campaigns=campaigns, max_leads=max_leads)
    except Exception as e:
        flash(f'Error fetching campaigns: {str(e)}', 'danger')
        return render_template('campaigns.html', campaigns=[], max_leads=1)

@app.route('/campaigns/create', methods=['GET', 'POST'])
@login_required
def create_campaign():
    if request.method == 'POST':
        campaign_name = request.form.get('name')
        data = {
            "name": campaign_name,
            "client_id": None,
        }
        
        try:
            response = requests.post(
                f"https://server.smartlead.ai/api/v1/campaigns/create?api_key={session['api_key']}", 
                data=data
            )
            
            if response.status_code == 200:
                flash('Campaign created successfully!', 'success')
                return redirect(url_for('campaigns'))
            else:
                flash(f'Error creating campaign: {response.text}', 'danger')
        except Exception as e:
            flash(f'Error creating campaign: {str(e)}', 'danger')
            
    return render_template('create_campaign.html')

# Update the view_campaign function with better lead handling
@app.route('/campaigns/<int:campaign_id>')
@login_required
def view_campaign(campaign_id):
    try:
        # Get campaign details
        app.logger.info(f"Fetching campaign with ID: {campaign_id}")
        campaign_response = api_request('get', f"campaigns/{campaign_id}")
        
        if campaign_response.status_code != 200:
            flash(f'Error fetching campaign details: API returned {campaign_response.status_code}', 'danger')
            return redirect(url_for('campaigns'))
            
        # Parse the campaign details
        try:
            campaign = campaign_response.json()
        except ValueError:
            flash(f'Error parsing campaign details: Invalid JSON response', 'danger')
            return redirect(url_for('campaigns'))
        
        # Enhanced lead handling with detailed debugging
        try:
            leads_response = api_request('get', f"campaigns/{campaign_id}/leads")
            leads_data = leads_response.json() if leads_response.status_code == 200 else []
            
            # Log the raw data structure details 
            app.logger.info(f"Raw leads response status: {leads_response.status_code}")
            app.logger.info(f"Raw leads data type: {type(leads_data)}")
            
            if isinstance(leads_data, dict):
                app.logger.info(f"Leads data keys: {list(leads_data.keys())}")
                # Log the total count if available
                if 'total_leads' in leads_data:
                    app.logger.info(f"API reports total_leads: {leads_data['total_leads']}")
                
                # If we have array data, log the first item structure
                if 'data' in leads_data and isinstance(leads_data['data'], list) and leads_data['data']:
                    first_lead = leads_data['data'][0]
                    app.logger.info(f"First lead structure from data array: {list(first_lead.keys())}")
                    app.logger.debug(f"First lead full content: {json.dumps(first_lead)}")
            
            # Extract leads list from whatever structure we got
            if isinstance(leads_data, dict):
                # Try all possible locations
                for possible_key in ['data', 'leads', 'items', 'results', 'response']:
                    if possible_key in leads_data and isinstance(leads_data[possible_key], list):
                        leads = leads_data[possible_key]
                        app.logger.info(f"Found {len(leads)} leads in '{possible_key}' field")
                        break
                else:
                    leads = []
                    app.logger.warning("No leads list found in the API response")
            else:
                leads = leads_data
                app.logger.info(f"Direct access found {len(leads)} leads")
            
            # Log the lead structure so we know what fields to extract
            if leads and len(leads) > 0:
                # Create detailed field analysis
                field_analysis = {}
                nested_analysis = {}
                
                for idx, lead in enumerate(leads[:5]):  # Look at first 5 leads
                    if isinstance(lead, dict):
                        app.logger.debug(f"Lead {idx} keys: {list(lead.keys())}")
                        
                        # Track what fields exist
                        for key, value in lead.items():
                            field_analysis[key] = field_analysis.get(key, 0) + 1
                            
                            # Look for email-like values to help with extraction
                            if isinstance(value, str) and '@' in value:
                                app.logger.info(f"Found email-like value in field '{key}': {value}")
                            
                            # Check nested objects too
                            if isinstance(value, dict):
                                if key not in nested_analysis:
                                    nested_analysis[key] = {}
                                for nested_key, nested_val in value.items():
                                    nested_analysis[key][nested_key] = nested_analysis[key].get(nested_key, 0) + 1
                                    # Look for email-like values in nested objects
                                    if isinstance(nested_val, str) and '@' in nested_val:
                                        app.logger.info(f"Found email-like value in nested field '{key}.{nested_key}': {nested_val}")
                
                app.logger.info(f"Fields present in leads: {field_analysis}")
                app.logger.info(f"Nested fields structure: {nested_analysis}")
            
            # Create more diverse field mappings based on what we learned
            field_mapping = {
                'first_name': ['first_name', 'firstName', 'fname', 'given_name', 'first', 'name_first', 'forename', 'first name'],
                'last_name': ['last_name', 'lastName', 'lname', 'surname', 'family_name', 'last', 'name_last', 'last name'],
                'name': ['name', 'full_name', 'display_name', 'contact_name', 'person_name', 'fullname', 'displayname', 'lead_name'],
                'email': ['email', 'emailAddress', 'email_address', 'mail', 'primary_email', 'contact_email', 
                          'user_email', 'email_primary', 'person_email', 'work_email', 'business_email', 'reply_to'],
                'company': ['company', 'company_name', 'companyName', 'organization', 'organisation', 'employer', 
                           'firm', 'business', 'workplace', 'work', 'business_name', 'company name', 'org', 
                           'corporation', 'enterprise', 'establishment']
            }
            
            # Process each lead with extensively improved extraction
            processed_leads = []
            for idx, lead in enumerate(leads[:100]):  # Limit to first 100 leads
                if not isinstance(lead, dict):
                    app.logger.warning(f"Skipping lead {idx} because it's not a dictionary")
                    continue
                
                # Create a clean normalized lead
                normalized_lead = {}
                
                # Copy important fields
                normalized_lead['id'] = lead.get('id', idx)
                normalized_lead['status'] = lead.get('status', 'UNKNOWN')
                
                # First check if there's a 'lead' nested object with the email
                if 'lead' in lead and isinstance(lead['lead'], dict) and 'email' in lead['lead']:
                    email = lead['lead']['email']
                    if email:
                        app.logger.debug(f"Found email directly in lead.email for lead {idx}: {email}")
                        normalized_lead['email'] = email
                        
                        # Also check for name and company in the same nested object
                        if 'first_name' in lead['lead']:
                            normalized_lead['first_name'] = lead['lead']['first_name']
                        if 'last_name' in lead['lead']:
                            normalized_lead['last_name'] = lead['lead']['last_name']
                        if 'company' in lead['lead'] or 'company_name' in lead['lead']:
                            normalized_lead['company'] = lead['lead'].get('company') or lead['lead'].get('company_name')
                
                # If we didn't find email in lead.email, try our regular extraction
                if 'email' not in normalized_lead:
                    email = extract_field_value(lead, field_mapping['email'], idx=idx)
                    if email:
                        normalized_lead['email'] = email
                    else:
                        app.logger.warning(f"No email found for lead {idx}")
                        # Try harder with pattern matching - be extra aggressive
                        for key, value in lead.items():
                            if isinstance(value, str) and '@' in value and '.' in value:
                                normalized_lead['email'] = value
                                app.logger.info(f"Found email by pattern matching in field '{key}': {value}")
                                break
                            elif isinstance(value, dict):
                                # Look in nested dictionary
                                for nk, nv in value.items():
                                    if isinstance(nv, str) and '@' in nv and '.' in nv:
                                        normalized_lead['email'] = nv
                        name_parts = full_name.strip().split(maxsplit=1)
                        if name_parts:
                            normalized_lead['first_name'] = name_parts[0]
                            if len(name_parts) > 1:
                                normalized_lead['last_name'] = name_parts[1]
                
                # Extract company name
                company = extract_field_value(lead, field_mapping['company'], idx=idx)
                if company:
                    normalized_lead['company'] = company
                else:
                    # Try much harder to find company information
                    for key, value in lead.items():
                        if isinstance(value, str) and len(value) > 3:  # Ignore very short values
                            # Check if key contains company-related terms
                            if any(term in key.lower() for term in ['company', 'org', 'business', 'employer', 'workplace']):
                                normalized_lead['company'] = value
                                app.logger.info(f"Found company by extended field search: {key} = {value}")
                                break
                
                # Additional context: extract title/position if available
                title_mapping = ['title', 'job_title', 'position', 'role', 'occupation']
                title = extract_field_value(lead, title_mapping, idx=idx)
                if title:
                    normalized_lead['title'] = title
                
                # Store the processed lead
                processed_leads.append(normalized_lead)
            
            # Replace with normalized leads
            leads = processed_leads
            
            # Log summary statistics
            name_count = sum(1 for lead in leads if lead.get('first_name') or lead.get('last_name'))
            email_count = sum(1 for lead in leads if lead.get('email'))
            app.logger.info(f"Summary: Found {name_count}/{len(leads)} leads with names and {email_count}/{len(leads)} with emails")
            
            # If we found zero emails, this is critical - log the raw lead data to understand the structure
            if email_count == 0 and leads:
                app.logger.critical(f"Failed to extract ANY emails. Raw lead sample: {json.dumps(leads_data['data'][0] if isinstance(leads_data, dict) and 'data' in leads_data else leads_data[0])}")
                
        except Exception as e:
            app.logger.error(f"Error processing leads data: {str(e)}", exc_info=True)
            leads = []
        
        # Get campaign sequences
        try:
            sequences_response = api_request('get', f"campaigns/{campaign_id}/sequences")
            sequences = sequences_response.json() if sequences_response.status_code == 200 else []
        except Exception as e:
            app.logger.error(f"Error fetching sequences: {str(e)}")
            sequences = []
        
        # Get email accounts explicitly
        try:
            accounts_response = api_request('get', f"campaigns/{campaign_id}/email-accounts")
            if accounts_response.status_code == 200:
                email_accounts = accounts_response.json()
                # Manually set the email accounts in the campaign object
                campaign['email_accounts'] = email_accounts
                app.logger.info(f"Found {len(email_accounts)} email accounts for campaign")
        except Exception as e:
            app.logger.error(f"Error fetching email accounts: {str(e)}")
        
        # Calculate statistics
        total_leads = len(leads)
        opened_count = sum(1 for lead in leads if isinstance(lead, dict) and lead.get('status') == 'OPENED')
        replied_count = sum(1 for lead in leads if isinstance(lead, dict) and lead.get('status') == 'REPLIED')
        bounced_count = sum(1 for lead in leads if isinstance(lead, dict) and lead.get('status') == 'BOUNCED')
        
        # Calculate rates (protect against division by zero)
        total_leads_for_calc = max(total_leads, 1)
        
        campaign_stats = {
            'open_rate': round((opened_count / total_leads_for_calc) * 100, 1),
            'reply_rate': round((replied_count / total_leads_for_calc) * 100, 1),
            'bounce_rate': round((bounced_count / total_leads_for_calc) * 100, 1)
        }
        
        return render_template('view_campaign.html', 
                              campaign=campaign,
                              leads=leads,
                              sequences=sequences,
                              campaign_stats=campaign_stats)
    
    except Exception as e:
        app.logger.error(f"Error viewing campaign: {str(e)}")
        flash(f'Error fetching campaign details: {str(e)}', 'danger')
        return redirect(url_for('campaigns'))

@app.route('/campaigns/<int:campaign_id>/upload-leads', methods=['GET', 'POST'])
@login_required
def upload_leads(campaign_id):
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No file selected', 'warning')
            return redirect(request.url)
            
        file = request.files['csv_file']
        
        if file.filename == '':
            flash('No file selected', 'warning')
            return redirect(request.url)
        
        if file:
            try:
                # Process the CSV file
                df = pd.read_csv(io.StringIO(file.stream.read().decode('utf-8')))
                
                # Convert to the required format
                leads = []
                for _, row in df.iterrows():
                    lead = {
                        "first_name": row.get("First Name", ""),
                        "last_name": row.get("Last Name", ""),
                        "email": row.get("Email", ""),
                        "phone_number": row.get("Phone Number", ""),
                        "company_name": row.get("Company Name", ""),
                        "website": row.get("Website", ""),
                        "location": row.get("Country", ""),
                        "linkedin_profile": row.get("Linkedin Profile", ""),
                        "company_url": row.get("Company Url", "")
                    }
                    leads.append(lead)
                
                # Get form settings
                ignore_global_block_list = 'ignore_global_block_list' in request.form
                ignore_unsubscribe_list = 'ignore_unsubscribe_list' in request.form
                ignore_community_bounce_list = 'ignore_community_bounce_list' in request.form
                ignore_duplicate_leads = 'ignore_duplicate_leads' in request.form
                
                # Upload leads
                data = {
                    "lead_list": leads,
                    "settings": {
                        "ignore_global_block_list": ignore_global_block_list,
                        "ignore_unsubscribe_list": ignore_unsubscribe_list,
                        "ignore_community_bounce_list": ignore_community_bounce_list,
                        "ignore_duplicate_leads_in_other_campaign": ignore_duplicate_leads
                    }
                }
                
                response = requests.post(
                    f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/leads?api_key={session['api_key']}",
                    data=json.dumps(data),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    flash(f'Successfully uploaded {result.get("upload_count", 0)} leads!', 'success')
                else:
                    flash(f'Error uploading leads: {response.text}', 'danger')
                
                return redirect(url_for('view_campaign', campaign_id=campaign_id))
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
            
    return render_template('upload_leads.html', campaign_id=campaign_id)

@app.template_filter('date')
def format_date(value):
    """Format a date string from ISO format to YYYY-MM-DD"""
    if not value:
        return ""
    try:
        # Handle both date strings and datetime objects
        if isinstance(value, str):
            return value.split('T')[0]
        else:
            return value.strftime('%Y-%m-%d')
    except:
        return value

@app.route('/campaigns/<int:campaign_id>/toggle-status', methods=['POST'])
@login_required
def toggle_campaign_status(campaign_id):
    status = request.form.get('status', 'STOP')
    
    try:
        data = {
            "status": status
        }
        
        response = requests.post(
            f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/status?api_key={session['api_key']}",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            flash('Campaign status updated successfully!', 'success')
        else:
            flash(f'Error updating campaign status: {response.text}', 'danger')
            
    except Exception as e:
        flash(f'Error updating campaign status: {str(e)}', 'danger')
        
    return redirect(url_for('view_campaign', campaign_id=campaign_id))

@app.route('/campaigns/<int:campaign_id>/sequences/create', methods=['GET', 'POST'])
@login_required
def create_sequence(campaign_id):
    if request.method == 'POST':
        try:
            # Handle JSON data from the form
            data = request.get_json()
            
            response = requests.post(
                f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/sequences?api_key={session['api_key']}",
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return jsonify({"ok": True})
            else:
                return jsonify({"ok": False, "message": response.text})
        except Exception as e:
            return jsonify({"ok": False, "message": str(e)})
            
    return render_template('create_sequence.html', campaign_id=campaign_id)

@app.route('/email-accounts')
@login_required
def email_accounts():
    try:
        response = requests.get(f"https://server.smartlead.ai/api/v1/email-accounts?api_key={session['api_key']}")
        email_accounts = response.json()
        return render_template('email_accounts.html', email_accounts=email_accounts)
    except Exception as e:
        flash(f'Error fetching email accounts: {str(e)}', 'danger')
        return render_template('email_accounts.html', email_accounts=[])

@app.route('/email-accounts/add', methods=['GET', 'POST'])
@login_required
def add_email_account():
    if request.method == 'POST':
        # Extract form data
        account_type = request.form.get('account_type')
        from_name = request.form.get('from_name')
        from_email = request.form.get('from_email')
        message_per_day = int(request.form.get('message_per_day', 200))
        different_reply_to = 'different_reply_to' in request.form
        different_reply_to_address = request.form.get('different_reply_to_address') if different_reply_to else None
        
        # Build data payload
        data = {
            "type": account_type,
            "from_name": from_name,
            "from_email": from_email,
            "message_per_day": message_per_day,
            "different_reply_to_address": different_reply_to_address
        }
        
        # For SMTP accounts, add SMTP settings
        if account_type == 'SMTP':
            data.update({
                "smtp_host": request.form.get('smtp_host'),
                "smtp_port": request.form.get('smtp_port'),
                "username": request.form.get('username'),
                "password": request.form.get('password'),
                "smtp_port_type": request.form.get('smtp_port_type')
            })
        
        try:
            response = requests.post(
                f"https://server.smartlead.ai/api/v1/email-accounts?api_key={session['api_key']}",
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                flash('Email account added successfully!', 'success')
                return redirect(url_for('email_accounts'))
            else:
                flash(f'Error adding email account: {response.text}', 'danger')
        except Exception as e:
            flash(f'Error adding email account: {str(e)}', 'danger')
    
    return render_template('add_email_account.html')

@app.route('/email-accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_email_account(account_id):
    try:
        if request.method == 'POST':
            # Extract form data
            account_type = request.form.get('account_type')
            from_name = request.form.get('from_name')
            from_email = request.form.get('from_email')
            message_per_day = request.form.get('message_per_day')
            different_reply_to = 'different_reply_to' in request.form
            different_reply_to_address = request.form.get('different_reply_to_address') if different_reply_to else None
            
            # Build data payload
            data = {
                "from_name": from_name,
                "message_per_day": message_per_day,
                "different_reply_to_address": different_reply_to_address
            }
            
            # For SMTP accounts, add SMTP settings if provided
            if account_type == 'SMTP':
                smtp_password = request.form.get('password')
                if smtp_password:  # Only update password if provided
                    data["password"] = smtp_password
                
                smtp_data = {
                    "smtp_host": request.form.get('smtp_host'),
                    "smtp_port": request.form.get('smtp_port'),
                    "username": request.form.get('username'),
                    "smtp_port_type": request.form.get('smtp_port_type')
                }
                data.update({k: v for k, v in smtp_data.items() if v})  # Only add non-empty values
            
            response = requests.put(
                f"https://server.smartlead.ai/api/v1/email-accounts/{account_id}?api_key={session['api_key']}",
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                flash('Email account updated successfully!', 'success')
                return redirect(url_for('email_accounts'))
            else:
                flash(f'Error updating email account: {response.text}', 'danger')
        
        # Get email account details for editing
        response = requests.get(f"https://server.smartlead.ai/api/v1/email-accounts/{account_id}?api_key={session['api_key']}")
        account = response.json()
        
        return render_template('edit_email_account.html', account=account)
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('email_accounts'))

@app.route('/email-accounts/<int:account_id>/delete', methods=['POST'])
@login_required
def delete_email_account(account_id):
    try:
        response = requests.delete(f"https://server.smartlead.ai/api/v1/email-accounts/{account_id}?api_key={session['api_key']}")
        
        if response.status_code == 200:
            flash('Email account deleted successfully!', 'success')
        else:
            flash(f'Error deleting email account: {response.text}', 'danger')
    except Exception as e:
        flash(f'Error deleting email account: {str(e)}', 'danger')
    
    return redirect(url_for('email_accounts'))

@app.route('/campaigns/<int:campaign_id>/schedule', methods=['GET', 'POST'])
@login_required
def campaign_schedule(campaign_id):
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Fetch list of timezones from system
    timezones = pytz.all_timezones
    
    try:
        # Get current schedule if it exists
        schedule_response = requests.get(
            f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/schedule?api_key={session['api_key']}"
        )
        schedule = schedule_response.json() if schedule_response.status_code == 200 else None
        
        # Get campaign details for display
        campaign_response = requests.get(
            f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}?api_key={session['api_key']}"
        )
        campaign = campaign_response.json()
        
        if request.method == 'POST':
            # Extract form data
            timezone = request.form.get('timezone')
            days_of_the_week = request.form.getlist('days_of_the_week')
            days_of_the_week = [int(day) for day in days_of_the_week]
            start_hour = request.form.get('start_hour')
            end_hour = request.form.get('end_hour')
            min_time_btw_emails = request.form.get('min_time_btw_emails')
            max_new_leads_per_day = request.form.get('max_new_leads_per_day')
            schedule_start_time = request.form.get('schedule_start_time')
            
            if not schedule_start_time:
                schedule_start_time = None
            
            # Build schedule data
            schedule_data = {
                "timezone": timezone,
                "days_of_the_week": days_of_the_week,
                "start_hour": start_hour,
                "end_hour": end_hour,
                "min_time_btw_emails": int(min_time_btw_emails),
                "max_new_leads_per_day": int(max_new_leads_per_day),
                "schedule_start_time": schedule_start_time
            }
            
            response = requests.post(
                f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/schedule?api_key={session['api_key']}",
                data=json.dumps(schedule_data),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                flash('Campaign schedule updated successfully!', 'success')
                return redirect(url_for('view_campaign', campaign_id=campaign_id))
            else:
                flash(f'Error updating campaign schedule: {response.text}', 'danger')
        
        return render_template('campaign_schedule.html', 
                              campaign=campaign,
                              schedule=schedule,
                              days_of_week=days_of_week,
                              timezones=timezones)
    
    except Exception as e:
        flash(f'Error managing campaign schedule: {str(e)}', 'danger')
        return redirect(url_for('view_campaign', campaign_id=campaign_id))

@app.route('/campaigns/<int:campaign_id>/email-accounts', methods=['GET', 'POST'])
@login_required
def manage_email_accounts(campaign_id):
    try:
        # Get campaign details
        campaign_response = api_request('get', f"campaigns/{campaign_id}")
        if campaign_response.status_code != 200:
            flash(f'Error fetching campaign: API returned {campaign_response.status_code}', 'danger')
            return redirect(url_for('campaigns'))
        campaign = campaign_response.json()
        
        # Get all email accounts
        all_accounts_response = api_request('get', "email-accounts")
        all_email_accounts = all_accounts_response.json() if all_accounts_response.status_code == 200 else []
        
        # Get campaign's assigned email accounts
        campaign_accounts_response = api_request('get', f"campaigns/{campaign_id}/email-accounts")
        if campaign_accounts_response.status_code != 200:
            campaign_account_ids = []
        else:
            try:
                campaign_email_accounts = campaign_accounts_response.json()
                campaign_account_ids = [account['id'] for account in campaign_email_accounts if isinstance(account, dict) and 'id' in account]
            except (ValueError, KeyError, TypeError) as e:
                app.logger.error(f"Error processing campaign email accounts: {e}")
                campaign_account_ids = []
        
        # Handle form submission
        if request.method == 'POST':
            # Get selected email account IDs
            email_account_ids = request.form.getlist('email_account_ids')
            
            # Handle case when none are selected
            if not email_account_ids:
                email_account_ids = []
            else:
                try:
                    email_account_ids = [int(id) for id in email_account_ids]
                except ValueError:
                    flash('Invalid email account IDs submitted', 'danger')
                    return redirect(url_for('view_campaign', campaign_id=campaign_id))
            
            # Update assigned email accounts
            data = {
                "email_account_ids": email_account_ids
            }
            app.logger.info(f"Updating email accounts for campaign {campaign_id} with: {email_account_ids}")
            
            response = api_request('post', f"campaigns/{campaign_id}/email-accounts", data=data)
            if response.status_code == 200:
                flash('Email accounts updated successfully!', 'success')
                # Wait for API to process
                time.sleep(2)
                
                # Try to refresh campaign data
                try:
                    refresh_response = api_request('post', f"campaigns/{campaign_id}/refresh")
                    app.logger.info(f"Campaign refresh status: {refresh_response.status_code}")
                except Exception as e:
                    app.logger.error(f"Error refreshing campaign: {e}")
                
                return redirect(url_for('view_campaign', campaign_id=campaign_id))
            else:
                app.logger.error(f"Error updating email accounts: {response.text}")
                flash(f'Error updating email accounts: {response.text}', 'danger')
        
        return render_template('manage_email_accounts.html',
                              campaign=campaign,
                              all_email_accounts=all_email_accounts,
                              campaign_account_ids=campaign_account_ids)
    
    except Exception as e:
        app.logger.error(f"Error managing email accounts: {str(e)}")
        flash(f'Error managing email accounts: {str(e)}', 'danger')
        return redirect(url_for('campaigns'))

def update_campaign_email_accounts(campaign_id, email_account_ids):
    """Explicitly update campaign's email accounts in the database."""
    try:
        # Get details of assigned email accounts
        if email_account_ids:
            accounts_list = []
            for account_id in email_account_ids:
                try:
                    account_response = requests.get(
                        f"https://server.smartlead.ai/api/v1/email-accounts/{account_id}?api_key={session['api_key']}"
                    )
                    if account_response.status_code == 200:
                        accounts_list.append(account_response.json())
                except Exception as e:
                    app.logger.error(f"Failed to fetch email account {account_id}: {str(e)}")
            
            app.logger.info(f"Retrieved {len(accounts_list)} email accounts for campaign {campaign_id}")
            
            # Wait for the API to process changes
            time.sleep(1)
            
            # Explicitly refresh campaign
            try:
                refresh_response = requests.post(
                    f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/refresh?api_key={session['api_key']}"
                )
                app.logger.info(f"Campaign refresh result: {refresh_response.status_code}")
            except Exception as e:
                app.logger.error(f"Failed to refresh campaign: {str(e)}")
    except Exception as e:
        app.logger.error(f"Error updating campaign email accounts: {str(e)}")

@app.route('/api/campaign-stats/<int:campaign_id>')
@login_required
def campaign_stats_api(campaign_id):
    """API endpoint for fetching campaign stats via AJAX"""
    try:
        # Get campaign leads
        leads_response = requests.get(
            f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/leads?api_key={session['api_key']}"
        )
        
        if leads_response.status_code != 200:
            app.logger.error(f"Failed to fetch campaign leads: {leads_response.status_code}, {leads_response.text}")
            return jsonify({
                'success': False,
                'message': f'Failed to fetch campaign leads: {leads_response.status_code}'
            }), 500
        
        # Safely parse JSON response
        try:
            leads_data = leads_response.json()
        except ValueError as e:
            app.logger.error(f"Failed to parse leads response as JSON: {e}")
            return jsonify({
                'success': False,
                'message': 'Failed to parse leads data'
            }), 500
            
        # Handle if leads_data is a dict instead of a list
        if isinstance(leads_data, dict):
            app.logger.info(f"Stats: Leads data is a dict with keys: {leads_data.keys()}")
            # Extract leads from the 'data' field if it exists
            if 'data' in leads_data and isinstance(leads_data['data'], list):
                leads = leads_data['data']
            elif 'error' in leads_data:
                return jsonify({
                    'success': False,
                    'message': leads_data['error']
                }), 500
            else:
                # Default to empty list if we can't extract leads
                leads = []
        else:
            leads = leads_data
        
        # Calculate statistics - ensure each lead is a valid dictionary
        total_leads = len(leads)
        
        leads_by_status = {}
        for lead in leads:
            if not isinstance(lead, dict):
                continue  # Skip non-dict leads
            
            status = lead.get('status', 'unknown')
            if status in leads_by_status:
                leads_by_status[status] += 1
            else:
                leads_by_status[status] = 1
        
        # Calculate rates (protect against division by zero)
        total_leads_for_calc = max(total_leads, 1)
        
        stats = {
            'total_leads': total_leads,
            'leads_by_status': leads_by_status,
            'rates': {
                'open_rate': round((leads_by_status.get('OPENED', 0) / total_leads_for_calc) * 100, 1),
                'reply_rate': round((leads_by_status.get('REPLIED', 0) / total_leads_for_calc) * 100, 1),
                'bounce_rate': round((leads_by_status.get('BOUNCED', 0) / total_leads_for_calc) * 100, 1),
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        app.logger.error(f"Error fetching campaign stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/check-api')
@login_required
def check_api():
    """Helper route to check API status and configuration"""
    try:
        # Check basic API connectivity
        response = requests.get(f"https://server.smartlead.ai/api/v1/campaigns?api_key={session['api_key']}")
        status = response.status_code
        
        if status == 200:
            # Try to get a single campaign to test detailed access
            campaigns = response.json()
            if campaigns and len(campaigns) > 0:
                campaign_id = campaigns[0]['id']
                campaign_response = requests.get(
                    f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}?api_key={session['api_key']}"
                )
                campaign_status = campaign_response.status_code
                campaign_text = campaign_response.text[:200] + "..." if len(campaign_response.text) > 200 else campaign_response.text
            else:
                campaign_status = "No campaigns found"
                campaign_text = "N/A"
        else:
            campaign_status = "Skipped (API connection failed)"
            campaign_text = "N/A"
        
        # Return API status information
        return jsonify({
            'api_check': {
                'campaigns_list_status': status,
                'single_campaign_status': campaign_status,
                'campaign_response_excerpt': campaign_text,
                'api_key_length': len(session['api_key']) if 'api_key' in session else 0,
                'api_key_format': 'Looks valid' if len(session['api_key']) > 20 else 'Suspicious (too short)'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/campaigns/<int:campaign_id>/debug-leads')
@login_required
def debug_leads(campaign_id):
    try:
        leads_response = api_request('get', f"campaigns/{campaign_id}/leads")
        leads_data = leads_response.json() if leads_response.status_code == 200 else []
        total_leads = len(leads_data)
        field_stats = {}
        sample_lead = leads_data[0] if total_leads > 0 else {}
        
        for lead in leads_data:
            if isinstance(lead, dict):
                for field in lead.keys():
                    field_stats[field] = field_stats.get(field, 0) + 1
                    if field == 'contact' and isinstance(lead['contact'], dict):
                        for nested_field in lead['contact'].keys():
                            nested_key = f"contact.{nested_field}"
                            field_stats[nested_key] = field_stats.get(nested_key, 0) + 1
        
        return render_template('debug_leads.html', 
                              campaign_id=campaign_id, 
                              leads=leads_data, 
                              field_stats=field_stats, 
                              total_leads=total_leads, 
                              sample_lead=sample_lead)
    except Exception as e:
        app.logger.error(f"Error debugging leads: {str(e)}")
        flash(f'Error debugging leads: {str(e)}', 'danger')
        return redirect(url_for('view_campaign', campaign_id=campaign_id))

@app.route('/campaigns/<int:campaign_id>/lead/<int:lead_id>')
@login_required
def debug_lead_item(campaign_id, lead_id):
    try:
        leads_response = api_request('get', f"campaigns/{campaign_id}/leads")
        leads_data = leads_response.json() if leads_response.status_code == 200 else []
        
        if isinstance(leads_data, dict) and 'data' in leads_data:
            leads = leads_data['data']
        else:
            leads = leads_data
        
        # Find the specific lead by ID
        lead = next((l for l in leads if l.get('id') == lead_id), None)
        
        if not lead:
            flash('Lead not found', 'danger')
            return redirect(url_for('debug_leads', campaign_id=campaign_id))
        
        return render_template('debug_lead_item.html', 
                              campaign_id=campaign_id, 
                              lead=lead)
    except Exception as e:
        app.logger.error(f"Error debugging lead: {str(e)}")
        flash(f'Error debugging lead: {str(e)}', 'danger')
        return redirect(url_for('debug_leads', campaign_id=campaign_id))

@app.route('/api/lead-counts')
@login_required
def api_lead_counts():
    """API endpoint for refreshing lead counts"""
    try:
        # Get campaigns 
        response = api_request('get', "campaigns")
        campaigns = response.json() if response.status_code == 200 else []
        
        # Initialize counts
        total_leads = 0
        campaign_counts = {}
        
        # Update lead counts for each campaign
        for campaign in campaigns:
            try:
                # Get campaign details to get lead count
                campaign_detail_response = api_request('get', f"campaigns/{campaign['id']}")
                if campaign_detail_response.status_code == 200:
                    campaign_detail = campaign_detail_response.json()
                    lead_count = campaign_detail.get('lead_count', 0)
                    
                    # Update campaign count
                    campaign_counts[campaign['id']] = lead_count
                    # Add to total
                    total_leads += lead_count
            except Exception as e:
                app.logger.error(f"Error fetching lead count for campaign {campaign['id']}: {str(e)}")
        
        return jsonify({
            'success': True,
            'total_leads': total_leads,
            'campaign_counts': campaign_counts
        })
    except Exception as e:
        app.logger.error(f"Error fetching lead counts: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)