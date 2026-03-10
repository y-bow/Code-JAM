from flask import Blueprint, render_template, g, flash, redirect, url_for, request, jsonify
from ..middleware import school_scoped
from ..models import db, User, Message, FriendRequest, Friendship, Block
from sqlalchemy import or_, and_
from datetime import datetime

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

@messages_bp.route('/')
@school_scoped
def index():
    user = g.current_user
    # Get all conversations (distinct users this user has messaged)
    sent = db.session.query(Message.recipient_id).filter_by(sender_id=user.id).distinct()
    received = db.session.query(Message.sender_id).filter_by(recipient_id=user.id).distinct()
    
    chat_partner_ids = set([r[0] for r in sent.all()] + [r[0] for r in received.all()])
    chat_partners = User.query.filter(User.id.in_(chat_partner_ids)).all()
    
    # Get pending friend requests
    pending_requests = FriendRequest.query.filter_by(recipient_id=user.id, status='pending').all()
    # Get friends
    friendships = Friendship.query.filter(or_(Friendship.user1_id == user.id, Friendship.user2_id == user.id)).all()
    friend_ids = [f.user2_id if f.user1_id == user.id else f.user1_id for f in friendships]
    friends = User.query.filter(User.id.in_(friend_ids)).all()

    return render_template('messages/index.html', 
                           partners=chat_partners, 
                           pending_requests=pending_requests,
                           friends=friends)

@messages_bp.route('/history/<int:other_user_id>')
@school_scoped
def history(other_user_id):
    user = g.current_user
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == user.id, Message.recipient_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.recipient_id == user.id)
        )
    ).order_by(Message.sent_at.asc()).all()
    
    # Mark as read
    Message.query.filter_by(sender_id=other_user_id, recipient_id=user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'body': m.body,
        'timestamp': m.sent_at.strftime('%H:%M')
    } for m in messages])

@messages_bp.route('/send', methods=['POST'])
@school_scoped
def send():
    recipient_id = request.form.get('recipient_id')
    body = request.form.get('body')
    
    if not recipient_id or not body:
        return jsonify({'error': 'Missing fields'}), 400
        
    # Check block status
    is_blocked = Block.query.filter_by(blocker_id=recipient_id, blocked_id=g.current_user.id).first()
    if is_blocked:
        return jsonify({'error': 'You are blocked by this user'}), 403
        
    msg = Message(sender_id=g.current_user.id, recipient_id=recipient_id, body=body)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'id': msg.id, 'timestamp': msg.sent_at.strftime('%H:%M')})

@messages_bp.route('/request/send/<int:user_id>', methods=['POST'])
@school_scoped
def send_request(user_id):
    if g.current_user.role == 'teacher':
        return "Teachers cannot use social features", 403
    # Cross-school request support: check for target user existence
    target_user = User.query.get_or_404(user_id)
    if not target_user.is_active:
        return "User not found", 404
    # Check if already friends or request exists
    existing = FriendRequest.query.filter(
        or_(
            and_(FriendRequest.sender_id == g.current_user.id, FriendRequest.recipient_id == user_id),
            and_(FriendRequest.sender_id == user_id, FriendRequest.recipient_id == g.current_user.id)
        )
    ).first()
    
    if existing:
        flash('Request already sent or pending.', 'info')
    else:
        req = FriendRequest(sender_id=g.current_user.id, recipient_id=user_id)
        db.session.add(req)
        db.session.commit()
        flash('Friend request sent!', 'success')
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    return redirect(url_for('messages.index'))

@messages_bp.route('/request/respond/<int:request_id>/<action>', methods=['POST'])
@school_scoped
def respond_request(request_id, action):
    if g.current_user.role == 'teacher':
        return "Teachers cannot use social features", 403
    req = FriendRequest.query.get_or_404(request_id)
    if req.recipient_id != g.current_user.id:
        return "Unauthorized", 403
        
    if action == 'accept':
        req.status = 'accepted'
        friendship = Friendship(user1_id=req.sender_id, user2_id=req.recipient_id)
        db.session.add(friendship)
        flash('Request accepted!', 'success')
    else:
        req.status = 'declined'
        flash('Request declined.', 'info')
        
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    return redirect(url_for('messages.index'))

@messages_bp.route('/block/<int:user_id>', methods=['POST'])
@school_scoped
def block_user(user_id):
    if user_id == g.current_user.id:
        return "Cannot block yourself", 400
    
    existing = Block.query.filter_by(blocker_id=g.current_user.id, blocked_id=user_id).first()
    if not existing:
        block = Block(blocker_id=g.current_user.id, blocked_id=user_id)
        db.session.add(block)
        db.session.commit()
    
    flash('User blocked.', 'warning')
    return redirect(url_for('messages.index'))

@messages_bp.route('/unblock/<int:user_id>', methods=['POST'])
@school_scoped
def unblock_user(user_id):
    block = Block.query.filter_by(blocker_id=g.current_user.id, blocked_id=user_id).first()
    if block:
        db.session.delete(block)
        db.session.commit()
    
    flash('User unblocked.', 'success')
    return redirect(url_for('messages.index'))
@messages_bp.route('/search_users')
@school_scoped
def search_users():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    user = g.current_user
    # Find active non-teacher users matching name or email, excluding self
    # Note: Cross-school search enabled for students; Teachers are excluded from social discovery
    results = User.query.filter(
        User.id != user.id,
        User.is_active == True,
        User.role != 'teacher',
        or_(User.name.ilike(f'%{query}%'), User.email.ilike(f'%{query}%'))
    ).limit(10).all()
    
    # Check friendship/request status for each result
    friend_ids = [f.user2_id if f.user1_id == user.id else f.user1_id 
                  for f in Friendship.query.filter(or_(Friendship.user1_id == user.id, Friendship.user2_id == user.id)).all()]
    
    pending_sent = {r.recipient_id: r.id for r in FriendRequest.query.filter_by(sender_id=user.id, status='pending').all()}
    pending_received = {r.sender_id: r.id for r in FriendRequest.query.filter_by(recipient_id=user.id, status='pending').all()}

    output = []
    for r in results:
        status = 'none'
        req_id = None
        if r.id in friend_ids:
            status = 'friends'
        elif r.id in pending_sent:
            status = 'pending_sent'
            req_id = pending_sent[r.id]
        elif r.id in pending_received:
            status = 'pending_received'
            req_id = pending_received[r.id]
            
        output.append({
            'id': r.id,
            'name': r.name,
            'role': r.role,
            'status': status,
            'request_id': req_id
        })
        
    return jsonify(output)
