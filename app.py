#!/usr/bin/env python3
"""
AI员工政策顾问 - 后端服务 V2.0
使用DeepSeek API进行语义理解，以结构化知识库为权威依据
"""

import json
import os
import re
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, send_from_directory
from flask import Response
import time

app = Flask(__name__, static_folder="templates")

# ── 配置 ──────────────────────────────────────────────
DEEPSEEK_API_KEY = "sk-f0cf349ba8cb4aac84a76a6ab5963a77"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

# ── 加载知识库 ────────────────────────────────────────
HANDBOOK_PATH = os.path.join(os.path.dirname(__file__), "handbook.json")
with open(HANDBOOK_PATH, "r", encoding="utf-8") as f:
    KNOWLEDGE_BASE = json.load(f)

# 构建用于系统提示的知识库文本
def build_knowledge_text():
    lines = []
    for item in KNOWLEDGE_BASE:
        lines.append(f"【政策依据：{item['policy']}】")
        lines.append(f"问：{item['question']}")
        lines.append(f"答：{item['answer']}")
        lines.append("")
    return "\n".join(lines)

KNOWLEDGE_TEXT = build_knowledge_text()

SYSTEM_PROMPT = f"""你是星辰科技（上海）有限公司的AI员工政策顾问，专门帮助员工查询公司HR政策。

## 核心规则（必须严格遵守）

1. **只能根据以下知识库内容回答**，不得凭借自身知识编造任何政策内容
2. **如果知识库中没有明确依据**，必须回复：「该问题暂未收录，请联系HR进一步确认（hr@starrytech.com / 分机8002）」
3. **回答时必须注明政策依据**，格式为：「依据：[政策章节]」
4. **回答要简洁准确**，直接给出员工需要的信息，避免冗余解释
5. **数字和规则要精确**，如天数、金额、比例等不得有误

## 知识库内容

{KNOWLEDGE_TEXT}

## 回答格式

回答正文（直接回答问题，重要数字可加粗）

> 依据：[具体章节，如"第五章 5.1 工作时间"]

## 非HR政策问题的处理

如果问题与公司HR政策完全无关（如写诗、天气、个人请求等），必须严格按以下格式回复，不得添加任何其他内容：

该问题暂未收录，请联系HR进一步确认（hr@starrytech.com / 分机8002）
"""


def call_deepseek(question: str) -> dict:
    """调用DeepSeek API获取回答"""
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
        "max_tokens": 600,
        "temperature": 0.1,  # 低温度确保精确性
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        DEEPSEEK_BASE_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"].strip()

            # 判断是否找到答案
            # found=True 的充分条件：AI 明确引用了知识库依据
            # 以下任意一种情况视为未找到/拒答
            has_policy_ref = bool(re.search(r'依据[：:]', content))
            not_found = (
                "暂未收录" in content
                or not has_policy_ref  # 没有引用依据行，说明 AI 没能从知识库作答
            )

            # 提取依据
            policy_ref = ""
            match = re.search(r'依据[：:]\s*(.+?)(?:\n|$)', content)
            if match:
                policy_ref = match.group(1).strip()

            return {
                "found": not not_found,
                "answer": content,
                "policy": policy_ref,
                "model": MODEL,
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API错误 {e.code}: {error_body[:200]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络错误: {e.reason}")


# ── API路由 ──────────────────────────────────────────

@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"found": False, "answer": "请输入您的问题。", "policy": ""}), 400

    if len(question) > 500:
        return jsonify({"found": False, "answer": "问题过长，请精简后再提问。", "policy": ""}), 400

    try:
        result = call_deepseek(question)
        return jsonify(result)
    except RuntimeError as e:
        return jsonify({
            "found": False,
            "answer": f"系统暂时无法处理请求，请稍后再试。",
            "policy": "",
            "error": str(e)
        }), 503
    except Exception as e:
        return jsonify({
            "found": False,
            "answer": "系统内部错误，请联系IT支持。",
            "policy": "",
            "error": str(e)
        }), 500


@app.route("/api/categories", methods=["GET"])
def categories():
    cats = sorted(set(item["category"] for item in KNOWLEDGE_BASE))
    return jsonify(cats)


@app.route("/api/knowledge", methods=["GET"])
def knowledge():
    summary = [{"id": i["id"], "category": i["category"], "question": i["question"], "policy": i["policy"]}
               for i in KNOWLEDGE_BASE]
    return jsonify(summary)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "knowledge_count": len(KNOWLEDGE_BASE), "model": MODEL})


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 AI员工政策顾问 V2.0 启动中...")
    print(f"📚 已加载 {len(KNOWLEDGE_BASE)} 条HR政策知识")
    print(f"🤖 AI模型: {MODEL}")
    print(f"🌐 访问地址: http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
