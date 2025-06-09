from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from mysql.connector import Error
import hashlib
from datetime import datetime
import os
from functools import wraps
from pymongo import MongoClient
from zhipuai import ZhipuAI

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  
    'database': 'chatdata'
}

# MongoDB 连接配置
MONGO_CONFIG = {
    'host': 'localhost',
    'port': 27017,
    'db_name': 'chatdata'
}

# 数据库连接函数
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"数据库连接错误: {e}")
        return None

# MongoDB 连接函数
def get_mongo_connection():
    try:
        client = MongoClient(MONGO_CONFIG['host'], MONGO_CONFIG['port'])
        db = client[MONGO_CONFIG['db_name']]
        return db
    except Exception as e:
        print(f"MongoDB 连接错误: {e}")
        return None

# 登录检查装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # 密码加密
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # 检查邮箱是否已存在
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash('该邮箱已被注册', 'error')
                    return render_template('register.html')
                
                # 插入新用户
                cursor.execute(
                    "INSERT INTO users (u_name, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed_password)
                )
                conn.commit()
                
                flash('注册成功，请登录', 'success')
                return redirect(url_for('login'))
            except Error as e:
                flash(f'注册失败: {e}', 'error')
            finally:
                cursor.close()
                conn.close()
        
    return render_template('register.html')

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        print(hashed_password)
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                
                # 验证用户
                cursor.execute(
                    "SELECT * FROM users WHERE email = %s AND password = %s",
                    (email, hashed_password)   
                )
                user = cursor.fetchone()
                print("查到的用户:", user)
                
                if user:
                    session['user_id'] = user['uid']
                    session['username'] = user['u_name']
                    flash('登录成功', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('邮箱或密码错误', 'error')
            except Error as e:
                flash(f"登录失败: {e}", 'error')
            finally:
                cursor.close()
                conn.close()
        
    return render_template('login.html')

# 登出路由
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('您已成功登出', 'success')
    return redirect(url_for('index'))

# 用户面板路由
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # 获取用户的会话
            cursor.execute(
                """
                SELECT s.*, m.m_name 
                FROM sessions s
                JOIN models m ON s.m_id = m.m_id
                WHERE s.uid = %s
                ORDER BY s.start_t DESC
                """,
                (session['user_id'],)
            )
            sessions_list = cursor.fetchall()
            
            return render_template('dashboard.html', sessions=sessions_list)
        finally:
            cursor.close()
            conn.close()
    
    return render_template('dashboard.html', sessions=[])

# 创建新会话
@app.route('/create_session', methods=['POST'])
@login_required
def create_session():
    model_id = request.form['model_id']
    model_name = request.form['model_name']
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # 创建新会话
            cursor.execute(
                """
                INSERT INTO sessions (model_n, start_t, uid, m_id)
                VALUES (%s, %s, %s, %s)
                """,
                (model_name, datetime.now(), session['user_id'], model_id)
            )
            conn.commit()
            
            # 获取新创建的会话ID
            session_id = cursor.lastrowid
            
            flash('会话创建成功', 'success')
            return redirect(url_for('chat', session_id=session_id))
        finally:
            cursor.close()
            conn.close()
    
    flash('会话创建失败', 'error')
    return redirect(url_for('dashboard'))

# 聊天页面
@app.route('/chat/<int:session_id>')
@login_required
def chat(session_id):
    conn = get_db_connection()
    mongo_db = get_mongo_connection()

    if conn and mongo_db is not None:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # 验证会话所有权
            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = %s AND uid = %s",
                (session_id, session['user_id'])
            )
            session_data = cursor.fetchone()
            
            if not session_data:
                flash('无权访问该会话', 'error')
                return redirect(url_for('dashboard'))
            
            # 从MongoDB获取会话中的消息
            messages_collection = mongo_db.messages
            messages_cursor = messages_collection.find({'session_id': session_id}).sort('time', 1)
            
            messages = []
            for msg in messages_cursor:
                msg['_id'] = str(msg['_id']) # 将ObjectId转换为字符串以备后用
                if isinstance(msg.get('time'), datetime):
                    msg['time'] = msg['time'].strftime('%Y-%m-%d %H:%M:%S')
                messages.append(msg)
            
            # 获取模型信息
            cursor.execute(
                "SELECT * FROM models WHERE m_id = %s",
                (session_data['m_id'],)
            )
            model = cursor.fetchone()
            
            return render_template('chat.html', 
                                  session_data=session_data, 
                                  messages=messages, 
                                  model=model)
        finally:
            cursor.close()
            conn.close()
    
    flash('无法加载会话', 'error')
    return redirect(url_for('dashboard'))

# 发送消息API
@app.route('/api/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    user_input = data.get('message')
    session_id = data.get('session_id')
    
    if not user_input or not session_id:
        return jsonify({'error': '消息或会话ID不能为空'}), 400
    
    conn = get_db_connection()
    mongo_db = get_mongo_connection()

    if conn and mongo_db is not None:
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            # 验证会话所有权
            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = %s AND uid = %s",
                (session_id, session['user_id'])
            )
            session_data = cursor.fetchone()
            
            if not session_data:
                return jsonify({'error': '无权访问该会话'}), 403
            
            # 根据会话m_id获取模型信息，逻辑是先新建一个会话，再读取会话信息
            cursor.execute("SELECT m_name FROM models WHERE m_id = %s", (session_data['m_id'],))
            model_data = cursor.fetchone()
            if not model_data:
                return jsonify({'error': '找不到会话关联的模型'}), 404
            
            target_model_name = model_data['m_name']

            # --- API 调用和日志记录 ---
            ai_response_content = None
            log_status = 'failure'
            error_msg = None
            usage_data = {}
            request_time = datetime.now()

            try:
                client = ZhipuAI(api_key="")  # 请填写您自己的APIKey
                response = client.chat.completions.create(
                    model=target_model_name,  # 动态使用从数据库获取的模型名称
                    messages=[
                        {"role": "system", "content": "你是一个乐于回答各种问题的小助手，你的任务是提供专业、准确、有洞察力的建议。"},
                        {"role": "user", "content": user_input},
                    ],
                )
                ai_response_content = response.choices[0].message.content
                # 检查是否存在 usage 字段
                if hasattr(response, 'usage'):
                    usage_data = response.usage
                log_status = 'success'

            except Exception as e:
                error_msg = str(e)
                ai_response_content = "抱歉，调用AI服务时出现错误，请稍后再试。"
            
            response_time = datetime.now()
            time_taken = int((response_time - request_time).total_seconds() * 1000)

            # 记录API日志到MySQL
            log_cursor = None
            try:
                log_cursor = conn.cursor()
                log_cursor.execute(
                    """
                    INSERT INTO api_logs (session_id, m_id, request_time, response_time, time_taken_ms, 
                                          prompt_tokens, completion_tokens, total_tokens, status, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (session_id, session_data['m_id'], request_time, response_time, time_taken,
                     getattr(usage_data, 'prompt_tokens', None), 
                     getattr(usage_data, 'completion_tokens', None), 
                     getattr(usage_data, 'total_tokens', None),
                     log_status, error_msg)
                )
                conn.commit()
            except Error as e:
                # 即使日志记录失败，也不应中断主流程
                print(f"记录API日志失败: {e}")
            finally:
                if log_cursor:
                    log_cursor.close()

            # 将消息存入MongoDB
            message_doc = {
                'u_input': user_input,
                'ai_respond': ai_response_content,
                'time': response_time,
                'session_id': session_id,
                'm_id': session_data['m_id']
            }
            mongo_db.messages.insert_one(message_doc)
            
            if log_status == 'failure':
                return jsonify({'error': ai_response_content, 'status': 'failure'}), 500

            return jsonify({
                'status': 'success',
                'message': ai_response_content,
                'timestamp': response_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return jsonify({'error': '服务器错误'}), 500

# 获取可用模型API
@app.route('/api/models', methods=['GET'])
@login_required
def get_models():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM models")
            models = cursor.fetchall()
            
            return jsonify({'models': models})
        finally:
            cursor.close()
            conn.close()
    
    return jsonify({'error': '服务器错误'}), 500

# 获取会话消息API
@app.route('/api/messages/<int:session_id>', methods=['GET'])
@login_required
def get_messages(session_id):
    conn = get_db_connection()
    mongo_db = get_mongo_connection()
    if conn and mongo_db is not None:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # 验证会话所有权
            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = %s AND uid = %s",
                (session_id, session['user_id'])
            )
            if not cursor.fetchone():
                return jsonify({'error': '无权访问该会话'}), 403
            
            # 从MongoDB获取会话中的消息
            messages_collection = mongo_db.messages
            messages_cursor = messages_collection.find({'session_id': session_id}).sort('time', 1)
            
            messages = []
            for msg in messages_cursor:
                msg['_id'] = str(msg['_id']) # ObjectId -> str
                msg['time'] = msg['time'].strftime('%Y-%m-%d %H:%M:%S')
                messages.append(msg)
            
            return jsonify({'messages': messages})
        finally:
            cursor.close()
            conn.close()
    
    return jsonify({'error': '服务器错误'}), 500


if __name__ == '__main__':
    app.run(debug=True)
