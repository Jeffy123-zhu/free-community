# 社区贡献追踪系统 (Community Contribution Tracking System)

## 功能概述

- ✅ 事件档案管理 (Event Profile)
- ✅ 组织信息管理
- ✅ 事件类型管理
- ✅ 贡献记录 (志愿工时、现金捐赠、物资捐赠)
- ✅ 季度报告生成
- ✅ 数据统计仪表板

## 快速启动

### 1. 安装依赖

```bash
pip install flask
```

### 2. 运行程序

```bash
cd community_system
python app.py
```

### 3. 访问系统

打开浏览器访问: http://localhost:5000

## 数据库结构

- `event_types` - 事件类型查询表
- `organizations` - 组织信息表
- `event_profiles` - 事件档案主表
- `contributions` - 贡献记录明细表
- `quarterly_summaries` - 季度汇总表

## 使用流程

1. 首先添加组织信息 (可选)
2. 添加新事件，填写基本信息
3. 在事件编辑页面添加贡献记录
4. 通过季度报告查看统计数据

## 文件结构

```
community_system/
├── app.py              # Flask主应用
├── database.py         # 数据库模型
├── community.db        # SQLite数据库 (运行后自动生成)
├── templates/          # HTML模板
│   ├── base.html
│   ├── index.html
│   ├── add_event.html
│   ├── edit_event.html
│   ├── event_list.html
│   ├── view_event.html
│   ├── organizations.html
│   ├── event_types.html
│   ├── reports.html
│   └── report_result.html
└── README.md
```
