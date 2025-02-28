document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    let currentTaskId = null;

    // إدارة الأحداث
    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('task_started', (data) => {
        currentTaskId = data.task_id;
        document.getElementById('progress-container').style.display = 'block';
        document.getElementById('stop-btn').style.display = 'inline-block';
    });

    socket.on('progress_update', (data) => {
        const progress = (data.current / data.total) * 100;
        document.getElementById('progress-bar').style.width = `${progress}%`;
        document.getElementById('progress-text').innerText = 
            `تم إرسال ${data.current} من ${data.total} رسائل`;
    });

    socket.on('task_complete', (data) => {
        alert('اكتملت المهمة بنجاح!');
        resetUI();
    });

    socket.on('task_stopped', (data) => {
        alert('تم إيقاف المهمة');
        resetUI();
    });

    socket.on('captcha_error', (data) => {
        alert(data.message);
        location.reload();
    });

    // معالجة إرسال النموذج
    document.querySelector('form').addEventListener('submit', (e) => {
        e.preventDefault();
        
        const formData = {
            email: document.querySelector('[name="email"]').value,
            password: document.querySelector('[name="password"]').value,
            victim: document.querySelector('[name="victim"]').value,
            subject: document.querySelector('[name="subject"]').value,
            message: document.querySelector('[name="message"]').value,
            number: document.querySelector('[name="number"]').value,
            captcha: document.querySelector('[name="captcha"]').value
        };

        socket.emit('start_task', formData);
    });

    // معالجة إيقاف المهمة
    document.getElementById('stop-btn').addEventListener('click', () => {
        if (currentTaskId) {
            socket.emit('stop_task', { task_id: currentTaskId });
        }
    });

    function resetUI() {
        document.getElementById('progress-container').style.display = 'none';
        document.getElementById('stop-btn').style.display = 'none';
        document.getElementById('progress-bar').style.width = '0%';
        document.getElementById('progress-text').innerText = '';
        currentTaskId = null;
    }
});
