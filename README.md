# Travel Sharing App (旅行信息分享应用)

本项目是一个基于前后端分离架构的旅行信息分享平台，旨在为用户提供旅行前的攻略制定、旅行中的路线管理以及旅行后的资源分享与社交互动功能。

## 📋 功能列表与要求

本项目实现了以下核心需求：

1.  **旅行前**：攻略收集、筛选、队伍组建（添加成员）。
2.  **旅行中**：路线云备份、队伍管理。
3.  **旅行后**：资源分享、浏览动态、好友互动。

## ✨ 项目特色

*   **前后端分离**：前端采用 React.js，后端采用 Python Flask。
*   **DDD 领域驱动设计**：后端代码结构清晰，划分为 Auth（认证）、Social（社交）、Travel（旅行）三个核心领域。
*   **现代化 UI**：采用 Dark Glassmorphism（深色玻璃拟态）设计风格，提供沉浸式的用户体验。
*   **功能丰富**：
    *   用户注册与登录
    *   旅行计划管理（创建行程、添加活动、邀请成员）
    *   社交广场（发布动态、点赞、评论）
    *   即时通讯（好友聊天）

## 🛠️ 技术栈

*   **前端**：React, Vite, CSS Modules
*   **后端**：Python, Flask, SQLAlchemy
*   **数据库**：MySQL
*   **其他**：Axios, React Router

## 📂 项目结构

### 后端结构 (Backend)

后端采用领域驱动设计 (DDD) 架构：

```text
backend/src
├── app.py                  # 应用入口
├── app_auth/               # 认证领域 (用户管理)
│   ├── domain/             # 领域层 (实体, 领域服务)
│   ├── infrastructure/     # 基础设施层 (DAO, 仓储实现)
│   ├── services/           # 应用服务层
│   └── view/               # 接口层 (API Views)
├── app_social/             # 社交领域 (帖子, 评论, 聊天)
│   ├── domain/
│   ├── infrastructure/
│   ├── services/
│   └── view/
├── app_travel/             # 旅行领域 (行程, 活动, 成员)
│   ├── domain/
│   ├── infrastructure/
│   ├── services/
│   └── view/
├── shared/                 # 共享模块 (数据库核心, 事件总线)
└── static/                 # 静态文件 (上传的图片等)
```

### 前端结构 (Frontend)

前端基于 React + Vite 构建：

```text
frontend/src
├── api/                    # API 接口封装 (auth, social, travel)
├── assets/                 # 静态资源
├── components/             # 公共组件 (Button, Card, Input, Layout...)
├── context/                # 全局状态 (AuthContext)
├── pages/                  # 页面组件
│   ├── auth/               # 认证相关页面 (Login, Register, Profile)
│   ├── social/             # 社交相关页面 (Feed, Chat, PostDetail)
│   └── travel/             # 旅行相关页面 (MyTrips, TripDetail...)
├── styles/                 # 全局样式 (theme.css)
├── App.jsx                 # 根组件 (路由配置)
└── main.jsx                # 入口文件
```

## 🚀 快速开始 (Getting Started)

### 1. 环境准备

*   Node.js & npm
*   Python 3.8+
*   MySQL Database

### 2. 启动后端服务器

确保 MySQL 服务已启动，并配置好数据库连接。

```bash
# 进入后端目录
cd travel_sharing_app_v0/backend

# 激活虚拟环境 (Windows)
# 如果没有创建虚拟环境，请先创建: python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动应用
.venv\Scripts\python.exe src/app.py
```

### 3. 启动前端服务器

```bash
# 进入前端目录
cd travel_sharing_app_v0/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问本地地址：`http://localhost:5173` (默认 Vite 端口)


