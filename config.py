"""
InkAI 小说创作系统配置文件
"""
import os
from typing import Dict, List

# API配置（DeepSeek，兼容 OpenAI 格式）
API_KEY = "your_deepseek_api_key_here"
BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-v4-flash"
TEMPERATURE = 0.6

# Token配置
MAX_TOKENS = 8192  # GLM-4.5-flash的最大输出token数
CHAPTER_MAX_TOKENS = 8192  # 章节写作专用的最大token数

# 嵌入模型配置 (用于续写功能)
EMBEDDING_API_KEY = "your_embedding_api_key_here"
EMBEDDING_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/embeddings"
EMBEDDING_MODEL = "embedding-3"

# 标签配置
TAG_CATEGORIES = {
    "类型标签": ["玄幻", "都市", "悬疑", "科幻", "言情", "历史", "军事", "武侠", "仙侠", "奇幻", "耽美", "百合", "轻小说", "同人", "游戏", "无限流", "系统", "修真", "灵异", "推理", "侦探", "西幻", "末世", "重生", "穿越", "历史架空", "军事战争", "科幻机甲", "赛博朋克", "克苏鲁"],
    "主题标签": ["复仇", "成长", "权谋", "治愈", "冒险", "爱情", "友情", "家庭", "职场", "校园", "救赎", "逆袭", "商战", "社会问题", "心理", "惊悚", "恐怖", "末日生存", "异能", "超能力", "时间旅行", "平行宇宙", "人工智能", "环保", "社会批判", "政治斗争", "经济斗争", "伦理", "探索", "寻宝", "谍战", "间谍", "悬疑解谜", "家庭伦理", "青春成长", "校园恋爱", "友情羁绊", "亲情", "爱情纠葛"],
    "风格标签": ["幽默诙谐", "严肃深刻", "文艺抒情", "热血激昂", "温馨治愈", "黑暗压抑", "轻松愉快", "悬疑紧张", "浪漫唯美", "冷峻写实", "奇幻瑰丽", "细腻描写", "快节奏", "慢节奏", "史诗感", "日常系", "沙雕", "虐心", "治愈系", "黑暗系", "现实主义", "超现实", "后现代", "哥特", "蒸汽朋克", "赛博朋克", "史诗", "轻松", "沉重", "光明", "冷酷", "讽刺", "荒诞", "诗意", "口语化", "叙事性强"],
    "受众标签": [ "青少年", "成年人", "女性向", "男性向", "全年龄", "儿童向", "少女向", "少男向", "中年向", "老年向", "学生", "上班族", "家庭主妇", "退休人员", "LGBTQ+群体", "二次元爱好者", "科幻迷", "历史爱好者", "游戏爱好者", "动漫爱好者", "家庭向", "情侣向", "亲子向", "特定兴趣群体"],
    "字数标签": ["短篇（<10万字）", "中篇（10-30万字）", "长篇（30-80万字）", "超长篇（80-200万字）", "巨著（>200万字）"]
}

# 人物原型库
CHARACTER_ARCHETYPES = {
    "侦探": {
        "traits": ["观察力强", "逻辑思维", "独来独往", "正义感强"],
        "background": "通常有执法或调查背景",
        "motivation": "追求真相和正义"
    },
    "学生": {
        "traits": ["好奇心强", "学习能力", "年轻活力", "理想主义"],
        "background": "校园生活，青春年华",
        "motivation": "成长和探索世界"
    },
    "医生": {
        "traits": ["专业严谨", "救死扶伤", "冷静理性", "责任感强"],
        "background": "医学专业背景",
        "motivation": "拯救生命，医学研究"
    }
}

# 故事结构配置
STORY_STRUCTURE = {
    "三幕剧": {
        "第一幕": {
            "setup": "介绍世界观、主角目标、初始冲突",
            "length_ratio": 0.25
        },
        "第二幕": {
            "confrontation": "中期危机、低谷期、转折点",
            "length_ratio": 0.5
        },
        "第三幕": {
            "resolution": "高潮对决、结局",
            "length_ratio": 0.25
        }
    }
}

# 质量评估标准
QUALITY_THRESHOLD = 80
QUALITY_DIMENSIONS = {
    "情节连贯性": {"weight": 0.3, "description": "无前后矛盾，伏笔100%呼应"},
    "人物立体度": {"weight": 0.25, "description": "角色情绪变化自然，动机合理"},
    "语言风格": {"weight": 0.25, "description": "符合标签的紧张感"},
    "创新吸引力": {"weight": 0.2, "description": "读者停留率>60%，点赞率>30%"}
}

# 文件路径配置
# 项目根目录（config.py 所在目录，即 InkAI-gzx），用绝对路径，避免受运行时工作目录影响
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 小说数据输出目录：默认放到 InkAI-gzx 同级的 ../InkAI-Books（与代码分离，便于单独用 git 管理小说）
# 可用环境变量 INKAI_BOOKS_DIR 覆盖默认路径
DATA_DIR = os.environ.get(
    "INKAI_BOOKS_DIR",
    os.path.abspath(os.path.join(_PROJECT_ROOT, "..", "InkAI-Books"))
)
NOVELS_DIR = os.path.join(DATA_DIR, "novels")
KNOWLEDGE_GRAPHS_DIR = os.path.join(DATA_DIR, "knowledge_graphs")
# templates 属于代码资源，始终跟随项目目录，不随小说数据外移
TEMPLATES_DIR = os.path.join(_PROJECT_ROOT, "templates")

# 确保目录存在
for directory in [DATA_DIR, NOVELS_DIR, KNOWLEDGE_GRAPHS_DIR, TEMPLATES_DIR]:
    os.makedirs(directory, exist_ok=True)
