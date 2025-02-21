from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app import db
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.email_template import EmailTemplate, EmailSequence
import pandas as pd
import os

bp = Blueprint('campaign', __name__, url_prefix='/campaign')

@bp.route('/')
@login_required
def index():
    campaigns = Campaign.query.all()
    return render_template('campaign/index.html', campaigns=campaigns)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        campaign = Campaign(name=name, description=description)
        db.session.add(campaign)
        db.session.commit()
        
        flash('Campaign created successfully!', 'success')
        return redirect(url_for('campaign.setup_sequence', campaign_id=campaign.id))
        
    return render_template('campaign/create.html')

@bp.route('/<int:campaign_id>/upload-contacts', methods=['GET', 'POST'])
@login_required
def upload_contacts(campaign_id):
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
                df = pd.read_csv(file)
                for _, row in df.iterrows():
                    contact = Contact(
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        email=row['email'],
                        campaign_id=campaign_id
                    )
                    db.session.add(contact)
                db.session.commit()
                flash('Contacts imported successfully!', 'success')
                return redirect(url_for('campaign.view', campaign_id=campaign_id))
            except Exception as e:
                flash(f'Error importing contacts: {str(e)}', 'error')
                
    return render_template('campaign/upload_contacts.html', campaign_id=campaign_id)

@bp.route('/<int:campaign_id>/setup-sequence', methods=['GET', 'POST'])
@login_required
def setup_sequence(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    templates = EmailTemplate.query.all()
    
    if request.method == 'POST':
        template_ids = request.form.getlist('template_id[]')
        delay_days = request.form.getlist('delay_days[]')
        delay_hours = request.form.getlist('delay_hours[]')
        delay_minutes = request.form.getlist('delay_minutes[]')
        
        for order, (template_id, days, hours, minutes) in enumerate(
            zip(template_ids, delay_days, delay_hours, delay_minutes), 1):
            sequence = EmailSequence(
                campaign_id=campaign_id,
                template_id=template_id,
                delay_days=int(days),
                delay_hours=int(hours),
                delay_minutes=int(minutes),
                sequence_order=order
            )
            db.session.add(sequence)
            
        db.session.commit()
        flash('Email sequence setup completed!', 'success')
        return redirect(url_for('campaign.view', campaign_id=campaign_id))
        
    return render_template('campaign/setup_sequence.html', 
                         campaign=campaign, 
                         templates=templates)

@bp.route('/<int:campaign_id>/edit-sequence', methods=['GET', 'POST'])
@login_required
def edit_sequence(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    templates = EmailTemplate.query.all()
    
    if request.method == 'POST':
        # Delete existing sequences
        EmailSequence.query.filter_by(campaign_id=campaign_id).delete()
        
        # Add new sequences
        template_ids = request.form.getlist('template_id[]')
        delay_days = request.form.getlist('delay_days[]')
        
        for order, (template_id, delay) in enumerate(zip(template_ids, delay_days), 1):
            sequence = EmailSequence(
                campaign_id=campaign_id,
                template_id=template_id,
                delay_days=int(delay),
                sequence_order=order
            )
            db.session.add(sequence)
            
        db.session.commit()
        flash('Email sequence updated successfully!', 'success')
        return redirect(url_for('campaign.view', campaign_id=campaign_id))
        
    return render_template('campaign/edit_sequence.html', 
                         campaign=campaign, 
                         templates=templates)

@bp.route('/<int:campaign_id>')
@login_required
def view(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
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

@bp.route('/<int:campaign_id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if campaign.status == 'active':
        campaign.status = 'paused'
        flash('Campaign paused successfully!', 'success')
    else:
        # Check if campaign has templates and contacts before activating
        if not campaign.email_sequences:
            flash('Please set up email sequences before activating the campaign.', 'error')
            return redirect(url_for('campaign.setup_sequence', campaign_id=campaign.id))
            
        if not campaign.contacts:
            flash('Please add contacts before activating the campaign.', 'error')
            return redirect(url_for('campaign.upload_contacts', campaign_id=campaign.id))
            
        campaign.status = 'active'
        flash('Campaign activated successfully!', 'success')
    
    db.session.commit()
    return redirect(url_for('campaign.view', campaign_id=campaign.id)) 