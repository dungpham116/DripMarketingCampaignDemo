from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app import db
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.email_template import EmailTemplate, EmailSequence
from app.smartlead_api import SmartleadAPI
import pandas as pd
import os
import json

bp = Blueprint('campaign', __name__, url_prefix='/campaign')
smartlead = SmartleadAPI()

@bp.route('/')
@login_required
def index():
    # Get campaigns from SmartLead
    try:
        smartlead_campaigns = smartlead.get_campaigns()
        
        # Create or update local campaign records
        for sl_campaign in smartlead_campaigns:
            campaign = Campaign.query.filter_by(smartlead_id=sl_campaign['id']).first()
            if not campaign:
                campaign = Campaign(
                    name=sl_campaign['name'],
                    smartlead_id=sl_campaign['id'], 
                    status=sl_campaign['status'].lower()
                )
                db.session.add(campaign)
        
        db.session.commit()
    except Exception as e:
        flash(f"Error syncing with SmartLead: {str(e)}", "error")
    
    # Get updated campaigns from database with any local relationships
    campaigns = Campaign.query.all()
    return render_template('campaign/index.html', campaigns=campaigns)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        # Create campaign on SmartLead
        try:
            response = smartlead.create_campaign(name)
            
            if response.get('ok'):
                # Create local record
                campaign = Campaign(
                    name=name, 
                    description=description,
                    smartlead_id=response.get('id')
                )
                db.session.add(campaign)
                db.session.commit()
                
                flash('Campaign created successfully!', 'success')
                return redirect(url_for('campaign.setup_sequence', campaign_id=campaign.id))
            else:
                flash(f"Error creating campaign on SmartLead: {response.get('error', 'Unknown error')}", 'error')
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
            
    return render_template('campaign/create.html')

@bp.route('/<int:campaign_id>/upload-contacts', methods=['GET', 'POST'])
@login_required
def upload_contacts(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
            
        if file and file.filename.endswith('.csv'):
            try:
                # Read CSV
                df = pd.read_csv(file)
                
                # Format leads for SmartLead API
                leads = []
                for _, row in df.iterrows():
                    lead = {
                        "first_name": str(row.get('first_name', '')),
                        "last_name": str(row.get('last_name', '')),
                        "email": str(row.get('email', '')),
                        "company_name": str(row.get('company_name', ''))
                    }
                    leads.append(lead)
                    
                    # Also create local record for UI purposes
                    contact = Contact(
                        first_name=str(row.get('first_name', '')),
                        last_name=str(row.get('last_name', '')),
                        email=str(row.get('email', '')),
                        campaign_id=campaign_id
                    )
                    db.session.add(contact)
                
                # Upload leads to SmartLead
                response = smartlead.upload_leads(campaign.smartlead_id, leads)
                
                if response.get('ok'):
                    db.session.commit()
                    flash(f"Uploaded {response.get('upload_count', 0)} contacts successfully!", 'success')
                    return redirect(url_for('campaign.view', campaign_id=campaign_id))
                else:
                    db.session.rollback()
                    flash(f"Error uploading contacts to SmartLead: {response}", 'error')
                
            except Exception as e:
                flash(f'Error importing contacts: {str(e)}', 'error')
                
    return render_template('campaign/upload_contacts.html', campaign_id=campaign_id)

@bp.route('/<int:campaign_id>/setup_sequence', methods=['GET', 'POST'])
@login_required
def setup_sequence(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    templates = EmailTemplate.query.all()
    
    if request.method == 'POST':
        # Parse the advanced sequence data
        sequence_data_json = request.form.get('sequence_data')
        if sequence_data_json:
            sequence_data = json.loads(sequence_data_json)
            
            # Save locally first
            # Clear existing sequences
            EmailSequence.query.filter_by(campaign_id=campaign.id).delete()
            
            # Add main sequence
            for step in sequence_data['main_sequence']:
                sequence = EmailSequence(
                    campaign_id=campaign.id,
                    template_id=step['template_id'],
                    delay_days=step['delay_days'],
                    delay_hours=step['delay_hours'],
                    delay_minutes=step['delay_minutes'],
                    sequence_order=step['sequence_order']
                )
                db.session.add(sequence)
            
            # Save branches in JSON format to campaign 
            campaign.branch_data_json = json.dumps(sequence_data['branches'])
            
            db.session.commit()
            
            # Now save to SmartLead
            # Format sequence data for SmartLead API
            smartlead_sequence = {
                "main_sequence": sequence_data['main_sequence'],
                "branches": sequence_data['branches']
            }
            
            try:
                # Send to SmartLead API
                response = smartlead.create_advanced_sequence(campaign.smartlead_id, smartlead_sequence)
                
                if response.get('ok'):
                    flash('Email sequence saved successfully!', 'success')
                else:
                    flash(f"Error saving sequence to SmartLead: {response.get('error', 'Unknown error')}", 'error')
            except Exception as e:
                flash(f"Error: {str(e)}", 'error')
                
            return redirect(url_for('campaign.view', campaign_id=campaign.id))
    
    return render_template('campaign/setup_sequence.html', 
                           campaign=campaign, 
                           templates=templates)

@bp.route('/<int:campaign_id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if campaign.status == 'active':
        try:
            # Pause campaign on SmartLead
            response = smartlead.pause_campaign(campaign.smartlead_id)
            if response.get('ok'):
                campaign.status = 'paused'
                db.session.commit()
                flash('Campaign paused successfully!', 'success')
            else:
                flash(f"Error pausing campaign on SmartLead: {response}", 'error')
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
    else:
        # Check if campaign has templates and contacts before activating
        if not campaign.email_sequences:
            flash('Please set up email sequences before activating the campaign.', 'error')
            return redirect(url_for('campaign.setup_sequence', campaign_id=campaign.id))
            
        if not campaign.contacts:
            flash('Please add contacts before activating the campaign.', 'error')
            return redirect(url_for('campaign.upload_contacts', campaign_id=campaign.id))
        
        try:    
            # Configure email accounts
            try:
                accounts = smartlead.get_email_accounts()
                if accounts:
                    account_ids = [account['id'] for account in accounts]
                    smartlead.add_email_accounts_to_campaign(campaign.smartlead_id, account_ids)
            except Exception as e:
                flash(f'Warning: Could not configure email accounts. {str(e)}', 'warning')
                
            # Start campaign on SmartLead
            response = smartlead.start_campaign(campaign.smartlead_id)
            if response.get('ok'):
                campaign.status = 'active'
                db.session.commit()
                flash('Campaign activated successfully!', 'success')
            else:
                flash(f"Error activating campaign on SmartLead: {response}", 'error')
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
    
    return redirect(url_for('campaign.view', campaign_id=campaign.id))

@bp.route('/<int:campaign_id>')
@login_required
def view(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Get updated data from SmartLead
    if campaign.smartlead_id:
        try:
            # Get campaign stats
            stats = smartlead.get_campaign_stats(campaign.smartlead_id)
            campaign.smartlead_stats = stats
        except Exception as e:
            flash(f"Could not retrieve SmartLead stats: {str(e)}", "warning")
            
    return render_template('campaign/view.html', campaign=campaign)

@bp.route('/templates', methods=['GET', 'POST'])
@login_required
def templates():
    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        body = request.form.get('body')
        
        template = EmailTemplate(
            name=name,
            subject=subject,
            body=body
        )
        db.session.add(template)
        db.session.commit()
        
        flash('Email template created successfully!', 'success')
        return redirect(url_for('campaign.templates'))
        
    templates = EmailTemplate.query.all()
    return render_template('campaign/templates.html', templates=templates) 