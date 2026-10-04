import random
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from flask import render_template, redirect, url_for, request, session, flash
from app.core.auth import auth_bp, limiter
from app.core.auth.decorators import login_required
from app.core.auth.services import authenticate, change_user_password, get_redirect_target
from app.models import User


def generate_captcha():
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    captcha_text = "".join(random.choices(chars, k=random.randint(5, 6)))
    session['captcha_answer'] = captcha_text
    width, height = 180, 60
    image = Image.new('RGB', (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(image)
    for _ in range(8):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=(random.randint(150, 200), random.randint(150, 200), random.randint(150, 200)), width=1)
    for _ in range(100):
        draw.point((random.randint(0, width), random.randint(0, height)), fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)))
    try:
        font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    current_x = 20
    for char in captcha_text:
        char_y = random.randint(10, 25)
        draw.text((current_x, char_y), char, fill=(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)), font=font)
        current_x += random.randint(25, 30)
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    session['captcha_image'] = f"data:image/png;base64,{img_str}"
    return session['captcha_image']


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = authenticate(email, password)
        if user:
            if not user.is_active:
                flash('Your account has been deactivated.', 'danger')
                generate_captcha()
                return render_template('login.html')
            if user.institution and not user.institution.is_active:
                flash('Your institution is currently inactive.', 'danger')
                generate_captcha()
                return render_template('login.html')
            session['user_id'] = user.id
            session['role'] = user.role
            session['name'] = user.name
            session['institution_id'] = user.institution_id
            return redirect(url_for(get_redirect_target(user)))
        flash('Invalid email or password', 'danger')
        generate_captcha()
    generate_captcha()
    return render_template('login.html')


@auth_bp.route('/refresh-captcha', methods=['GET'])
def refresh_captcha():
    image_src = generate_captcha()
    return {"image_src": image_src}


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@limiter.limit("5 per 10 minutes")
@login_required
def change_password():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        success, message = change_user_password(user, current_password, new_password, confirm_password)
        flash(message, 'success' if success else 'danger')
        if success:
            return redirect(url_for(get_redirect_target(user)))
    return render_template('change_password.html')
