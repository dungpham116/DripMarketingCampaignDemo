from flask import Blueprint, send_file, request
from app.models.tracking import EmailTracking
from app.models.contact import Contact
from app import db
import io

bp = Blueprint('tracking', __name__)

@bp.route('/t/<token>')
def track_open(token):
    # Decode the tracking token to get contact_id and sequence_id
    try:
        contact_id, sequence_id = decode_tracking_token(token)
        contact = Contact.query.get(contact_id)
        
        if contact and contact.status != 'responded':
            contact.status = 'seen'
            tracking = EmailTracking(
                contact_id=contact_id,
                email_sequence_id=sequence_id,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(tracking)
            db.session.commit()
    except:
        pass
        
    # Return a 1x1 transparent pixel
    pixel = io.BytesIO()
    pixel.write(b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
    pixel.seek(0)
    return send_file(pixel, mimetype='image/gif')

def decode_tracking_token(token):
    # Implement your token decoding logic here
    # This should return (contact_id, sequence_id)
    pass 