from io import BytesIO
import uuid
import warnings
from cryptography.utils import CryptographyDeprecationWarning
import qrcode

from database import add_transaction
from oxapay.functions import confirm_oxa_payment, create_invoice, create_static_address, create_white_label_invoice

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
import time
import paramiko
import telebot
import console
import requests
import time
import secrets
import threading
import string
import hmac
import hashlib
import logging
import os
from telebot import types
from datetime import datetime
from re import findall as reg, DOTALL, search
from telebot.apihelper import ApiTelegramException
import sqlite3
from decouple import config

log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, 'spoofer.log')

logger = logging.getLogger(__name__)
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

public_key = '73a883630fe29f737cb60e1e52b1c73b6f1cfc23142faa5dac64cac69a80d2ed'
private_key = '5aCBb3A869667b8Da51e912E38776f7bf107eFC2B6DB3a517087C00da14dC963'

fg = '\033[92m'
fr = '\033[91m'
fw = '\033[97m'
fy = '\033[93m'
fb = '\033[94m'
flc = '\033[96m'
bd = '\u001b[1m'
res = '\u001b[0m'

# configuration

user_data_dict = {}
recharge_queue = []

sub_price = 100

host_ssh = config('host_ssh')
username_ssh = config('username_ssh')
password_ssh = config('SSH_PASSWORD')

adminlist = ['5748713709','7448447170']

tokenbot = config('BOT_TOKEN')

image_path = os.path.join(os.path.dirname(__file__), 'photo_2023-11-05_00-09-39.png')

bot = telebot.TeleBot(tokenbot)

def logo():
    import shutil

    console_width = shutil.get_terminal_size().columns

    pattern = """\033[1;31m

\033[0m
          Coder: {}@Test_Bot{}
    """.format(fg,fw)


    pattern_centered = "\n".join(line.center(console_width) for line in pattern.splitlines())
    print(pattern_centered)

#bot

user_states = {}
messages_en_attente = {}

def current():
    now = datetime.now()
    return now.strftime("%H:%M:%S")

def insert_user(user_id):
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (chat_id, user , pass , license ,solde)
            VALUES (? , ? , ? , ? , ?)
        ''', (user_id , '' , '' , 0 , 0))
    except sqlite3.IntegrityError:
        logger.error("[{}SYS{}] [{}{}{}] User {}{}{} already exist in DB.".format(fy,fw,fg,current(),fw,fr,user_id,fw))
    else:
        conn.commit()
    conn.close()

def get_all_chatid():
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id TEXT PRIMARY KEY,
            user TEXT,
            pass TEXT,
            exp TEXT,
            license INTEGER,
            solde INTEGER
        )
    ''')

    cursor.execute('SELECT chat_id FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def update_solde(newsolde, user_id):
    try:
        conn = sqlite3.connect('utilisateurs.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET solde = ?
            WHERE chat_id = ?
        ''', (newsolde, user_id))
        
        conn.commit()
    except sqlite3.Error as e:
        logger.error("Error updating solde:", str(e))
    finally:
        conn.close()

def update_exp(exp, user_id):
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE users
            SET exp = ?
            WHERE chat_id = ?
        ''', (exp, user_id))
        conn.commit()
    except sqlite3.Error as e:
        logger.error("Error updating solde:", str(e))
    finally:
        conn.close()

def update_license(user_id):
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE users
            SET license = ?
            WHERE chat_id = ?
        ''', (1, user_id))
        conn.commit()
    except sqlite3.Error as e:
        logger.error("Error updating solde:", str(e))
    finally:
        conn.close()

def update_user_pwd(user_id , user , pwd):
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE users
            SET user = ? , pass = ?
            WHERE chat_id = ?
        ''', (user , pwd , user_id))
        conn.commit()
    except sqlite3.Error as e:
        logger.error("Error updating solde:", str(e))
    finally:
        conn.close()

def get_user_pwd(user_id):
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    for id , user , pwd , exp , license ,solde in users:
        if str(id) == str(user_id):
            if license == 1 :
                return user , pwd
            else:
                return None , None
    return None , None 

def is_valid_callerID(callerID):
    return callerID.isdigit()

def extract_arrays(response):
    array_blocks = reg(r"Array\s*\((.*?)\)", response, DOTALL)
    parsed_arrays = []
    for block in array_blocks:
        array_data = {}
        lines = block.strip().split("\n")
        for line in lines:
            if "=>" in line:
                key, value = search(r"\[(.*?)\] => (.*?)$", line).groups()
                array_data[key.strip()] = value.strip()
        parsed_arrays.append(array_data)
    return parsed_arrays

def get_license_details(user_id):
    us, pwd = get_user_pwd(user_id)
    return "<b>Host</b>: <code>sip.new-bot.com</code>\n<b>User</b>: <code>{}</code>\n<b>Password</b>: <code>{}</code>".format(
        us, pwd
    )

def randomize():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for i in range(10))

def d2m():
    current_time = datetime.now()
    ms = int(current_time.microsecond / 100)
    return int(time.mktime(current_time.timetuple()) * 1000 + ms)

def pass_gen():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for i in range(30))

def create_user(user_id , bal):
    try:
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ssh, username=username_ssh, password=password_ssh)
        _stdin, _stdout, _stderr = client.exec_command("ls")
        res = _stdout.read().decode()
        if "Invalid argument" not in str(res):
            _stdin, _stdout, _stderr = client.exec_command(
                "php /home/magnusapi/createuser.php {} {}".format(user_id , bal)
            )
            xx = _stdout.read().decode()
            if "[success] => 1" in str(xx):
                us = reg(r"\[username\] => (.*?)\n", str(xx))[0]
                pwd = reg(r"\[password\] => (.*?)\n", str(xx))[0]

                logger.info('[{}LOG{}] [{}{}{}] [{}NEW USER{}] USER > {}{}{}'.format(fg,fw,fg,current(),fw,fg,fw,fr,user_id,fw))

                return us , pwd
            client.close()
    except Exception as e:
        logger.error("user error occurred:", str(e))
    return

def get_and_print_history(user_id):
    def extract_info(row):
        called_station = search(r'\[calledstation\] => (.*?)\n', str(row)).group(1)
        caller_id = search(r'\[callerid\] => (.*?)\n', str(row)).group(1)
        start_time = search(r'\[starttime\] => (.*?)\n', str(row)).group(1)
        session_time = search(r'\[sessiontime\] => (.*?)\n', str(row)).group(1)

        message = f"\n📞 <b>Numéro appelé:</b> <code>{called_station}</code>\n📞 <b>Caller ID:</b> <code>{caller_id}</code>\n⏰ <b>Heure:</b> <code>{start_time}</code>\n⌛ <b>Durée de l'appel:</b> <code>{session_time} seconds</code>"

        return message

    def extract_arrays(response):
        return reg(r'\[\d+\] => Array\n\s+\((.*?)\n\s+\)', response, DOTALL)

    try:
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ssh, username=username_ssh, password=password_ssh)
        _stdin, _stdout, _stderr = client.exec_command("ls")
        res = _stdout.read().decode()
        if "Invalid argument" not in str(res):
            _stdin, _stdout, _stderr = client.exec_command(
                "php /home/magnusapi/gethistory.php {}".format(user_id)
            )
            xx = _stdout.read().decode()
            arrays = extract_arrays(xx)
            i = 0
            caption = ""
            client.close()
            if arrays:
                for array in arrays:
                    formatted_message = extract_info(array)
                    if i != 4:
                        caption += f"{formatted_message}\n\n{'='*30}\n"
                    else:
                        caption += f"{formatted_message}"
                    i += 1
                    if i == 5 : 
                        break
                return caption
            else:
                return "Aucun historique d'appels disponible."
    except Exception as e:
        logger.error("user error occurred:", str(e))
    return

def has_license(user_id):
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    for row in users:
        if str(row[0]) == str(user_id):
            if row[4] == 0: 
                return False
            else:
                return True
    return False

def get_balance(user_id):
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()
    cursor.execute('SELECT solde FROM users WHERE chat_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        try:
            return float(result[0])
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting balance to float: {e}")
            return 0.0
    return 0.0

def get_balance_magnus(user_id):
    try:
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ssh, username=username_ssh, password=password_ssh)
        _stdin, _stdout, _stderr = client.exec_command("ls")
        res = _stdout.read().decode()
        if "Invalid argument" not in str(res):
            _stdin, _stdout, _stderr = client.exec_command(
                "php /home/magnusapi/users.php"
            )
            xx = _stdout.read().decode()
            arrays = extract_arrays(xx)
            for array in arrays:
                if array["username"] == str(user_id):
                    return array["credit"]
            client.close()
            return 0
    except Exception as e:
        logger.error("Balance error occurred:", str(e))

def get_exp(user_id):
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    for row in users:
        if str(row[0]) == str(user_id):
            return str(row[3])
    return False

def get_callerid(user_id):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ssh, username=username_ssh, password=password_ssh)
        _stdin, _stdout, _stderr = client.exec_command("php /home/magnusapi/sips.php")
        xx = _stdout.read().decode()
        client.close()
        array_blocks = str(xx).split("=> Array")
        for block in array_blocks:
            if "defaultuser" in str(block) and str(user_id) in str(block):
                callerid = reg(r"\[cid_number\] => (.*?)\n", str(block))[0]
                return callerid
        return None

    except Exception as e:
        logger.error("callerID error occurred:", str(e))

def change_callerID(user_id,callerID):
    try:
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ssh, username=username_ssh, password=password_ssh)
        _stdin, _stdout, _stderr = client.exec_command("ls")
        res = _stdout.read().decode()
        if "Invalid argument" not in str(res):
            _stdin, _stdout, _stderr = client.exec_command(
                "php /home/magnusapi/change_callerid.php {} {}".format(user_id, callerID)
            )
            xx = _stdout.read().decode()
            if "[success] => 1" in str(xx):
                logger.info('[{}LOG{}] [{}{}{}] [{}CALLEDID{}] USER > {}{}{} - NEW CALLERID > {}{}{} '.format(fg,fw,fg,current(),fw,fg,fw,fr,user_id,fw,fg,callerID,fw))
            client.close()
    except Exception as e:
        logger.error("changecallerID error occurred:", str(e))

def activelicense(user_id):
    update_license(user_id)
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ssh, username=username_ssh, password=password_ssh)

        _, stdout, stderr = client.exec_command("ls")
        ls_output = stdout.read().decode()
        if "Invalid argument" not in ls_output:
            _, stdout, stderr = client.exec_command("php /home/magnusapi/activelicense.php {}".format(user_id))
            result = stdout.read().decode()
            error = stderr.read().decode()
            exp = reg(r"\[expirationdate\] => (.*?)\n", str(result))[0]
            update_exp(exp , user_id)

        client.close()

    except Exception as e:
        logger.error("activatelicense error occurred:", str(e))

def extract_user(user_id):
    try:
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ssh, username=username_ssh, password=password_ssh)
        _stdin, _stdout, _stderr = client.exec_command("ls")
        res = _stdout.read().decode()
        if "Invalid argument" not in str(res):
            _stdin, _stdout, _stderr = client.exec_command(
                "php /home/magnusapi/users.php"
            )
            xx = _stdout.read().decode()
            arrays = extract_arrays(xx)
            for array in arrays:
                if array["username"] == str(user_id):
                    return array['credit']
            client.close()
            return False
    except Exception as e:
        logger.error("extractuser error occurred:", str(e))

def add_credit(user_id,count):
    try:
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ssh, username=username_ssh, password=password_ssh)
        _stdin, _stdout, _stderr = client.exec_command("ls")
        res = _stdout.read().decode()
        if "Invalid argument" not in str(res):
            _stdin, _stdout, _stderr = client.exec_command(
                "php /home/magnusapi/credit.php {} {}".format(user_id , count)
            )
    except Exception as e:
        logger.error("addcredit error occurred:", str(e))
    return

def is_fournisseur_online():
    fournisseur_url = "http://165.231.148.240/mbilling/"
    try:
        response = requests.get(fournisseur_url)
        if response.status_code == 200:
            return True  
    except requests.exceptions.RequestException:
        pass
    return False  

@bot.callback_query_handler(func=lambda call: call.data == "fournisseur")
def fournisseur_status(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)

    if is_fournisseur_online():
        status_message = "En ligne"
    else:
        status_message = "Hors ligne"

    caption = f"🌐 Le site du fournisseur est actuellement : {status_message}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
    markup.add(return_button)

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption=caption, reply_markup=markup, parse_mode='HTML')
        
def remove_credit(user_id,count):
    try:
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ssh, username=username_ssh, password=password_ssh)
        _stdin, _stdout, _stderr = client.exec_command("ls")
        res = _stdout.read().decode()
        if "Invalid argument" not in str(res):
            _stdin, _stdout, _stderr = client.exec_command(
                "php /home/magnusapi/credit.php {} -{}".format(user_id , count)
            )
    except Exception as e:
        logger.error("An error occurred:", str(e))

def update_change_pass(user_id , pwd):
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE users
            SET pass = ?
            WHERE chat_id = ?
        ''', (pwd , user_id))
        conn.commit()
    except sqlite3.Error as e:
        logger.error("Error updating solde:", str(e))
    finally:
        conn.close()

def changepass(user_id , mdp):
    try:
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ssh, username=username_ssh, password=password_ssh)
        _stdin, _stdout, _stderr = client.exec_command("ls")
        res = _stdout.read().decode()
        if "Invalid argument" not in str(res):
            _stdin, _stdout, _stderr = client.exec_command(
                "php /home/magnusapi/changepass.php {} {}".format(user_id , mdp)
            )
    except Exception as e:
        logger.error("removesip error occurred:", str(e))
    return 

def get_calls_online():
    try:
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ssh, username=username_ssh, password=password_ssh)
        _stdin, _stdout, _stderr = client.exec_command("ls")
        res = _stdout.read().decode()
        if "Invalid argument" not in str(res):
            _stdin, _stdout, _stderr = client.exec_command(
                "php /home/magnusapi/callsonline.php"
            )
            xx = _stdout.read().decode()
            if "[count] =>" in str(xx):
                count = reg(r"\[count\] => (.*?)\n", str(xx))[0]
                return count
            return 0
    except Exception as e:
        logger.error("addcredit error occurred:", str(e))
    return

def removelicense_magnus(user_id):
    try:
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ssh, username=username_ssh, password=password_ssh)
        _stdin, _stdout, _stderr = client.exec_command("ls")
        res = _stdout.read().decode()
        if "Invalid argument" not in str(res):
            _stdin, _stdout, _stderr = client.exec_command(
                "php /home/magnusapi/removelicense.php {}".format(user_id)
            )
    except Exception as e:
        logger.error("addcredit error occurred:", str(e))
    return

@bot.callback_query_handler(func=lambda call : call.data == "confirm_changepassword")
def handle_confirmation(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)

    user_data = user_data_dict.get(user_id, {})
    new_password = user_data.get("new_password")
    if new_password:
        update_change_pass(user_id , new_password)
        changepass(user_id, new_password)

        caption = "✅ Le mot de passe a été changé avec succès!"
        markup = types.InlineKeyboardMarkup(row_width=1)
        return_button = types.InlineKeyboardButton("🔙 Menu", callback_data="return")
        markup.add(return_button)
        with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
            bot.send_photo(user_id, photo, caption, reply_markup=markup)
    del user_data_dict[user_id]

def new_mdp():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for i in range(10))

@bot.callback_query_handler(func=lambda call: call.data == "changepassword")
def changepassword(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)

    new_password  = new_mdp()

    caption = f"<b>Nouveau mot de passe :</b> <code>{new_password }</code>\n\nCliquez sur « <b>✅ Confirmer</b> » pour appliquer la modification."
    markup = types.InlineKeyboardMarkup(row_width=2)
    confirm_button = types.InlineKeyboardButton("✅ Confirmer", callback_data="confirm_changepassword")
    return_button = types.InlineKeyboardButton("❌ Annuler", callback_data="return")
    markup.add(confirm_button,return_button)
    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption , reply_markup=markup , parse_mode='HTML')

    user_data_dict[user_id] = {"new_password": new_password}

@bot.callback_query_handler(func=lambda call: call.data == "passwordsip")
def password_sip_callback(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)

    if has_license(user_id):
        license_details = get_license_details(user_id)
        caption = f"🔒 <b><u>T'es informations SIP:</u></b>🔒\n\n{license_details}"
        caption += "\n\n<b>⚠️ IL EST INTERDIT DE PARTAGEZ VOS IDENTIFIANTS DE CONNEXION ⚠️</b>"
        markup = types.InlineKeyboardMarkup(row_width=2)
        changepassword = types.InlineKeyboardButton("🔄 Changer le mot de passe", callback_data="changepassword")
        erreur_button = types.InlineKeyboardButton("‼️ Listes des erreurs", callback_data="erreur")
        return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
        markup.add(changepassword, erreur_button, return_button)
    else:
        caption = "🛑 Tu n'as pas/plus la licence 🛑"
        markup = types.InlineKeyboardMarkup(row_width=1)
        buy_license_button = types.InlineKeyboardButton("💶 Acheter la license", callback_data="buy_license")
        return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
        markup.add(buy_license_button, return_button)

    try:
        with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
            bot.send_photo(user_id, photo, caption, reply_markup=markup, parse_mode="HTML")
    except:
        main_menu(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "erreur")
def erreur_callback(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)

    caption = """
    <b>🚀 Bienvenue sur Test_BotSpoofer ® </b>

<b>⁉️ Voici une aide pour les problèmes les plus fréquents :</b>

"""

    markup = types.InlineKeyboardMarkup(row_width=2)
    stun_dns_button = types.InlineKeyboardButton("1. Erreur STUN DNS", callback_data="stun_dns")
    unauthorized_button = types.InlineKeyboardButton("2. Erreur Unauthorized", callback_data="unauthorized")
    declined_button = types.InlineKeyboardButton("3. Erreur Declined", callback_data="declined")
    timeout_button = types.InlineKeyboardButton("4. Erreur Request Timeout", callback_data="request_timeout")
    all_circuits_busy_button = types.InlineKeyboardButton("5. Erreur All Circuits Are Busy Now", callback_data="all_circuits_busy")
    support_button = types.InlineKeyboardButton("📩 Support", url="https://t.me/Test_BotSenderID")
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")

    markup.add(stun_dns_button, unauthorized_button)
    markup.add(declined_button, timeout_button)
    markup.add(all_circuits_busy_button)
    markup.add(support_button, return_button)

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "stun_dns")
def stun_dns_callback(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    
    caption = """<b>1. Erreur STUN DNS :</b>
<i>Solution initiale :</i>
- Accédez à votre compte SIP.
- Allez en bas de la page et ouvrez les "Paramètres Réseaux".
- Désactivez la fonction "STUN".
"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="erreur")
    markup.add(return_button)

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "unauthorized")
def unauthorized_callback(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    
    caption = """<b>2. Erreur Unauthorized :</b>
<i>Cause :</i> Votre mot de passe est incorrect, il a peut-être été changé ou mal copié.
<i>Solution :</i>
- Allez sur le bot et sélectionnez "Accès SIP" puis "Changer le mot de passe".
- Copiez et collez le nouveau mot de passe.
"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="erreur")
    markup.add(return_button)

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "declined")
def declined_callback(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    
    caption = """<b>3. Erreur Declined lors des appels :</b>
<i>Cause :</i> Votre compte n'a plus de crédit.
<i>Solution :</i>
- Vérifiez votre crédit en utilisant la commande /start sur le bot.
- Rechargez votre compte via le bouton sur @Test_BotpooferBOT.
"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="erreur")
    markup.add(return_button)

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "request_timeout")
def request_timeout_callback(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    
    caption = """<b>4. Erreur Request Timeout :</b>
<i>Cause :</i> Si une annonce indique que le service est indisponible, attendez sa réactivation.
<i>Solution :</i>
- Si aucune annonce n'a été faite, essayez de vous connecter en utilisant la 4G au lieu du WiFi, un VPN, ou changez d'adresse IP.
"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="erreur")
    markup.add(return_button)

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "all_circuits_busy")
def all_circuits_busy_callback(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    
    caption = """<b>5. Erreur "All Circuits Are Busy Now" (message audio en anglais) :</b>
<i>Solution :</i> Contactez @Test_BotSenderID, car plusieurs raisons peuvent être à l'origine de ce problème et une assistance directe sera nécessaire.
"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="erreur")
    markup.add(return_button)

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "buy_license")
def buy_license_callback(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)

    caption = f"""💳 Le prix de la licence est de {str(sub_price)}€/mois

Clique sur confirmer pour l'acheter
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    buy_license_button = types.InlineKeyboardButton(
        "✨ Je confirme", callback_data="confirmation"
    )
    return_button = types.InlineKeyboardButton("🔙 Menu", callback_data="return")
    markup.add(buy_license_button, return_button)
    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "confirmation")
def confirmation_payment(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)

    try:
        bal = get_balance(user_id)
        if bal == False:
            bal = 0
    except:
        bal = 0.0
    if float(bal) < float(sub_price):
        caption = """🛑 Tu n'as pas assez de solde pour acheter la licence merci de recharger 🛑"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        recharge = types.InlineKeyboardButton(
            "💳 Recharger", callback_data="recharge"
        )
        return_button = types.InlineKeyboardButton("🔙 Menu", callback_data="return")
        markup.add(recharge, return_button)
        with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
            bot.send_photo(user_id, photo, caption, reply_markup=markup)
    else:
        bal = float(bal) - float(sub_price)
        us , pwd = create_user(user_id , bal)
        update_user_pwd(user_id , us , pwd)
        update_solde(bal , user_id)
        activelicense(user_id)
        logger.info('[{}LOG{}] [{}{}{}] [{}LICENSE{}] {}{}{} just bought license.'.format(fg,fw,fg,current(),fw,fg,fw,fr,user_id,fw))
        caption = """<b>✅ Achat avec succès</b>
<b>💰Solde Restant</b> : {:.2f}
""".format(bal)
        markup = types.InlineKeyboardMarkup(row_width=1)
        return_button = types.InlineKeyboardButton("🔙 Menu", callback_data="return")
        markup.add(return_button)

        with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
            bot.send_photo(user_id, photo, caption, reply_markup=markup,parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "callerID")
def caller_id_callback(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)

    if has_license(user_id):
        caption = ""
        callerID = get_callerid(user_id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        if callerID:
            caption = f"👤<b>CallerID</b> : {callerID}"
        else:
            caption = "Vous n'avez pas encore configuré de CallerID\n\nC'est obligatoire pour appeler"
        callerid_idea = types.InlineKeyboardButton("🏦 Les numéros d'oppostion ", callback_data="callerididea")
        change_callerID = types.InlineKeyboardButton("🔁 Change ton caller ID", callback_data="change_callerID")
        return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
        
        markup.add(change_callerID, callerid_idea, return_button)
        with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
            bot.send_photo(user_id, photo, caption, reply_markup=markup, parse_mode="HTML")
    else:
        caption = "🛑 Tu n'as pas la licence 🛑"
        markup = types.InlineKeyboardMarkup(row_width=1)
        buy_license_button = types.InlineKeyboardButton("💶 Acheter la licence", callback_data="buy_license")
        recharge_button = types.InlineKeyboardButton("💳 Recharge", callback_data="recharge")
        return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
        markup.add(buy_license_button, recharge_button, return_button)

        with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
            bot.send_photo(user_id, photo, caption, reply_markup=markup, parse_mode="HTML")

def handle_new_callerID_or_text(message):
    user_id = message.chat.id
    xxxxx = message.text

    if is_valid_callerID(xxxxx):
        change_callerID(user_id, xxxxx)
        response = f"📲 Ton CallerID a bien été modifié 📲\n\nTon CallerID est maintenant: {xxxxx}"
        markup = types.InlineKeyboardMarkup(row_width=1)
        back = types.InlineKeyboardButton("🔙 Menu", callback_data="return")
        markup.add(back)
    else:
        response = "❌ Ce numéro n'est pas valide ❌\n\nVoici un exemple: 33194134874"
        markup = types.InlineKeyboardMarkup(row_width=1)
        restart = types.InlineKeyboardButton(
            "🔄 Recommencer ", callback_data="change_callerID"
        )
        back = types.InlineKeyboardButton("❌ Annuler", callback_data="return")
        markup.add(restart, back)
    
    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, response, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "change_callerID")
def change_callerID_callback(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)

    caption = "Envoie ci-dessous le numéro (CallerID) avec lequel tu veux appeler"

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption)

    bot.register_next_step_handler_by_chat_id(user_id, handle_new_callerID_or_text)

def timeleft(bal): 
    call_price = 0.45

    timeleft = (bal / call_price) * 60

    hours = int(timeleft // 3600)
    minutes = int((timeleft % 3600) // 60)
    seconds = int(timeleft % 60)

    return '{}h:{}m:{}s'.format(hours, minutes, seconds)

@bot.callback_query_handler(func=lambda call: call.data == "restart")
def restart_callback(call):
    change_callerID_callback(call)

@bot.callback_query_handler(func=lambda call: call.data == "callerididea")
def callerid_idea(call):
    user_id = call.message.chat.id
    try:
        bot.delete_message(user_id, call.message.message_id)
    except ApiTelegramException as e:
        if "message can't be deleted for everyone" in str(e) or "message to delete not found" in str(e):
            # Silently handle the error without logging or printing anything
            pass
    finally:
        # Proceed with the rest of your logic, e.g., sending the caller ID suggestions
        caption = """ 
<b>🏦 Crédit Agricole </b>: <code>33969399291</code>
<b>🏦 Société générale </b>: <code>33969393339</code>
<b>🏦 La Banque Postale </b>: <code>33969399998</code>
<b>🏦 Caisse d'Epargne </b>: <code>33969363939</code>
<b>🏦 La Banque Populaire </b>: <code>33177862424</code>
<b>🏦 BNP Paribas </b>: <code>33140141010</code>
<b>🏦 CIC </b>: <code>33388398578</code>
<b>🏦 LCL </b>: <code>33969327777</code>
<b>🏦 Crédit Mutuel </b>: <code>33388401000</code>
<b>🏦 HSBC </b>: <code>33892683208</code>
<b>🏦 Banque de France </b>: <code>33892705705</code>
"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
        markup.add(return_button)
        with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
            bot.send_photo(user_id, photo, caption, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "historiqueappel")
def historiqueappel(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id , call.message.message_id)

    caption = get_and_print_history(user_id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
    markup.add(return_button)
    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "accountsettings")
def account_settings_callback(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)

    user_info = bot.get_chat_member(chat_id=user_id, user_id=user_id).user
    username = user_info.username
    markup = types.InlineKeyboardMarkup(row_width=2)

    bal = float(get_balance(user_id))
    if bal == False:
        bal = 0

    if has_license(user_id):
        bal = float(get_balance_magnus(user_id))
        caption = f"👤 @{username} ({user_id})\n\n"
        caption += "💰<b>SOLDE</b> : {:.2f}€".format(float(bal))
        caption += "\n\n⌛ <b>Reste</b> : {}".format(timeleft(float(bal)))
        caption += f"\n\n<b>📆DATE D'EXPIRATION</b> : {str(get_exp(user_id))}"
        historique = types.InlineKeyboardButton("📜 Ton historique d'appel" , callback_data="historiqueappel")
        recharge_button = types.InlineKeyboardButton("💶 Recharge", callback_data="recharge")
        return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
        markup.add(historique,recharge_button , return_button)
    else:
        caption = f"👤 @{username} ({user_id})\n\n"
        caption += "💰<b>SOLDE</b> : {:.2f}€".format(float(bal))
        caption += "\n\n🛑 Tu n'as pas la licence 🛑"
        buy_license_button = types.InlineKeyboardButton("✨ Acheter la licence", callback_data="buy_license")
        recharge_button = types.InlineKeyboardButton("💶 Recharge", callback_data="recharge")
        return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
        markup.add(buy_license_button , recharge_button , return_button)

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption, reply_markup=markup, parse_mode="HTML")

def converter(coin, currency, amount):
    if '.' in str(coin):
        coin = str(coin).split('.')[0]
    url = f'https://api.coinconvert.net/convert/{coin}/{currency}?amount={amount}'
    data = requests.get(url)
    req = data.json()
    return str(req[currency])

def curl_coin_payment(postdata):
    url = "https://www.coinpayments.net/api.php"
    payload = postdata
    payload['key'] = public_key
    payload['version'] = 1
    payload = "&".join([f"{key}={value}" for key, value in payload.items()])

    apiseal = hmac.new(private_key.encode('utf-8'), payload.encode('utf-8'), hashlib.sha512).hexdigest()

    headers = {
        "HMAC": apiseal,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(url, data=payload, headers=headers)
    return response

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_callback(call):
    user_id = call.message.chat.id
    user_username = call.from_user.username
    logging.info(f"L'utilisateur {user_username} accède à la page de rechargement.")
    caption = """
<b>💰 Pour recharger, clique simplement sur la monnaie de ton choix ci-dessous et suis les instructions pour envoyer le montant désiré :</b>
    """
    markup = types.InlineKeyboardMarkup(row_width=2)
    BTC = types.InlineKeyboardButton('Bitcoin [BTC]', callback_data='payment_BTC')
    ETH = types.InlineKeyboardButton('Ether [ETH]', callback_data='payment_ETH')
    LTC = types.InlineKeyboardButton('Litecoin [LTC]', callback_data='payment_LTC')
    USDTE = types.InlineKeyboardButton('USDT [ERC20]', callback_data='payment_USDT.ERC20')
    USDTT = types.InlineKeyboardButton('USDT [TRC20]', callback_data='payment_USDT.TRC20')
    SOL = types.InlineKeyboardButton('Monero [XMR]', callback_data='payment_XMR')
    retour = types.InlineKeyboardButton('🔙 Retour', callback_data='return')

    markup.add(BTC, ETH, LTC, USDTE, USDTT, SOL, retour)
    if call.message.photo:
        bot.edit_message_caption(chat_id=user_id, message_id=call.message.message_id, caption=caption, reply_markup=markup, parse_mode='HTML')
    else:
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=caption, reply_markup=markup, parse_mode='HTML')

def mark_transaction_completed(chat_id, message_id):
    completed_button = types.InlineKeyboardButton("✅ complété", callback_data="completed")
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(completed_button)

    try:
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=markup)
    except: pass

@bot.callback_query_handler(func=lambda call: call.data == "fermer")
def cancel_order(call):
    user_id = call.message.chat.id
    data = call.data.split("_")

    completed_button = types.InlineKeyboardButton("❌ annulé", callback_data="cancelled")
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(completed_button)

    # try:
    #     bot.delete_message(user_id, call.message.message_id)
    # except:
    #     pass

    try:
        bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=markup)
    except: pass
    


# @bot.callback_query_handler(func=lambda call: call.data.startswith("payment_"))
# def payment_callback(call):
#     user_id = call.message.chat.id
#     data = call.data.split("_")

#     if len(data) > 2:
#         try:
#             bot.delete_message(user_id, call.message.message_id)
#         except:
#             pass
    
#     payment_type = data[1]  
#     network = None
#     if 'USDT' in payment_type.upper():
#         network = payment_type.split('.')[-1]
#         payment_type = 'USDT'
#     amount = 100
    
#     order_id = str(uuid.uuid4())
#     # By default, we generate
#     # Handle white-label payment
#     if len(data) == 2 or data[-1] == "wl":
#         pay_link, track_id, address, payamount = create_white_label_invoice(user_id, amount, payment_type,order_id, network=network)

#         if pay_link and track_id:
#             try:
#                 img = requests.get(pay_link).content
#             except:
#                 img = None
                
#             caption = f"""
# 📝 *Détails de la transaction :*

# 💱 *Choix :* {payment_type.upper() + f'.{network}' if network else payment_type.upper()}
# 🔗 *addresse pour le paiement :* `{address}`
# 💰 *montante :* {payamount}

# addresse expirera dans 30 minutes.
# """
#             # Add buttons for confirming payment and returning to standard invoice
#             done_button = types.InlineKeyboardButton("✅ C'est fait", callback_data="fermer")
#             cancel_button = types.InlineKeyboardButton("❌ Annuler", callback_data="return")
#             toggle_button = types.InlineKeyboardButton("🔄 méthode alternative", callback_data=f"payment_{payment_type}_in")

#             markup = types.InlineKeyboardMarkup(row_width=2)
#             markup.add(cancel_button, toggle_button)
#             # markup.add(toggle_button)
#             if img:
#                 msg = bot.send_photo(user_id, photo=img, caption=caption, reply_markup=markup, parse_mode='Markdown')
#             else:
#                 with open(image_path, 'rb') as photo:
#                     msg=bot.send_photo(user_id, photo=photo, caption=caption, reply_markup=markup, parse_mode='Markdown')

#             order_id = msg.message_id
#             add_transaction(user_id, f'{payment_type}-Whitelabel', amount, 'EUR', track_id, 'Pending', order_id)
#         else:
#             bot.send_message(user_id, "Erreur lors de la création de l'invoice crypto. Réessayez plus tard.")

#     elif data[-1] == "in":
#         pay_link, track_id = create_invoice(user_id, payment_type, amount, order_id)

#         if pay_link and track_id:
#             caption = f"""
# 📝 *Détails de la transaction :*

# 💱 *Monnaie :* vous pouvez payer dans la devise de votre choix
# 💰 *Montant :* {amount} EUR
# 🔗 *Lien de paiement :* [Cliquez ici pour payer]({pay_link})

# Veuillez procéder au paiement via le lien ci-dessus. Le lien expirera dans 30 minutes.
# """
#             # Add buttons for toggling and confirming payment
#             done_button = types.InlineKeyboardButton("✅ C'est fait", callback_data="fermer")
#             cancel_button = types.InlineKeyboardButton("❌ Annuler", callback_data="return")
#             toggle_button = types.InlineKeyboardButton("🔄 méthode alternative", callback_data=f"payment_{payment_type + f'.{network}' if network else payment_type}_wl")

#             markup = types.InlineKeyboardMarkup(row_width=2)
#             # markup.add(done_button, cancel_button, toggle_button)
#             markup.add(cancel_button,toggle_button)

#             with open(image_path, 'rb') as photo:
#                 msg = bot.send_photo(user_id, photo=photo, caption=caption, reply_markup=markup, parse_mode='Markdown')
#             order_id = msg.message_id
#             add_transaction(user_id, 'Invoice', amount, 'EUR', track_id, 'Pending', order_id)
#         else:
#             bot.send_message(user_id, "Erreur lors de la création de l'invoice. Réessayez plus tard.")




# @bot.callback_query_handler(func=lambda call: call.data.startswith("payment_"))
# def payment_callback(call):
#     user_id = call.message.chat.id
#     data = call.data.split("_")

#     if len(data) > 2:
#         try:
#             bot.delete_message(user_id, call.message.message_id)
#         except:
#             pass
    
#     amount_data = call.data.split(":")

#     if len(amount_data) == 2:
#         try:
#             amount = float(amount_data[1])
#         except:
#             print('bad amount format')
#             amount = None
#     else: amount = None
            

#     payment_type = data[1]
#     network = None
#     if 'USDT' in payment_type.upper():
#         network = payment_type.split('.')[-1]
#         payment_type = 'USDT'


#     if amount:
#         converted_amount = converter(payment_type, "EUR", amount)
#         create_payment_flow(user_id, payment_type, network, converted_amount, call, xx = amount)

#     else:
#         # Ask the user to input the amount they want to recharge
#         msg = bot.send_message(user_id, f"Veuillez entrer le montant que vous souhaitez recharger en {payment_type.upper()} :")
#         bot.register_next_step_handler(msg, process_recharge_amount, payment_type, network, call)

# def process_recharge_amount(message, payment_type, network, call, amount=None):
#     user_id = message.chat.id
    
#     try:

#         print(message.text)
#         # Get the amount input by the user
#         amount = float(message.text)
#     except ValueError:
#         bot.send_message(user_id, "Montant non valide, veuillez entrer un nombre.")
#         bot.register_next_step_handler(message, process_recharge_amount, payment_type, network, call)

#     else:
#         # Convert the amount in the selected coin to EUR
#         converted_amount = converter(payment_type, "EUR", amount)

#         # Continue with the payment flow, creating the invoice or white-label invoice
#         create_payment_flow(user_id, payment_type, network, converted_amount, call, xx = amount)

    

# def create_payment_flow(user_id, payment_type, network, amount, call, xx):
#     order_id = str(uuid.uuid4())

#     # Check if user selected white-label payment
#     if len(call.data.split("_")) == 2 or 'wl' in call.data.split("_")[-1]:
#         pay_link, track_id, address, payamount = create_white_label_invoice(user_id, amount, payment_type, order_id, network=network)

#         payamount = xx if float(converter(payment_type,'EUR',abs(xx - float(payamount)))) < 0.2 else payamount

#         if pay_link and track_id:
#             # Handle sending the image or QR code
#             send_payment_details(user_id, pay_link, address, payamount, payment_type, network)
#             add_transaction(user_id, f'{payment_type}-Whitelabel', amount, 'EUR', track_id, 'Pending', order_id)
#         else:
#             bot.send_message(user_id, "Erreur lors de la création de l'invoice crypto. Réessayez plus tard.")

#     # If it's a standard invoice
#     elif "in" in call.data.split("_")[-1]:
#         pay_link, track_id = create_invoice(user_id, payment_type, amount, order_id)

#         if pay_link and track_id:
#             caption = f"""
# 📝 *Détails de la transaction :*

# 💱 *Monnaie :* {payment_type.upper()}
# 💰 *Montant :* {amount} EUR
# 🔗 *Lien de paiement :* [Cliquez ici pour payer]({pay_link})

# Veuillez procéder au paiement via le lien ci-dessus. Le lien expirera dans 30 minutes.
# """
#             markup = types.InlineKeyboardMarkup(row_width=2)
#             cancel_button = types.InlineKeyboardButton("❌ Annuler", callback_data="return")
#             toggle_button = types.InlineKeyboardButton("🔄 méthode alternative", callback_data=f"payment_{payment_type + f'.{network}' if network else payment_type}_wl:{xx}")
#             markup.add(cancel_button,toggle_button)

#             with open(image_path, 'rb') as photo:
#                 bot.send_photo(user_id, photo=photo, caption=caption, reply_markup=markup, parse_mode='Markdown')
            
#             add_transaction(user_id, 'Invoice', amount, 'EUR', track_id, 'Pending', call.message.message_id)
#         else:
#             bot.send_message(user_id, "Erreur lors de la création de l'invoice. Réessayez plus tard.")

# def send_payment_details(user_id, pay_link, address, payamount, payment_type, network):
#     caption = f"""
# 📝 *Détails de la transaction :*

# 💱 *Choix :* {payment_type.upper() + f'.{network}' if network else payment_type.upper()}
# 🔗 *addresse pour le paiement :* `{address}`
# 💰 *montante :* {payamount}

# addresse expirera dans 30 minutes.
# """
    
#     markup = types.InlineKeyboardMarkup(row_width=2)
#     cancel_button = types.InlineKeyboardButton("❌ Annuler", callback_data="return")
#     toggle_button = types.InlineKeyboardButton("🔄 méthode alternative", callback_data=f"payment_{payment_type + f'.{network}' if network else payment_type}_in:{payamount}")
#     markup.add(cancel_button, toggle_button)

#     img = requests.get(pay_link).content
#     bot.send_photo(user_id, photo=img, caption=caption, reply_markup=markup, parse_mode='Markdown')

# def worker(user_id, txn_id, message_id = None):
#     amount_x,amount_sent, coin = confirm_oxa_payment(txn_id)
#     if amount_x and coin:
#         conn = sqlite3.connect('utilisateurs.db')
#         cursor = conn.cursor()

#         montant = float(amount_sent)
#         current_balance = get_balance(user_id)
#         new_balance = current_balance + montant
        
#         # Update the balance in the local database
#         update_solde(new_balance, user_id)
        
#         # Update the balance in MagnusBilling
#         add_credit(user_id, montant)

#         conn.commit()
#         conn.close()

#         if message_id:
#             mark_transaction_completed(user_id, message_id)
#         print(f'[LOG] [{user_id}] [RECEIVED: {amount_sent}€ ≈ {amount_x} {coin}]')
#         with open('recharge_logs.txt', 'a', errors='ignore') as log_file:
#             log_file.write(f'[LOG] [USERID: {user_id}] [COIN: {coin}] [RECEIVED: {amount_sent}]\n')
#         confirmation_message = f"💰 Votre paiement de *{float(amount_sent):.2f} €* a été reçu et ajouté à votre compte. Merci !\n\nPour revenir au menu principal, veuillez entrer la commande /start, s'il vous plaît."
#         with open('photo_2023-11-05_00-09-39.png', 'rb') as photo:
#             bot.send_photo(user_id, photo, caption=confirmation_message, parse_mode='Markdown')
#     else:
#         print(f'[LOG] [{user_id}] Payment confirmation failed.')
def get_qr_code(address):
    # generate qr code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=3,
    )
    qr.add_data(address)
    qr.make(fit=True)

    # save qr code as png image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_img.save('buffer.png', format='PNG')
    
    qr_bytes = buffer.getvalue()
    return qr_bytes

@bot.callback_query_handler(func=lambda call: call.data.startswith("payment_"))
def payment_callback(call):
    user_id = call.message.chat.id
    data = call.data.split("_")

    if len(data) > 2:
        try:
            bot.delete_message(user_id, call.message.message_id)
        except:
            pass
    
    payment_type = data[1]  
    network = None
    if 'USDT' in payment_type.upper():
        network = payment_type.split('.')[-1]
        payment_type = 'USDT'
    # amount = 100
    
    order_id = str(uuid.uuid4())
    address = create_static_address(user_id, payment_type,order_id, network=network)

    if address:
        try:
            img = get_qr_code(address)
        except:
            img = None
            
        caption = f"""
📝 *Détails de la transaction :*

💱 *Choix :* {payment_type.upper() + f'.{network}' if network else payment_type.upper()}
🔗 *addresse pour le paiement :* `{address}`
"""
        # Add buttons for confirming payment and returning to standard invoice
        done_button = types.InlineKeyboardButton("✅ C'est fait", callback_data="fermer")
        cancel_button = types.InlineKeyboardButton("❌ Annuler", callback_data="return")

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(cancel_button)
        # markup.add(toggle_button)
        if img:
            msg = bot.send_photo(user_id, photo=img, caption=caption, reply_markup=markup, parse_mode='Markdown')
        else:
            with open(image_path, 'rb') as photo:
                msg=bot.send_photo(user_id, photo=photo, caption=caption, reply_markup=markup, parse_mode='Markdown')
                
        add_transaction(user_id, f'{payment_type}-Static-{address}', None, None, None, 'Pending', order_id)
    else:
        bot.send_message(user_id, "Erreur lors de la création de l'invoice crypto. Réessayez plus tard.")


def worker(user_id, amount, coin,order_id, message_id = None):
    # amount_x,amount_sent, coin = confirm_oxa_payment(txn_id)
    # print('payment confirmed')
    
    if amount and coin:
        conn = sqlite3.connect('utilisateurs.db')
        cursor = conn.cursor()

        amount_sent = converter(coin,'EUR',amount)
        montant = float(amount_sent)
        current_balance = get_balance(user_id)
        new_balance = current_balance + montant
        
        # Update the balance in the local database
        update_solde(new_balance, user_id)
        
        # Update the balance in MagnusBilling
        add_credit(user_id, montant)

        conn.commit()
        conn.close()

        if message_id:
            mark_transaction_completed(user_id, message_id)
        logger.info(f'[LOG] [{user_id}] [RECEIVED: {amount_sent}€ ≈ {amount} {coin}]')
        with open('recharge_logs.txt', 'a', errors='ignore') as log_file:
            log_file.write(f'[LOG] [USERID: {user_id}] [COIN: {coin}] [RECEIVED: {amount_sent}]\n')
        confirmation_message = f"💰 Votre paiement de *{float(amount_sent):.2f} €* a été reçu et ajouté à votre compte. Merci !\n\nPour revenir au menu principal, veuillez entrer la commande /start, s'il vous plaît."
        with open('photo_2023-11-05_00-09-39.png', 'rb') as photo:
            bot.send_photo(user_id, photo, caption=confirmation_message, parse_mode='Markdown')
    else:
        logger.info(f'[LOG] [{user_id}] Payment confirmation failed.')

def send_status_change(user_id,status, amount, coin):
    # amount_x,amount_sent, coin = confirm_oxa_payment(txn_id)
    # print('payment confirmed')
    
    if amount and coin:
        amount_sent = converter(coin,'EUR',amount)
        montant = float(amount_sent)

        confirmation_message = f"💰 votre transfert de *{float(amount):.2f} {coin}* est {status}"
        with open('photo_2023-11-05_00-09-39.png', 'rb') as photo:
            bot.send_photo(user_id, photo, caption=confirmation_message, parse_mode='Markdown')
    else:
        logger.info(f'[LOG] [{user_id}] send Payment status update failed.')


@bot.callback_query_handler(func=lambda call: call.data == "return")
def return_to_main_menu(call):
    user_id = call.message.chat.id
    try:
        bot.delete_message(user_id, call.message.message_id)
    except ApiTelegramException as e:
        if "message to delete not found" in str(e) or "message can't be deleted for everyone" in str(e):
            # Silently handle the error without printing anything
            pass
    finally:
        main_menu(user_id)

def handle_addcredit_text(message):
    user_id = message.chat.id
    if user_id in user_states:
        state = user_states[user_id]["step"]
        user_msg = message.text

        if state == 0:
            credit = extract_user(user_msg)
            creditlocal = get_balance(user_msg)
            if float(credit) == 0 or float(credit) > 0:
                user_states[user_id]["user_msg"] = user_msg
                user_states[user_id]["credit"] = credit
                user_states[user_id]["step"] = 1 
                caption = "Combien voulez vous ajouter du credit?"
                with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
                    bot.send_photo(user_id, photo, caption)
                bot.register_next_step_handler(message, handle_addcredit_amount)
            elif float(creditlocal) == 0 or float(creditlocal) > 0:
                user_states[user_id]["user_msg"] = user_msg
                user_states[user_id]["credit"] = creditlocal
                user_states[user_id]["step"] = 1 
                caption = "Combien voulez vous ajouter du credit?"
                with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
                    bot.send_photo(user_id, photo, caption)
                bot.register_next_step_handler(message, handle_addcredit_amount)
            else:
                caption = "Username {} n'existe pas.".format(user_states[user_id]["user_msg"])
                with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
                    bot.send_photo(user_id, photo, caption)

def handle_removecredit_text(message):
    user_id = message.chat.id
    if user_id in user_states:
        state = user_states[user_id]["step"]
        user_msg = message.text
        if state == 0:
            credit = extract_user(user_msg)
            creditlocal = get_balance(user_msg)
            if float(credit) == 0 or float(credit) > 0:
                user_states[user_id]["user_msg"] = user_msg
                user_states[user_id]["credit"] = credit
                user_states[user_id]["step"] = 1 
                caption = "Combien voulez vous retirer du credit?"
                with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
                    bot.send_photo(user_id, photo, caption)
                bot.register_next_step_handler(message, handle_removecredit_amount)
            elif float(creditlocal) == 0 or float(creditlocal) > 0:
                user_states[user_id]["user_msg"] = user_msg
                user_states[user_id]["credit"] = creditlocal
                user_states[user_id]["step"] = 1 
                caption = "Combien voulez vous retirer du credit?"
                with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
                    bot.send_photo(user_id, photo, caption)
                bot.register_next_step_handler(message, handle_removecredit_amount)
            else:
                caption = "Username {} n'existe pas.".format(user_states[user_id]["user_msg"])
                with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
                    bot.send_photo(user_id, photo, caption)

def handle_addcredit_amount(message):
    user_id = message.chat.id
    text_message = message.text
    credit = user_states[user_id]["credit"]
    if float(credit) == 0 or float(credit) > 0:
        nvc = float(credit) + float(text_message)
        update_solde(nvc , user_states[user_id]["user_msg"])
        add_credit(user_states[user_id]["user_msg"], text_message)
    caption = "👤 User ID : {}\n".format(user_states[user_id]["user_msg"])
    caption += "💰 Solde précedent : {:.2f}\n".format(float(credit))
    caption += "💰 Solde Nouveau : {:.2f}".format(float(nvc))
    markup = types.InlineKeyboardMarkup(row_width=2)
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
    markup.add(return_button)
    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption, reply_markup=markup)
    logger.info('[{}LOG{}] [{}{}{}] [{}ADDED CREDIT{}] USER > {}{}{} - OLD CREDIT > {}{}{} - NEW CREDIT > {}{}{}'.format(fg,fw,fg,current(),fw,fg,fw,fr,user_id,fw,fr,credit,fw,fg,nvc,fw))

def handle_removecredit_amount(message):
    user_id = message.chat.id
    text_message = message.text
    credit = user_states[user_id]["credit"]
    if float(credit) == 0 or float(credit) > 0:
        nvc = float(credit) - float(text_message)
        update_solde(nvc , user_id)
        remove_credit(user_id, text_message)
    caption = "👤 User ID : {}\n".format(user_states[user_id]["user_msg"])
    caption += "💰 Solde Actuel : {:.2f}\n".format(float(credit))
    caption += "💰 Solde Nouveau : {:.2f}".format(float(nvc))
    markup = types.InlineKeyboardMarkup(row_width=2)
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
    markup.add(return_button)
    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption, reply_markup=markup)
    logger.info('[{}LOG{}] [{}{}{}] [{}REMOVED CREDIT{}] USER > {}{}{} - OLD CREDIT > {}{}{} - NEW CREDIT > {}{}{}'.format(fg,fw,fg,current(),fw,fr,fw,fr,user_id,fw,fr,float(credit),fw,fg,nvc,fw))

@bot.callback_query_handler(func=lambda call: call.data == "addcredit")
def addcredit(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    user_states[user_id] = {
        "step": 0, 
        "user_msg": None,
        "credit": None,
    }
    caption = "Quel est le ID du user ?"
    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption)
    bot.register_next_step_handler_by_chat_id(user_id, handle_addcredit_text)


@bot.callback_query_handler(func=lambda call: call.data == "removecredit")
def removecredit(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    user_states[user_id] = {
        "step": 0, 
        "user_msg": None,
        "credit": None,
    }
    caption = "Quel est le ID du user ?"
    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption)
    bot.register_next_step_handler_by_chat_id(user_id, handle_removecredit_text)

def handle_announcement_image(message):
    user_id = message.chat.id
    if user_id in messages_en_attente:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            messages_en_attente[user_id]['image'] = file_id
            caption = "✅ Image reçue. Veuillez saisir le texte de l'annonce maintenant :"
            bot.send_message(chat_id=user_id, text=caption)
            bot.register_next_step_handler(message, handle_announcement_input)
        else:
            bot.send_message(chat_id=user_id, text="❌ Ce n'est pas une image. Veuillez envoyer une image.")
            bot.register_next_step_handler(message, handle_announcement_image)
    else:
        bot.send_message(chat_id=user_id, text="❌ Aucune annonce en attente. Veuillez réessayer.")

@bot.callback_query_handler(func=lambda call: call.data == "annonce")
def send_announcement(call):
    chat_id = call.message.chat.id
    if is_admin(chat_id):
        user_id = call.from_user.id
        messages_en_attente[user_id] = {}
        bot.send_message(chat_id=chat_id, text="📢 Veuillez envoyer l'image de l'annonce ou tapez 'skip' pour sauter cette étape :")
        bot.register_next_step_handler(call.message, handle_announcement_image)
    else:
        bot.send_message(chat_id=chat_id, text="❌ Vous n'êtes pas autorisé à envoyer des annonces.")

def handle_announcement_input(message):
    user_id = message.chat.id
    if user_id in messages_en_attente:
        if 'image' not in messages_en_attente[user_id]:
            caption = "Veuillez envoyer l'image de l'annonce ou tapez 'skip' pour sauter cette étape."
            bot.send_message(chat_id=user_id, text=caption)
            bot.register_next_step_handler(message, handle_announcement_image)
        else:
            announcement_message = message.text
            messages_en_attente[user_id]['announcement_message'] = announcement_message
            markup = types.InlineKeyboardMarkup()
            confirm_button = types.InlineKeyboardButton("Confirmer ✅", callback_data="confirm_announcement")
            cancel_button = types.InlineKeyboardButton("Annuler ❌", callback_data="cancel_announcement")
            markup.add(confirm_button, cancel_button)
            bot.send_message(chat_id=user_id, text=f"📢 *Message d'annonce :*\n\n{announcement_message}\n\nVeuillez choisir une action :", parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(chat_id=user_id, text="❌ Aucune annonce en attente. Veuillez réessayer.")

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_announcement", "cancel_announcement"])
def handle_inline_button_click(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    if user_id in messages_en_attente:
        if call.data == "confirm_announcement":
            announcement_message = messages_en_attente[user_id]['announcement_message']
            image_file_id = messages_en_attente[user_id].get('image')
            send_announcement_to_all_users(announcement_message, image_file_id)
            bot.send_message(chat_id=chat_id, text="✅ L'annonce a été envoyée à tous les utilisateurs avec succès.")
            del messages_en_attente[user_id]
        elif call.data == "cancel_announcement":
            del messages_en_attente[user_id]
            bot.send_message(chat_id=chat_id, text="❌ L'envoi de l'annonce a été annulé.")

def send_announcement_to_all_users(announcement_message, image_file_id=None):
    conn = sqlite3.connect("utilisateurs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users")
    user_ids = cursor.fetchall()
    conn.close()
    for user_id in user_ids:
        try:
            if image_file_id:
                bot.send_photo(chat_id=user_id[0], photo=image_file_id, caption=announcement_message)
            else:
                bot.send_message(chat_id=user_id[0], text=announcement_message)
        except telebot.apihelper.ApiTelegramException as e:
            if "Forbidden: bot was blocked by the user" in str(e):
                logger.error(f"L'utilisateur {user_id[0]} a bloqué le bot.")
            else:
                logger.error(f"Erreur inattendue lors de l'envoi du message à {user_id[0]} : {str(e)}")

def remove_license(user_id):
    conn = sqlite3.connect("utilisateurs.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE chat_id=?", (user_id,))
    conn.commit()
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data == "removelicense")
def remove_license_callback(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    
    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption="Veuillez entrer l'ID du client à supprimer:")
    bot.register_next_step_handler_by_chat_id(user_id, handle_remove_license)

def handle_remove_license(message):
    user_id = message.chat.id
    removed_user_id = message.text
    
    remove_license(removed_user_id)
    removelicense_magnus(removed_user_id)
    
    confirmation_message = f"La licence pour l'utilisateur {removed_user_id} a été supprimée avec succès."
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
    markup.add(return_button)

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption=confirmation_message, reply_markup=markup)
    logger.info('[INFO] [{}] License removed for user {} by admin {}'.format(current(), removed_user_id, user_id))

def is_admin(user_id):
    return str(user_id) in adminlist

@bot.callback_query_handler(func=lambda call: call.data == "callsonline")
def calls_online(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id , call.message.message_id)

    caption = "il y a <b>{}</b> appels en cours.".format(get_calls_online())
    markup = types.InlineKeyboardMarkup(row_width=2)
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
    markup.add(return_button)

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption=caption, reply_markup=markup,parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "admindashboard")
def admin_starter(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)

    uuuu = bot.get_chat_member(chat_id=user_id, user_id=user_id).user
    username = uuuu.username

    markup = types.InlineKeyboardMarkup(row_width=2)
    add = types.InlineKeyboardButton("➕ Ajouter crédit", callback_data="addcredit")
    remove = types.InlineKeyboardButton("➖ Enlever crédit", callback_data="removecredit")
    callsonline = types.InlineKeyboardButton("☎️ Appels en cours", callback_data="callsonline")
    removelicense = types.InlineKeyboardButton("🚫 Enlever licence", callback_data="removelicense")
    annonce = types.InlineKeyboardButton("📢 Annonce", callback_data="annonce")
    fournisseur = types.InlineKeyboardButton("🤝 Fournisseur", callback_data="fournisseur")
    return_button = types.InlineKeyboardButton("🔙 Retour", callback_data="return")
    markup.add(add, remove, callsonline, removelicense, annonce, fournisseur, return_button)
    caption = """ <b>🚀 Test_BotSpoofer 🚀</b>

<b>🚀 Panel Admin 🚀</b>

Bienvenue Admin , {}""".format(username)

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption=caption, reply_markup=markup, parse_mode='HTML')

def main_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    passwordsip = types.InlineKeyboardButton("🔒 Les accès SIP", callback_data="passwordsip")
    callerID = types.InlineKeyboardButton("⚙️ Changer le Caller ID", callback_data="callerID")
    smsspoof = types.InlineKeyboardButton("💻 Spoofer avec licence", url="https://t.me/Test_BotSenderSMSBOT")
    support = types.InlineKeyboardButton("🥂 Spoofer VIP", url="https://t.me/Test_BotSenderIDBOT")
    accountsettings = types.InlineKeyboardButton("👤 Mon compte", callback_data="accountsettings")

    caption = f""" <b>🚀 Bienvenue sur Test_BotSpoofer ® </b>

<b>⚠️ <strong>Notre priorité ? votre satisfaction !!!</strong></b>

<b>☎️ Tous les caller id sans restriction.</b>

<b><i>💻 <u> Avec licence 100€/ mois 0,29€/ minute. 

🖥 Sans licence 0,45€/ minute.

🥂 Licence VIP 1000€/ mois 0,25€/ minute ( route privée ).</u></i></b>

<b>⌨️ DTMF illimité avec ou sans licence ✅</b>

<b>📲 Le spoofer est : ACTIF ✅</b>
"""

    if is_admin(user_id):
        admin_dashboard = types.InlineKeyboardButton("🚀 Admin Dashboard", callback_data="admindashboard")
        markup.add(passwordsip, callerID, smsspoof, support, accountsettings, admin_dashboard)
    else:
        markup.add(passwordsip, callerID, smsspoof, support, accountsettings)

    with open("photo_2023-11-05_00-09-39.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption=caption, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(commands=["start"])
def starter(message):
    user_id = message.chat.id
    logger.info('[{}LOG{}] [{}{}{}] {}{}{} Started the bot.'.format(fg,fw,fg,current(),fw,fr,user_id,fw))
    user_ids = get_all_chatid()
    found = 0
    for id in user_ids:
        if str(id) == str(user_id):
            found += 1
            break
    if not found:
        insert_user(user_id)

    main_menu(user_id)

if __name__ == "__main__":
    logo()
    print('\n\n[{}INF{}] Bot Token : {}{}{}\n[{}INF{}] Subscription Price : {}{}€{}\n\n[{}INF{}] Starting Bot...'.format(fg,fw,fr,tokenbot,fw,fg,fw,fr,sub_price,fw,fg,fw))
    # print('[INF] starting webhook...')
    

    bot.skip_pending = True
    while True:
        try:
            print('[{}INF{}] Bot Started Successfully!'.format(fg,fw))
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Une erreur s'est produite : {str(e)}")
            continue
