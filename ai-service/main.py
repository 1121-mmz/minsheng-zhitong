import os
import json
import time
from typing import TypedDict
from fastapi import FastAPI
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding
from langgraph.graph import StateGraph, START, END

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key 从环境变量读取
API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not API_KEY:
    print("[警告] 未设置 DEEPSEEK_API_KEY，AI 分诊将走兜底逻辑。")

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com") if API_KEY else None

# 向量库配置
QDRANT_HOST = os.getenv("QDRANT_HOST")  # docker 里为 qdrant；本地留空则用内存模式
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
COLLECTION_REG = "dept_regulations"
COLLECTION_HISTORY = "history_orders"
TOPK = 3


class TriageRequest(BaseModel):
    text: str
    history: list = Field(default_factory=list)


# 本地知识库（示例数据，正式使用时替换为完整的部门权责清单）
knowledge_base = [
    {
        "dept": "城市管理局",
        "text": "市政设施维护管理：下水道堵塞、污水外溢、井盖缺失损坏、道路破损坑洼、违章建筑、占道经营、乱倒垃圾等城市管理问题",
        "keywords": ["下水道", "污水", "井盖", "道路", "违建", "占道", "垃圾", "市政"],
        "basis": "《城市管理执法权责清单》第12条：负责市政排水管网及附属设施的维护管理。",
    },
    {
        "dept": "生态环境局",
        "text": "环境污染防治监管：工业噪音、餐饮油烟、空气污染、水污染、工地扬尘、夜间施工扰民、异味排放等环境问题",
        "keywords": ["噪音", "油烟", "污染", "施工扰民", "扬尘", "异味", "环境"],
        "basis": "《环境保护法》第42条：负责环境污染防治的监督管理。",
    },
    {
        "dept": "市场监督管理局",
        "text": "市场经营秩序监管：食品安全、过期变质食品、乱涨价、价格欺诈、假冒伪劣商品、缺斤少两、消费维权投诉",
        "keywords": ["食品", "过期", "超市", "物价", "欺诈", "假冒", "消费", "涨价"],
        "basis": "《食品安全法》第5条：负责食品生产经营活动的监督管理。",
    },
    {
        "dept": "住房和城乡建设局",
        "text": "房屋与物业相关问题：房屋质量、墙体开裂漏水、物业纠纷、电梯故障、老旧小区改造、公租房廉租房申请",
        "keywords": ["房屋", "漏水", "物业", "电梯", "小区改造", "公租房", "质量"],
        "basis": "《物业管理条例》及住建部门职责：负责房屋质量与物业服务的监督管理。",
    },
    {
        "dept": "卫生健康委员会",
        "text": "医疗卫生服务监管：医院就诊、医疗纠纷、医生执业、医保报销、疫苗接种、公共卫生、疫情防控、卫生许可证",
        "keywords": ["医院", "医疗", "就诊", "医保", "疫苗", "卫生", "疫情", "挂号"],
        "basis": "《基本医疗卫生与健康促进法》：负责医疗卫生服务的监督管理。",
    },
    {
        "dept": "教育局",
        "text": "教育相关诉求：入学转学、学区划分、学校收费、课外补课、校园安全、教师师德、培训机构退费",
        "keywords": ["学校", "入学", "学区", "补课", "教育", "老师", "培训", "学费"],
        "basis": "《义务教育法》：负责各级各类教育的统筹管理。",
    },
    {
        "dept": "人力资源和社会保障局",
        "text": "劳动权益保障：拖欠工资、劳动仲裁、劳动合同纠纷、社保缴纳、养老金、工伤认定、失业金申领、就业",
        "keywords": ["欠薪", "工资", "劳动", "仲裁", "社保", "养老", "工伤", "失业", "合同"],
        "basis": "《劳动合同法》及人社部门职责：负责劳动用工与社会保险的监督管理。",
    },
    {
        "dept": "民政局",
        "text": "社会救助与民政事务：低保申请、临时救助、养老服务、残疾人补贴、婚姻登记、孤儿收养、社区管理",
        "keywords": ["低保", "养老", "救助", "残疾", "婚姻", "民政", "补贴"],
        "basis": "《社会救助暂行办法》：负责最低生活保障等社会救助工作。",
    },
    {
        "dept": "交通运输局",
        "text": "交通出行问题：公交线路调整、出租车拒载、共享单车乱停放、交通拥堵、停车难、道路标线信号灯、网约车",
        "keywords": ["公交", "出租", "共享单车", "交通", "拥堵", "停车", "网约车", "信号灯"],
        "basis": "《道路交通安全法》及交通部门职责：负责城市公共交通与道路运输管理。",
    },
    {
        "dept": "水务局",
        "text": "供排水与燃气问题：停水、水压不足、水管爆裂、水质问题、燃气供应中断、燃气管道安全",
        "keywords": ["停水", "水压", "水管", "水质", "燃气", "停气"],
        "basis": "《城市供水条例》：负责城市供水、排水与燃气的行业管理。",
    },
]

# 向量检索组件（懒加载，失败时回退到关键词匹配）
embedding_model = None
_model_failed = False
qdrant = None
_index_ready = False


def _ensure_model():
    global embedding_model, _model_failed
    if embedding_model is None and not _model_failed:
        try:
            embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)
        except Exception as e:
            _model_failed = True
            print(f"[RAG] embedding 模型加载失败（请检查网络/镜像）: {e}")
    return embedding_model


def _ensure_indexed():
    global qdrant, _index_ready
    if _index_ready:
        return True
    model = _ensure_model()
    if model is None:
        return False
    try:
        if qdrant is None:
            qdrant = (
                QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
                if QDRANT_HOST
                else QdrantClient(":memory:")
            )
        texts = [item["text"] for item in knowledge_base]
        vectors = list(model.embed(texts))
        dim = len(vectors[0])
        qdrant.recreate_collection(
            COLLECTION_REG,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        points = [
            PointStruct(
                id=i,
                vector=[float(x) for x in vec],
                payload={"dept": knowledge_base[i]["dept"], "basis": knowledge_base[i]["basis"]},
            )
            for i, vec in enumerate(vectors)
        ]
        qdrant.upsert(COLLECTION_REG, points=points)
        if not qdrant.collection_exists(COLLECTION_HISTORY):
            qdrant.create_collection(
                COLLECTION_HISTORY,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
        _index_ready = True
        print(f"[RAG] 向量库就绪：权责清单 {len(points)} 条，维度 {dim}")
        return True
    except Exception as e:
        print(f"[RAG] 向量库索引失败（稍后重试）: {e}")
        qdrant = None
        return False


def _vector_search(collection: str, query: str, topk: int = TOPK):
    if not _ensure_indexed():
        return []
    query_vec = list(embedding_model.embed([query]))[0]
    res = qdrant.query_points(
        collection,
        query=[float(x) for x in query_vec],
        limit=topk,
    )
    return getattr(res, "points", res) or []


def search_regulation(query: str) -> str:
    """工具：在部门权责清单中检索主办部门和法律依据"""
    hits = _vector_search(COLLECTION_REG, query, TOPK)
    if not hits:
        for item in knowledge_base:
            for kw in item["keywords"]:
                if kw in query:
                    return f"主办部门：{item['dept']}，派单依据：{item['basis']}"
        return "未检索到相关的权责清单条目。"
    return "；".join(
        f"主办部门：{h.payload['dept']}，派单依据：{h.payload['basis']}" for h in hits
    )


def lookup_history(query: str) -> str:
    """工具：检索历史相似工单的处理结果作为参考"""
    if not _ensure_indexed():
        return "历史检索暂不可用。"
    hits = _vector_search(COLLECTION_HISTORY, query, TOPK)
    if not hits:
        return "暂无相似历史工单。"
    return "；".join(
        f"相似工单：{h.payload.get('summary', '')}（主办：{h.payload.get('dept', '')}）"
        for h in hits
    )


def remember_history(text: str, result: dict):
    """把本次分诊结果写入历史工单向量库，供下次相似诉求参考"""
    if not _ensure_indexed():
        return
    try:
        summary = (result or {}).get("summary") or text[:20]
        dept = (result or {}).get("mainDept") or "未知"
        vec = list(embedding_model.embed([text]))[0]
        qdrant.upsert(
            COLLECTION_HISTORY,
            points=[
                PointStruct(
                    id=int(time.time() * 1000),
                    vector=[float(x) for x in vec],
                    payload={"summary": summary, "dept": dept, "text": text},
                )
            ],
        )
    except Exception as e:
        print(f"[Agent] 历史记录写入失败: {e}")


# 检索 Agent 的工具定义（OpenAI function calling 格式）
RETRIEVAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_regulation",
            "description": "在部门权责清单中检索与诉求相关的法规依据和主办部门",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "用于检索的诉求关键词或改写后的检索语句"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_history",
            "description": "检索历史相似工单的处理结果，作为分诊参考",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "用于检索历史工单的诉求描述"}
                },
                "required": ["query"],
            },
        },
    },
]


def _extract_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass
    return None


def _chat_json(prompt: str, system: str = None):
    """一次 JSON 模式的 LLM 调用，返回 dict（失败返回 None）"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},
        timeout=20,
    )
    return _extract_json(resp.choices[0].message.content or "")


def run_tool(name: str, arguments: dict) -> str:
    q = (arguments or {}).get("query", "")
    if name == "search_regulation":
        return search_regulation(q)
    if name == "lookup_history":
        return lookup_history(q)
    return "未知工具"


# ---------- LangGraph 多 Agent 状态与节点 ----------

class TriageState(TypedDict, total=False):
    user_input: str
    history: list
    need_clarify: bool
    clarify_question: str
    intake: dict
    retrieval: str
    final_result: dict


INTAKE_SYSTEM = "你是政务热线的受理 Agent，负责理解市民诉求、抽取关键要素，并判断信息是否足够。"


def intake_node(state: TriageState):
    history = state.get("history") or []
    user_input = state.get("user_input", "")
    lines = []
    for m in history:
        role = "市民" if m.get("role") == "user" else "系统"
        lines.append(f"{role}：{m.get('content', '')}")
    lines.append(f"市民：{user_input}")
    convo = "\n".join(lines)

    prompt = f"""已知对话：
{convo}

你是受理 Agent，判断诉求信息是否足够，遵循以下原则：
- 「具体地点」对派单至关重要：如果诉求没有说明具体位置（例如只说"下水道堵了""很吵"但没说在哪），必须 need_clarify=true 并反问具体位置。
- 事项类型模糊、或无法判断紧急程度时，同样需要反问澄清。
- 只有当事项类型、具体地点、紧急程度都足够明确时，才 need_clarify=false。

只输出 JSON：
{{"need_clarify": false, "clarify_question": "", "intake": {{"category": "事项类型", "location": "地点", "urgency": "一般/紧急", "keywords": "关键词"}}}}"""

    data = _chat_json(prompt, system=INTAKE_SYSTEM) or {}
    need_clarify = bool(data.get("need_clarify"))
    clarify_question = data.get("clarify_question", "")
    intake = data.get("intake") or {}
    print(f"[受理Agent] need_clarify={need_clarify} | 问题={clarify_question} | 要素={intake}")
    return {
        "need_clarify": need_clarify,
        "clarify_question": clarify_question,
        "intake": intake,
    }


RETRIEVAL_SYSTEM = (
    "你是政务热线的检索 Agent。根据诉求要素，调用工具检索部门权责清单和历史相似工单，"
    "把检索到的内容原样返回，不要自行下结论。"
)


def retrieval_node(state: TriageState):
    intake = state.get("intake") or {}
    query = " ".join(
        [intake.get("category", ""), intake.get("location", ""), intake.get("keywords", "")]
    ).strip()
    if not query:
        query = state.get("user_input", "")

    messages = [
        {"role": "system", "content": RETRIEVAL_SYSTEM},
        {"role": "user", "content": f"诉求要素：{json.dumps(intake, ensure_ascii=False)}\n请检索相关信息。"},
    ]

    collected = []
    for _ in range(2):
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=RETRIEVAL_TOOLS,
            tool_choice="auto",
            temperature=0,
            timeout=20,
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            if msg.content:
                collected.append(msg.content)
            break
        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            }
        )
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except Exception:
                args = {}
            result = run_tool(tc.function.name, args)
            print(f"[检索Agent] 调用工具 {tc.function.name}({args}) -> {result[:60]}...")
            collected.append(result)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return {"retrieval": "\n".join(collected)}


DECISION_SYSTEM = "你是政务热线的决策 Agent，负责综合检索结果给出最终分诊结论。"


def decision_node(state: TriageState):
    intake = state.get("intake") or {}
    retrieval = state.get("retrieval") or ""
    prompt = f"""【诉求要素】：{json.dumps(intake, ensure_ascii=False)}
【检索结果】：{retrieval}

请综合给出分诊结论，只输出 JSON：
{{"summary":"20字以内总结","mainDept":"主办单位","assistDept":"协办单位(无则填街道办事处)","basis":"法律或权责依据","confidence":0.95,"needHuman":false}}"""

    data = _chat_json(prompt, system=DECISION_SYSTEM) or {}
    return {"final_result": data}


def route_after_intake(state: TriageState) -> str:
    return "clarify" if state.get("need_clarify") else "retrieval"


builder = StateGraph(TriageState)
builder.add_node("intake", intake_node)
builder.add_node("retrieval", retrieval_node)
builder.add_node("decision", decision_node)
builder.add_edge(START, "intake")
builder.add_conditional_edges(
    "intake",
    route_after_intake,
    {"clarify": END, "retrieval": "retrieval"},
)
builder.add_edge("retrieval", "decision")
builder.add_edge("decision", END)
graph = builder.compile()
print("[启动] 多Agent LangGraph 分诊已加载")


def simple_triage(text: str):
    """兜底：单次检索 + 单次生成的简化流程（不做多 Agent）"""
    context = search_regulation(text)
    prompt = f"""
    你是一个政务热线智能分诊助手。请根据用户的诉求，以及我们检索到的知识库上下文，给出分诊结果。

    【用户诉求】：{text}
    【知识库检索结果】：{context}

    请严格按照以下 JSON 格式返回（不要返回任何其他废话）：
    {{
        "summary": "对诉求的20字以内精炼总结",
        "mainDept": "推荐的主办单位名称",
        "assistDept": "推荐的协办单位名称，如果没有就填'街道办事处'",
        "basis": "派单的法律或权责依据",
        "confidence": 0.95,
        "needHuman": false
    }}
    """
    return _chat_json(prompt)


@app.post("/triage")
def triage(req: TriageRequest):
    text = req.text

    if client is None:
        return {
            "summary": text,
            "mainDept": "综合执法局",
            "assistDept": "待定",
            "basis": "未配置 DEEPSEEK_API_KEY，请配置后重试",
            "confidence": 0.5,
            "needHuman": True,
        }

    # 优先走 LangGraph 多 Agent 流程
    try:
        out = graph.invoke({"user_input": text, "history": req.history})
        if out.get("need_clarify"):
            return {"type": "clarify", "question": out.get("clarify_question", "")}
        result = out.get("final_result")
        if result:
            remember_history(text, result)
            return result
    except Exception as e:
        print(f"[多Agent] 编排失败，回退单次生成: {e}")

    # 兜底：单次生成
    result = None
    try:
        result = simple_triage(text)
    except Exception as e:
        print(f"[模型] 调用失败: {e}")

    if result is None:
        result = {
            "summary": text,
            "mainDept": "综合执法局",
            "assistDept": "待定",
            "basis": "模型处理异常，建议人工介入",
            "confidence": 0.5,
            "needHuman": True,
        }

    remember_history(text, result)
    return result
