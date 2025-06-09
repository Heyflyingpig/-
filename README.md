# 广东工业大学数据库课程设计——aichatbox

这是一个基于 Flask、MySQL 和 MongoDB 构建的 Web 应用，用户可以与智谱AI提供的多种大语言模型进行交互。应用支持用户注册、登录、会话管理，并将聊天记录和API调用日志持久化存储。

## 主要功能

*   **用户认证**: 提供用户注册和登录功能。
*   **会话管理**: 用户可以创建、查看和管理与不同AI模型的聊天会话。
*   **实时聊天**: 在聊天页面与AI进行实时问答交互。
*   **模型切换**: 支持在创建会话时选择不同的AI模型。
*   **聊天记录存储**: 使用 MongoDB 存储所有聊天记录，方便回溯。
*   **API日志**: 使用 MySQL 记录对AI模型的每次API调用详情，包括token消耗、响应时间等。

## 技术栈

*   **后端**: Flask
*   **数据库**:
    *   MySQL: 用于存储用户信息、会话、模型和API日志。
    *   MongoDB: 用于存储聊天消息。
*   **AI服务**: [智谱AI (ZhipuAI)](https://www.zhipuai.cn/)
*   **前端**: HTML, CSS, JavaScript

## 项目结构

```
.
├── static/
│   ├── css/         # 样式文件
│   ├── js/          # 脚本文件
│   └── chatdata.html # (可能用于数据可视化)
├── templates/
│   ├── base.html      # 基础模板
│   ├── chat.html      # 聊天页面
│   ├── dashboard.html # 用户仪表盘
│   ├── index.html     # 首页
│   ├── login.html     # 登录页面
│   └── register.html  # 注册页面
├── chatdata.py        # Flask 应用主文件
├── requirements.txt   # Python 依赖
└── README.md          # 本文档
```

## 安装与配置

### 1. 先决条件

*   Python 3.x
*   MySQL Server
*   MongoDB Server

### 2. 克隆项目

```bash
git clone <your-repository-url>
cd aichatbox作业
```

### 3. 创建虚拟环境并安装依赖

建议使用虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # on Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 4. 配置数据库

#### MySQL

1.  登录到您的 MySQL 服务器并创建一个新的数据库。

    ```sql
    CREATE DATABASE chatdata;
    ```

2.  执行以下SQL脚本来创建所需的表结构。

    ```sql
    USE chatdata;

        -- 用户表
    CREATE TABLE users (
        uid INT PRIMARY KEY AUTO_INCREMENT,
        u_name VARCHAR(50) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    );

    -- 模型表
    CREATE TABLE models (
        m_id INT PRIMARY KEY AUTO_INCREMENT,
        m_name VARCHAR(50) NOT NULL,
        version VARCHAR(20) NOT NULL,
        describ TEXT
    );

    -- 会话表
    CREATE TABLE sessions (
        session_id INT PRIMARY KEY AUTO_INCREMENT,
        model_n VARCHAR(50) NOT NULL,
        start_t DATETIME NOT NULL,
        uid INT NOT NULL,
        m_id INT NOT NULL,
        FOREIGN KEY (uid) REFERENCES users(uid),
        FOREIGN KEY (m_id) REFERENCES models(m_id)
    );



    -- API日志表
    CREATE TABLE api_logs (
        log_id INT AUTO_INCREMENT PRIMARY KEY,
        session_id INT,
        m_id INT,
        request_time DATETIME,
        response_time DATETIME,
        time_taken_ms INT,
        prompt_tokens INT,
        completion_tokens INT,
        total_tokens INT,
        status VARCHAR(20) NOT NULL,
        error_message TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id),
        FOREIGN KEY (m_id) REFERENCES models(m_id)
    );
        -- 用户数据
    INSERT INTO users (u_name, email, password) VALUES 
    ('张三', 'zhangsan@example.com', 'password123'),
    ('李四', 'lisi@example.com', 'password456'),
    ('王五', 'wangwu@example.com', 'password789');

    INSERT INTO models (m_name, version, describ) VALUES 
    ('GLM-Z1-Flash', '1.0', 'GLM推理模型'),
    ('GLM-4-Flash', '1.0', 'GLM快速模型'),
    ('GLM-4-Flash-250414', '1.0', 'GLM长输出模型');

    ```

#### MongoDB

1.  确保您的 MongoDB 服务正在运行。
2.  应用会自动在 MongoDB 中创建名为 `chatdata` 的数据库和名为 `messages` 的集合。

### 5. 配置应用

打开 `chatdata.py` 文件并更新以下配置：

*   **MySQL 数据库连接 (`DB_CONFIG`)**:
    ```python
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'your_mysql_user',
        'password': 'your_mysql_password',
        'database': 'chatdata'
    }
    ```

*   **MongoDB 连接 (`MONGO_CONFIG`)**:
    ```python
    MONGO_CONFIG = {
        'host': 'localhost',
        'port': 27017,
        'db_name': 'chatdata'
    }
    ```

*   **ZhipuAI API Key**:
    在 `send_message` 函数中，找到以下行并替换为您自己的 API Key。
    ```python
    client = ZhipuAI(api_key="YOUR_ZHIPUAI_API_KEY") 
    ```
    在 `chatdata.py` 的第 305 行附近。

## 运行应用

完成上述配置后，在项目根目录下运行以下命令来启动 Flask 应用：

```bash
python chatdata.py
```

应用将默认在 `http://127.0.0.1:5000` 上运行。

## 使用方法

1.  打开浏览器并访问 `http://127.0.0.1:5000`。
2.  点击 "注册" 创建一个新账户。
3.  使用您的账户信息 "登录"。
4.  登录后，您将进入仪表盘页面，这里会显示您过去的聊天会话。
5.  在仪表盘上，选择一个AI模型并点击 "创建新会话" 来开始一个新的聊天。
6.  在聊天页面，输入您的问题并发送，AI 将会回复您。 