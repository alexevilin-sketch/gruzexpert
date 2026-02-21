<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Контакты - GRUZEXPERT</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        
        :root {
            --primary: #39ff14;
            --secondary: #ffff00;
            --dark: #000000;
        }
        
        body { 
            background: var(--dark); 
            color: var(--primary); 
            font-family: 'Courier New', monospace;
        }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        .header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid var(--primary);
            margin-bottom: 30px;
        }
        
        .contacts-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 30px;
            margin: 40px 0;
        }
        
        .contact-card {
            border: 2px solid var(--primary);
            padding: 40px;
            text-align: center;
        }
        
        .contact-icon {
            font-size: 4rem;
            margin-bottom: 20px;
        }
        
        .contact-value {
            font-size: 2rem;
            color: var(--secondary);
            margin: 20px 0;
        }
        
        .btn {
            display: inline-block;
            padding: 15px 30px;
            background: transparent;
            color: var(--primary);
            border: 2px solid var(--primary);
            text-decoration: none;
            margin: 10px;
        }
        
        .btn:hover {
            background: var(--primary);
            color: var(--dark);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📞 КОНТАКТЫ</h1>
            <a href="/" class="btn">🏠 НА ГЛАВНУЮ</a>
        </div>
        
        <div class="contacts-grid">
            <div class="contact-card">
                <div class="contact-icon">📱</div>
                <h3>ТЕЛЕФОН</h3>
                <div class="contact-value">+370 600 83564</div>
                <p>Работаем 24/7</p>
            </div>
            
            <div class="contact-card">
                <div class="contact-icon">📧</div>
                <h3>EMAIL</h3>
                <div class="contact-value">orders@gruzexpert.info</div>
                <p>Ответим в течение часа</p>
            </div>
            
            <div class="contact-card">
                <div class="contact-icon">📨</div>
                <h3>TELEGRAM</h3>
                <div class="contact-value">@gruzexpertvilnius_bot</div>
                <p>Наш бот для заказов</p>
            </div>
            
            <div class="contact-card">
                <div class="contact-icon">📍</div>
                <h3>АДРЕС</h3>
                <div class="contact-value">Вильнюс, Литва</div>
                <p>Работаем по всей Литве</p>
            </div>
        </div>
    </div>
</body>
</html>
