#!/usr/bin/env python3
import asyncio
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import aiosqlite
from datetime import datetime
import traceback

# Получаем токен из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN', "8573711643:AAFceOUgqdnNFr_Wct2TPegImJSpGA-OwNQ")

# Настройки email (опционально)
SMTP_SERVER = "mail.spacemail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
TARGET_EMAIL = os.environ.get('TARGET_EMAIL', 'orders@gruzexpert.info')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== КЛАСС КАЛЬКУЛЯТОРА =====
class CargoCalculator:
    # Базовая ставка в зависимости от типа услуги (евро/час за одного рабочего)
    BASE_RATES = {
        'delivery': 20,
        'moving': 25,
        'office': 30,
        'dismantling': 35,
        'assembly': 30,
        'rigging': 40
    }
    
    # Коэффициенты объёма
    VOLUME_MULTIPLIERS = {
        'small': 1.0,
        'medium': 1.3,
        'large': 1.7,
        'huge': 2.2
    }
    
    # Коэффициенты срочности
    URGENCY_MULTIPLIERS = {
        'normal': 1.0,
        'urgent': 1.5,
        'express': 2.0
    }
    
    # Цены дополнительных услуг
    EXTRAS_PRICES = {
        'packing': 50,
        'materials': 30,
        'furniture_disassembly': 40,
        'furniture_assembly': 60,
        'waste_removal': 35,
        'insurance': 0.05,
        'piano': 100,
        'safe': 150,
        'waiting': 15,
        'long_distance': 100
    }
    
    # Названия для отображения
    SERVICE_NAMES = {
        'delivery': '🚚 Доставка груза',
        'moving': '🏠 Квартирный переезд',
        'office': '🏢 Офисный переезд',
        'dismantling': '🔨 Демонтаж',
        'assembly': '🪑 Сборка мебели',
        'rigging': '📦 Такелажные работы'
    }
    
    VOLUME_NAMES = {
        'small': '📦 Маленький (до 10м³)',
        'medium': '📦📦 Средний (10-30м³)',
        'large': '📦📦📦 Большой (30-60м³)',
        'huge': '🏭 Очень большой (60+м³)'
    }
    
    URGENCY_NAMES = {
        'normal': '🚶 Обычный (3-5 дней)',
        'urgent': '⚡ Срочный (24 часа)',
        'express': '🔥 Экспресс (2-4 часа)'
    }
    
    @classmethod
    def _get_extra_name(cls, extra_key):
        names = {
            'packing': '📦 Упаковка вещей',
            'materials': '📎 Упаковочные материалы',
            'furniture_disassembly': '🔧 Разборка мебели',
            'furniture_assembly': '🛠️ Сборка мебели',
            'waste_removal': '🗑️ Вывоз мусора',
            'piano': '🎹 Пианино/рояль',
            'safe': '🔒 Сейф/банкомат',
            'long_distance': '🛣️ Загород (50+ км)'
        }
        return names.get(extra_key, extra_key)
    
    @classmethod
    def calculate(cls, params):
        try:
            # Базовая ставка
            base_rate = cls.BASE_RATES.get(params.get('service_type', 'moving'), 25)
            
            # Применяем коэффициенты
            volume_mult = cls.VOLUME_MULTIPLIERS.get(params.get('volume', 'medium'), 1.3)
            urgency_mult = cls.URGENCY_MULTIPLIERS.get(params.get('urgency', 'normal'), 1.0)
            
            workers = params.get('workers', 2)
            hours = params.get('hours', 3)
            
            # Базовая стоимость
            base_cost = base_rate * workers * hours * volume_mult * urgency_mult
            
            # Надбавка за этаж
            floor_extra = 0
            floor = params.get('floor', 1)
            elevator = params.get('elevator', 'yes')
            floor_rate = 5
            
            if elevator == 'no':
                floor_extra = (floor - 1) * floor_rate * workers * hours
            elif elevator == 'passenger':
                floor_extra = (floor - 1) * (floor_rate * 0.5) * workers * hours
            
            # Ночной тариф
            night_extra = 0
            if params.get('time_of_day') == 'night':
                night_extra = base_cost * 0.5
            
            # Выходной день
            weekend_extra = 0
            if params.get('day_of_week') == 'weekend':
                weekend_extra = base_cost * 0.3
            
            # Дополнительные услуги
            extras_total = 0
            extras_list = []
            extras = params.get('extras', [])
            
            for extra in extras:
                if extra in cls.EXTRAS_PRICES:
                    if extra == 'insurance':
                        extras_total += base_cost * cls.EXTRAS_PRICES[extra]
                        extras_list.append(f'🛡️ Страховка груза (+{int(cls.EXTRAS_PRICES[extra] * 100)}%)')
                    elif extra == 'waiting':
                        extras_total += cls.EXTRAS_PRICES[extra] * hours
                        extras_list.append(f'⏱️ Ожидание ({cls.EXTRAS_PRICES[extra] * hours}€)')
                    else:
                        extras_total += cls.EXTRAS_PRICES[extra]
                        extras_list.append(f'{cls._get_extra_name(extra)} (+{cls.EXTRAS_PRICES[extra]}€)')
            
            # Итоговая стоимость
            total_cost = base_cost + floor_extra + night_extra + weekend_extra + extras_total
            
            # Форматируем детали
            service_type = params.get('service_type', 'moving')
            volume = params.get('volume', 'medium')
            urgency = params.get('urgency', 'normal')
            
            details = f"📋 ТИП УСЛУГИ: {cls.SERVICE_NAMES.get(service_type, service_type)}\n"
            details += f"📦 ОБЪЁМ РАБОТ: {cls.VOLUME_NAMES.get(volume, volume)}\n"
            details += f"👷 КОЛИЧЕСТВО ГРУЗЧИКОВ: {params.get('workers', 2)}\n"
            details += f"⏱️ КОЛИЧЕСТВО ЧАСОВ: {params.get('hours', 3)}\n"
            details += f"⚡ СРОЧНОСТЬ: {cls.URGENCY_NAMES.get(urgency, urgency)}\n"
            
            elevator_text = {
                'yes': 'грузовой лифт',
                'passenger': 'пассажирский лифт',
                'no': 'без лифта'
            }.get(params.get('elevator', 'yes'), 'грузовой лифт')
            
            details += f"🏢 ЭТАЖ: {params.get('floor', 1)} ({elevator_text})\n"
            details += f"🌙 ВРЕМЯ СУТОК: {'дневное' if params.get('time_of_day') == 'day' else 'ночное'}\n"
            details += f"📅 ДЕНЬ: {'будний' if params.get('day_of_week') == 'weekday' else 'выходной/праздник'}\n"
            
            if extras_list:
                details += f"\n➕ ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ:\n"
                for extra in extras_list:
                    details += f"{extra}\n"
            
            details += f"\n💰 ИТОГОВАЯ СТОИМОСТЬ: {round(total_cost)} €"
            
            return {
                'total_cost': round(total_cost),
                'base_cost': round(base_cost),
                'base_rate': base_rate,
                'workers': workers,
                'hours': hours,
                'volume_mult': volume_mult,
                'urgency_mult': urgency_mult,
                'floor_extra': round(floor_extra),
                'night_extra': round(night_extra),
                'weekend_extra': round(weekend_extra),
                'extras_total': round(extras_total),
                'extras_list': extras_list,
                'params': params,
                'details': details
            }
        except Exception as e:
            logger.error(f"Error in calculation: {e}\n{traceback.format_exc()}")
            return None

# ===== ФУНКЦИЯ ОТПРАВКИ EMAIL =====
async def send_calculation_email(calculation_result: dict, user_info: dict = None):
    """Отправка расчета на email"""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured, skipping email send")
        return False
        
    try:
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = TARGET_EMAIL
        msg['Subject'] = f"Новый расчет стоимости | GRUZEXPERT"
        
        # Формируем тело письма
        body = f"""
        <h2>🚛 НОВЫЙ РАСЧЕТ СТОИМОСТИ</h2>
        
        <p><strong>Время расчета:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        
        <h3>📊 ДЕТАЛИ РАСЧЕТА:</h3>
        <pre>{calculation_result['details']}</pre>
        
        <h3>💰 ИТОГО: {calculation_result['total_cost']} €</h3>
        
        <hr>
        <p><em>Отправлено из Telegram бота @gruzexpertvilnius_bot</em></p>
        """
        
        if user_info:
            body += f"\n<p><strong>Информация о пользователе:</strong><br>"
            if user_info.get('username'):
                body += f"Telegram: @{user_info['username']}<br>"
            body += f"User ID: {user_info['user_id']}</p>"
        
        msg.attach(MIMEText(body, 'html'))
        
        # Отправляем
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {TARGET_EMAIL}")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

# ===== СОСТОЯНИЯ ДЛЯ КАЛЬКУЛЯТОРА =====
class CalculatorStates(StatesGroup):
    waiting_for_service_type = State()
    waiting_for_volume = State()
    waiting_for_workers = State()
    waiting_for_hours = State()
    waiting_for_urgency = State()
    waiting_for_floor = State()
    waiting_for_elevator = State()
    waiting_for_time_of_day = State()
    waiting_for_day_of_week = State()
    waiting_for_extras = State()
    waiting_for_action = State()

# ===== БАЗА ДАННЫХ =====
async def init_db():
    async with aiosqlite.connect('cargo.db') as db:
        # Таблица расчетов
        await db.execute('''CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            params TEXT,
            result TEXT,
            total_cost REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        await db.commit()
    logger.info("Database initialized")

async def save_calculation(user_id: int, username: str, params: dict, result: dict):
    try:
        async with aiosqlite.connect('cargo.db') as db:
            await db.execute('''
                INSERT INTO calculations (user_id, username, params, result, total_cost)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                username,
                str(params),
                result['details'],
                result['total_cost']
            ))
            await db.commit()
        logger.info(f"Calculation saved for user {user_id}")
    except Exception as e:
        logger.error(f"Error saving calculation: {e}")

# ===== ПРИВЕТСТВЕННОЕ МЕНЮ =====
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "🚚 <b>Добро пожаловать в GRUZEXPERT!</b>\n\n"
        "🏆 <b>1000+ заказов | 20+ сотрудников | 5+ лет опыта</b>\n\n"
        "Я помогу вам рассчитать стоимость грузоперевозок:\n"
        "• 📦 Доставка груза\n"
        "• 🏠 Квартирные переезды\n"
        "• 🏢 Офисные переезды\n"
        "• 🔨 Демонтаж\n"
        "• 🪑 Сборка мебели\n"
        "• 📦 Такелажные работы\n\n"
        "<b>Нажмите кнопку для расчета:</b>"
    )
    
    kb = [
        [KeyboardButton(text="🧮 НАЧАТЬ РАСЧЕТ СТОИМОСТИ")],
        [KeyboardButton(text="📞 КОНТАКТЫ"), KeyboardButton(text="ℹ️ О НАС")]
    ]
    
    await message.answer(
        welcome_text,
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True),
        parse_mode="HTML"
    )

# ===== О НАС =====
@dp.message(F.text == "ℹ️ О НАС")
async def about_us(message: types.Message):
    about_text = (
        "🏆 <b>GRUZEXPERT В ЦИФРАХ</b>\n\n"
        "✅ <b>1000+</b> успешных заказов\n"
        "✅ <b>20+</b> профессиональных сотрудников\n"
        "✅ <b>5+</b> лет опыта работы в Литве\n"
        "✅ <b>98%</b> клиентов возвращаются снова\n\n"
        "⚡ <b>НАШИ ПРИНЦИПЫ:</b>\n"
        "• Точность — приезжаем минута в минуту\n"
        "• Скорость — подача за 15-30 минут\n"
        "• Лояльность — скидки постоянным клиентам\n\n"
        "💚 Работаем 24/7 без выходных!"
    )
    await message.answer(about_text, parse_mode="HTML")

# ===== КОНТАКТЫ =====
@dp.message(F.text == "📞 КОНТАКТЫ")
async def contacts(message: types.Message):
    contacts_text = (
        "📞 <b>Контакты:</b>\n\n"
        "📱 Телефон: +370 600 83564\n"
        "📧 Email: orders@gruzexpert.info\n\n"
        "📨 Telegram: @gruzexpertvilnius_bot\n"
        "⏰ <b>Работаем круглосуточно!</b>"
    )
    await message.answer(contacts_text, parse_mode="HTML")

# ===== КАЛЬКУЛЯТОР =====
@dp.message(F.text == "🧮 НАЧАТЬ РАСЧЕТ СТОИМОСТИ")
async def calculator_start(message: types.Message, state: FSMContext):
    kb = [
        [KeyboardButton(text="🚚 Доставка груза")],
        [KeyboardButton(text="🏠 Квартирный переезд")],
        [KeyboardButton(text="🏢 Офисный переезд")],
        [KeyboardButton(text="🔨 Демонтаж")],
        [KeyboardButton(text="🪑 Сборка мебели")],
        [KeyboardButton(text="📦 Такелажные работы")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    
    await message.answer(
        "🧮 <b>КАЛЬКУЛЯТОР СТОИМОСТИ</b>\n\n"
        "Шаг 1/9: Выберите тип услуги:",
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    await state.set_state(CalculatorStates.waiting_for_service_type)

@dp.message(CalculatorStates.waiting_for_service_type)
async def calc_service_type(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await cmd_start(message)
        return
    
    service_map = {
        "🚚 Доставка груза": "delivery",
        "🏠 Квартирный переезд": "moving",
        "🏢 Офисный переезд": "office",
        "🔨 Демонтаж": "dismantling",
        "🪑 Сборка мебели": "assembly",
        "📦 Такелажные работы": "rigging"
    }
    
    service_type = service_map.get(message.text)
    if not service_type:
        await message.answer("❌ Пожалуйста, выберите тип услуги из меню:")
        return
    
    await state.update_data(service_type=service_type)
    
    kb = [
        [KeyboardButton(text="📦 Маленький (до 10м³)")],
        [KeyboardButton(text="📦📦 Средний (10-30м³)")],
        [KeyboardButton(text="📦📦📦 Большой (30-60м³)")],
        [KeyboardButton(text="🏭 Очень большой (60+м³)")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    
    await message.answer(
        "Шаг 2/9: Выберите объём работ:",
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
    await state.set_state(CalculatorStates.waiting_for_volume)

@dp.message(CalculatorStates.waiting_for_volume)
async def calc_volume(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await cmd_start(message)
        return
    
    volume_map = {
        "📦 Маленький (до 10м³)": "small",
        "📦📦 Средний (10-30м³)": "medium",
        "📦📦📦 Большой (30-60м³)": "large",
        "🏭 Очень большой (60+м³)": "huge"
    }
    
    volume = volume_map.get(message.text)
    if not volume:
        await message.answer("❌ Пожалуйста, выберите объём из меню:")
        return
    
    await state.update_data(volume=volume)
    
    await message.answer(
        "Шаг 3/9: Введите количество грузчиков (1-10):\n"
        "📝 Например: 2",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CalculatorStates.waiting_for_workers)

@dp.message(CalculatorStates.waiting_for_workers)
async def calc_workers(message: types.Message, state: FSMContext):
    try:
        workers = int(message.text)
        if workers < 1 or workers > 10:
            await message.answer("❌ Пожалуйста, введите число от 1 до 10:")
            return
        
        await state.update_data(workers=workers)
        
        await message.answer(
            "Шаг 4/9: Введите количество часов (1-24):\n"
            "📝 Например: 3",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(CalculatorStates.waiting_for_hours)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число:")

@dp.message(CalculatorStates.waiting_for_hours)
async def calc_hours(message: types.Message, state: FSMContext):
    try:
        hours = float(message.text)
        if hours < 1 or hours > 24:
            await message.answer("❌ Пожалуйста, введите число от 1 до 24:")
            return
        
        await state.update_data(hours=hours)
        
        kb = [
            [KeyboardButton(text="🚶 Обычный (3-5 дней)")],
            [KeyboardButton(text="⚡ Срочный (24 часа)")],
            [KeyboardButton(text="🔥 Экспресс (2-4 часа)")],
            [KeyboardButton(text="❌ Отмена")]
        ]
        
        await message.answer(
            "Шаг 5/9: Выберите срочность выполнения:",
            reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        )
        await state.set_state(CalculatorStates.waiting_for_urgency)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число:")

@dp.message(CalculatorStates.waiting_for_urgency)
async def calc_urgency(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await cmd_start(message)
        return
    
    urgency_map = {
        "🚶 Обычный (3-5 дней)": "normal",
        "⚡ Срочный (24 часа)": "urgent",
        "🔥 Экспресс (2-4 часа)": "express"
    }
    
    urgency = urgency_map.get(message.text)
    if not urgency:
        await message.answer("❌ Пожалуйста, выберите срочность из меню:")
        return
    
    await state.update_data(urgency=urgency)
    
    await message.answer(
        "Шаг 6/9: Введите этаж, на который нужно подняться:\n"
        "📝 Например: 3",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CalculatorStates.waiting_for_floor)

@dp.message(CalculatorStates.waiting_for_floor)
async def calc_floor(message: types.Message, state: FSMContext):
    try:
        floor = int(message.text)
        if floor < 1 or floor > 25:
            await message.answer("❌ Пожалуйста, введите число от 1 до 25:")
            return
        
        await state.update_data(floor=floor)
        
        kb = [
            [KeyboardButton(text="✅ Грузовой лифт")],
            [KeyboardButton(text="🔄 Пассажирский лифт")],
            [KeyboardButton(text="❌ Нет лифта")],
            [KeyboardButton(text="❌ Отмена")]
        ]
        
        await message.answer(
            "Шаг 7/9: Выберите наличие лифта:",
            reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        )
        await state.set_state(CalculatorStates.waiting_for_elevator)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число:")

@dp.message(CalculatorStates.waiting_for_elevator)
async def calc_elevator(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await cmd_start(message)
        return
    
    elevator_map = {
        "✅ Грузовой лифт": "yes",
        "🔄 Пассажирский лифт": "passenger",
        "❌ Нет лифта": "no"
    }
    
    elevator = elevator_map.get(message.text)
    if not elevator:
        await message.answer("❌ Пожалуйста, выберите вариант из меню:")
        return
    
    await state.update_data(elevator=elevator)
    
    kb = [
        [KeyboardButton(text="☀️ Дневное (08:00-22:00)")],
        [KeyboardButton(text="🌙 Ночное (22:00-08:00)")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    
    await message.answer(
        "Шаг 8/9: Выберите время суток:",
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
    await state.set_state(CalculatorStates.waiting_for_time_of_day)

@dp.message(CalculatorStates.waiting_for_time_of_day)
async def calc_time_of_day(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await cmd_start(message)
        return
    
    time_map = {
        "☀️ Дневное (08:00-22:00)": "day",
        "🌙 Ночное (22:00-08:00)": "night"
    }
    
    time_of_day = time_map.get(message.text)
    if not time_of_day:
        await message.answer("❌ Пожалуйста, выберите время из меню:")
        return
    
    await state.update_data(time_of_day=time_of_day)
    
    kb = [
        [KeyboardButton(text="📅 Будний день")],
        [KeyboardButton(text="🎉 Выходной/Праздник")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    
    await message.answer(
        "Шаг 9/9: Выберите день недели:",
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyable=True)
    )
    await state.set_state(CalculatorStates.waiting_for_day_of_week)

@dp.message(CalculatorStates.waiting_for_day_of_week)
async def calc_day_of_week(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await cmd_start(message)
        return
    
    day_map = {
        "📅 Будний день": "weekday",
        "🎉 Выходной/Праздник": "weekend"
    }
    
    day_of_week = day_map.get(message.text)
    if not day_of_week:
        await message.answer("❌ Пожалуйста, выберите день из меню:")
        return
    
    await state.update_data(day_of_week=day_of_week)
    
    # Показываем меню дополнительных услуг
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Упаковка вещей (+50€)", callback_data="extra_packing")],
        [InlineKeyboardButton(text="📎 Упаковочные материалы (+30€)", callback_data="extra_materials")],
        [InlineKeyboardButton(text="🔧 Разборка мебели (+40€)", callback_data="extra_furniture_disassembly")],
        [InlineKeyboardButton(text="🛠️ Сборка мебели (+60€)", callback_data="extra_furniture_assembly")],
        [InlineKeyboardButton(text="🗑️ Вывоз мусора (+35€)", callback_data="extra_waste_removal")],
        [InlineKeyboardButton(text="🛡️ Страховка груза (+5%)", callback_data="extra_insurance")],
        [InlineKeyboardButton(text="🎹 Пианино/рояль (+100€)", callback_data="extra_piano")],
        [InlineKeyboardButton(text="🔒 Сейф/банкомат (+150€)", callback_data="extra_safe")],
        [InlineKeyboardButton(text="⏱️ Ожидание (15€/час)", callback_data="extra_waiting")],
        [InlineKeyboardButton(text="🛣️ Загород (50+ км, +100€)", callback_data="extra_long_distance")],
        [InlineKeyboardButton(text="✅ ЗАВЕРШИТЬ ВЫБОР", callback_data="extras_done")],
        [InlineKeyboardButton(text="❌ ПРОПУСТИТЬ", callback_data="extras_skip")]
    ])
    
    await message.answer(
        "➕ <b>ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ</b>\n\n"
        "Выберите нужные опции (можно несколько):\n"
        "Когда закончите, нажмите 'ЗАВЕРШИТЬ ВЫБОР'",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.update_data(extras=[])
    await state.set_state(CalculatorStates.waiting_for_extras)

@dp.callback_query(CalculatorStates.waiting_for_extras)
async def process_extras(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    extras = data.get('extras', [])
    
    if callback.data == "extras_done" or callback.data == "extras_skip":
        # Завершаем выбор и показываем результат
        params = {
            'service_type': data.get('service_type'),
            'volume': data.get('volume'),
            'workers': data.get('workers'),
            'hours': data.get('hours'),
            'urgency': data.get('urgency'),
            'floor': data.get('floor'),
            'elevator': data.get('elevator'),
            'time_of_day': data.get('time_of_day'),
            'day_of_week': data.get('day_of_week'),
            'extras': extras if callback.data == "extras_done" else []
        }
        
        result = CargoCalculator.calculate(params)
        
        if result:
            # Сохраняем расчет в БД
            username = callback.from_user.username or f"user_{callback.from_user.id}"
            await save_calculation(callback.from_user.id, username, params, result)
            
            # Формируем сообщение с результатом
            result_text = (
                "🧮 <b>РЕЗУЛЬТАТ РАСЧЕТА</b>\n\n"
                f"{result['details']}\n\n"
                "📊 <b>Детализация:</b>\n"
                f"• Базовая ставка: {result['base_rate']}€/час за рабочего\n"
                f"• Базовая стоимость: {result['base_cost']}€\n"
            )
            
            if result['floor_extra'] > 0:
                result_text += f"• Надбавка за этаж: +{result['floor_extra']}€\n"
            if result['night_extra'] > 0:
                result_text += f"• Ночной тариф: +{result['night_extra']}€\n"
            if result['weekend_extra'] > 0:
                result_text += f"• Выходной день: +{result['weekend_extra']}€\n"
            if result['extras_total'] > 0:
                result_text += f"• Доп. услуги: +{result['extras_total']}€\n"
            
            result_text += f"\n💰 <b>ИТОГО: {result['total_cost']} €</b>"
            
            # Кнопки для дальнейших действий
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📧 ОТПРАВИТЬ РАСЧЕТ НА EMAIL", callback_data="send_email")],
                [InlineKeyboardButton(text="🔄 НОВЫЙ РАСЧЕТ", callback_data="new_calculation")],
                [InlineKeyboardButton(text="📞 КОНТАКТЫ", callback_data="show_contacts")]
            ])
            
            await callback.message.edit_text(result_text, reply_markup=kb, parse_mode="HTML")
            await state.update_data(calculation_result=result)
            await state.set_state(CalculatorStates.waiting_for_action)
        else:
            await callback.message.edit_text("❌ Ошибка при расчете. Попробуйте снова.")
            await state.clear()
            
    else:
        # Добавляем/удаляем доп. услугу
        extra = callback.data.replace("extra_", "")
        
        if extra in extras:
            extras.remove(extra)
            await callback.answer(f"❌ Услуга удалена")
        else:
            extras.append(extra)
            await callback.answer(f"✅ Услуга добавлена")
        
        await state.update_data(extras=extras)
        
        # Обновляем сообщение с текущим списком
        extras_text = "➕ <b>ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ</b>\n\n"
        if extras:
            extras_text += "✓ Выбрано:\n"
            for e in extras:
                name = CargoCalculator._get_extra_name(e)
                price = CargoCalculator.EXTRAS_PRICES.get(e, 0)
                if e == 'insurance':
                    extras_text += f"  • {name} (+{int(price*100)}%)\n"
                elif e == 'waiting':
                    extras_text += f"  • {name} ({price}€/час)\n"
                else:
                    extras_text += f"  • {name} (+{price}€)\n"
        else:
            extras_text += "✓ Пока ничего не выбрано\n"
        
        extras_text += "\nВыберите нужные опции (можно несколько):"
        
        # Обновляем клавиатуру
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'✅ ' if 'packing' in extras else '📦 '}Упаковка вещей (+50€)", 
                callback_data="extra_packing"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if 'materials' in extras else '📎 '}Упаковочные материалы (+30€)", 
                callback_data="extra_materials"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if 'furniture_disassembly' in extras else '🔧 '}Разборка мебели (+40€)", 
                callback_data="extra_furniture_disassembly"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if 'furniture_assembly' in extras else '🛠️ '}Сборка мебели (+60€)", 
                callback_data="extra_furniture_assembly"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if 'waste_removal' in extras else '🗑️ '}Вывоз мусора (+35€)", 
                callback_data="extra_waste_removal"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if 'insurance' in extras else '🛡️ '}Страховка груза (+5%)", 
                callback_data="extra_insurance"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if 'piano' in extras else '🎹 '}Пианино/рояль (+100€)", 
                callback_data="extra_piano"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if 'safe' in extras else '🔒 '}Сейф/банкомат (+150€)", 
                callback_data="extra_safe"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if 'waiting' in extras else '⏱️ '}Ожидание (15€/час)", 
                callback_data="extra_waiting"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if 'long_distance' in extras else '🛣️ '}Загород (50+ км, +100€)", 
                callback_data="extra_long_distance"
            )],
            [InlineKeyboardButton(text="✅ ЗАВЕРШИТЬ ВЫБОР", callback_data="extras_done")],
            [InlineKeyboardButton(text="❌ ПРОПУСТИТЬ", callback_data="extras_skip")]
        ])
        
        await callback.message.edit_text(extras_text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(CalculatorStates.waiting_for_action)
async def process_action(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "send_email":
        data = await state.get_data()
        result = data.get('calculation_result')
        
        if not result:
            await callback.message.edit_text("❌ Ошибка: данные расчета не найдены")
            await state.clear()
            await cmd_start(callback.message)
            return
        
        # Отправляем email
        user_info = {
            'user_id': callback.from_user.id,
            'username': callback.from_user.username
        }
        
        success = await send_calculation_email(result, user_info)
        
        if success:
            await callback.message.edit_text(
                "✅ <b>Расчет успешно отправлен!</b>\n\n"
                f"Детали расчета отправлены на {TARGET_EMAIL}\n"
                "Наш менеджер свяжется с вами в ближайшее время.",
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "❌ <b>Ошибка при отправке</b>\n\n"
                "Пожалуйста, попробуйте позже или свяжитесь с нами напрямую:\n"
                f"📧 {TARGET_EMAIL}\n"
                "📱 +370 600 83564",
                parse_mode="HTML"
            )
        
        await state.clear()
        
        # Возвращаемся в главное меню
        kb = [
            [KeyboardButton(text="🧮 НАЧАТЬ РАСЧЕТ СТОИМОСТИ")],
            [KeyboardButton(text="📞 КОНТАКТЫ"), KeyboardButton(text="ℹ️ О НАС")]
        ]
        await callback.message.answer(
            "Главное меню:",
            reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        )
    
    elif callback.data == "new_calculation":
        await state.clear()
        await calculator_start(callback.message, state)
    
    elif callback.data == "show_contacts":
        await state.clear()
        await contacts(callback.message)
        await cmd_start(callback.message)

# ===== ОБРАБОТКА НЕИЗВЕСТНЫХ КОМАНД =====
@dp.message()
async def handle_unknown(message: types.Message, state: FSMContext):
    """Обработка сообщений не во время расчета"""
    current_state = await state.get_state()
    
    if current_state is not None:
        # Если мы в процессе расчета, игнорируем
        return
    
    await message.answer(
        "❓ Я не понимаю эту команду.\n"
        "Пожалуйста, используйте кнопки меню или напишите /start"
    )

async def main():
    try:
        await init_db()
        logger.info("🚀 GRUZEXPERT Бот для расчетов запущен!")
        logger.info(f"📧 Расчеты отправляются на: {TARGET_EMAIL}")
        logger.info("📝 Режимы работы:")
        logger.info("   🧮 Калькулятор стоимости")
        logger.info("   📧 Отправка расчетов на email")
        logger.info("   📞 Контакты и информация")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
