# AI员工政策顾问 🤖

基于星辰科技员工手册 V4.0 的 HR 智能问答系统，帮助员工快速查询公司 HR 政策。

## 功能

- 自然语言提问，AI 基于知识库精确回答
- 每条回答注明政策依据章节
- 知识库外问题自动提示联系 HR，不编造答案
- 11 个政策分类，34 条结构化知识

## 技术栈

- **后端**: Python / Flask + DeepSeek API
- **前端**: 纯 HTML/CSS/JS（无框架）
- **部署**: Nginx + systemd，HTTPS

## 在线地址

https://aicodingdemo.arielzhao.top

## 本地运行

```bash
pip install flask
python app.py
```

访问 http://localhost:5000
