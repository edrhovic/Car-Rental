from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.contact import ContactMessage
from models.notification import Notification
from models.user import User
from routes.admin import admin_required
import email_utils
from datetime import datetime
from models import db

contact_bp = Blueprint('contact', __name__, url_prefix='/contact')

@contact_bp.route('/')
def contact_page():
    """Display the Contact Us page"""
    return render_template('content/contact.html')

@contact_bp.route('/submit', methods=['POST'])
def contact_submit():
    """Handle contact form submission"""
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone', 'Not provided')
        message = request.form.get('message')
        
        if not name or not email or not message:
            flash('Please fill out all required fields.', 'danger')
            return redirect(url_for('contact.contact_page'))
        
        # Save message to database
        try:
            contact_message = ContactMessage(
                name=name,
                email=email,
                phone=phone,
                message=message
            )
            
            db.session.add(contact_message)
            db.session.commit()
            print(f"Successfully saved contact message from {name} ({email})")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error saving contact message to database: {str(e)}")
            flash('There was an issue saving your message. Please try again.', 'warning')
            return redirect(url_for('contact.contact_page'))
        
        # Get admin users to send notification to
        try:
            admin_users = User.query.filter_by(is_admin=True).all()
            admin_emails = [admin.email for admin in admin_users if admin.email]
            
            # Add a default email if no admin emails found
            if not admin_emails:
                admin_emails = ['info@jdmcarrentals.com']
            
            # Prepare email subject and content
            subject = f"New Contact Form Submission from {name}"
            html_content = f"""
            <h2>New Contact Form Submission</h2>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Phone:</strong> {phone}</p>
            <p><strong>Message:</strong></p>
            <p>{message}</p>
            """
            
            # Send email to admins
            email_sent = False
            for admin_email in admin_emails:
                try:
                    if email_utils.send_email(admin_email, subject, html_content):
                        email_sent = True
                        print(f"Successfully sent notification email to admin {admin_email}")
                except Exception as e:
                    print(f"Error sending email to admin {admin_email}: {str(e)}")
            
            # Also send an auto-reply to the user
            user_subject = "We've received your message - JDM Car Rentals"
            user_html_content = f"""
            <h2>Thank you for contacting JDM Car Rentals</h2>
            <p>Dear {name},</p>
            <p>We've received your message and will get back to you as soon as possible.</p>
            <p>For urgent inquiries, please call us at +63 962 561 5941.</p>
            <p>Best regards,<br>JDM Car Rentals Team</p>
            """
            
            try:
                email_utils.send_email(email, user_subject, user_html_content)
                print(f"Successfully sent auto-reply to user {email}")
            except Exception as e:
                print(f"Error sending auto-reply to user {email}: {str(e)}")
            
            # Create notification for admin users
            for admin in admin_users:
                try:
                    notification = Notification(
                        user_id=admin.id,
                        title='New Contact Form Submission',
                        message=f'New message from {name} ({email})',
                        notification_type='system',
                        is_read=False
                    )
                    db.session.add(notification)
                except Exception as e:
                    print(f"Error creating admin notification: {str(e)}")
            
            try:
                db.session.commit()
                print("Successfully saved admin notifications")
            except Exception as e:
                db.session.rollback()
                print(f"Error saving admin notifications: {str(e)}")
            
            flash('Your message has been sent successfully! We\'ll get back to you soon.', 'success')
            return redirect(url_for('contact.contact_page'))
            
        except Exception as e:
            print(f"Error in email/notification handling: {str(e)}")
            flash('Your message has been saved, but there was an issue sending notifications. We\'ll still get back to you soon.', 'warning')
            return redirect(url_for('contact.contact_page'))
            
    except Exception as e:
        db.session.rollback()
        print(f"Error processing contact form: {str(e)}")
        flash('An error occurred while processing your request. Please try again.', 'danger')
        return redirect(url_for('contact.contact_page'))

@contact_bp.route('/admin/messages')
@login_required
@admin_required
def admin_messages():
    """Display all contact messages for admin"""
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/contact_messages.html', messages=messages)

@contact_bp.route('/admin/messages/<int:message_id>')
@login_required
@admin_required
def view_message(message_id):
    """Display details of a specific message"""
    message = ContactMessage.query.get_or_404(message_id)
    
    # Mark as read if not already
    if not message.is_read:
        message.is_read = True
        db.session.commit()
        
    return render_template('admin/message_details.html', message=message)

@contact_bp.route('/admin/messages/<int:message_id>/reply', methods=['POST'])
@login_required
@admin_required
def reply_message(message_id):
    """Reply to a contact message"""
    message = ContactMessage.query.get_or_404(message_id)
    reply_text = request.form.get('reply', '')
    
    if not reply_text:
        flash('Reply cannot be empty', 'danger')
        return redirect(url_for('contact.view_message', message_id=message_id))
    
    # Update message in database
    message.admin_reply = reply_text
    message.replied_at = datetime.utcnow()
    message.replied_by = current_user.id
    
    # Send email reply
    subject = "Response from JDM Car Rentals"
    html_content = f"""
    <h2>Response to Your Inquiry</h2>
    <p>Dear {message.name},</p>
    <p>Thank you for contacting JDM Car Rentals. Here is our response to your inquiry:</p>
    <div style="padding: 15px; background-color: #f8f9fa; border-left: 4px solid #6c757d; margin: 20px 0;">
        {reply_text}
    </div>
    <p>Your original message:</p>
    <div style="padding: 15px; background-color: #f8f9fa; border-left: 4px solid #007bff; margin: 20px 0;">
        {message.message}
    </div>
    <p>If you have any further questions, please don't hesitate to contact us.</p>
    <p>Best regards,<br>JDM Car Rentals Team</p>
    """
    
    email_sent = email_utils.send_email(message.email, subject, html_content)
    
    if email_sent:
        db.session.commit()
        flash('Your reply has been sent successfully!', 'success')
    else:
        db.session.rollback()
        flash('There was an issue sending your reply. Please try again.', 'danger')
    
    return redirect(url_for('contact.view_message', message_id=message_id))

@contact_bp.route('/admin/messages/<int:message_id>/mark-as-read', methods=['POST'])
@login_required
@admin_required
def mark_as_read(message_id):
    """Mark a message as read (AJAX)"""
    message = ContactMessage.query.get_or_404(message_id)
    message.is_read = True
    db.session.commit()
    return jsonify({'success': True}) 