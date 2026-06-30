"""
小说规则管理器（Novel Rules）
管理 per-novel 写作规则，支持 AI 对话式规则建立。
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import config


class RulesManager:
    """单本小说的规则管理器"""

    def __init__(self, novel_id: str):
        self.novel_id = novel_id
        self._data: Dict[str, Any] = {}
        self._loaded = False

    @property
    def _file_path(self) -> str:
        return os.path.join(config.NOVELS_DIR, self.novel_id, "rules.json")

    def load(self) -> Dict[str, Any]:
        """加载规则，不存在则返回空模板"""
        if self._loaded:
            return self._data
        try:
            if os.path.exists(self._file_path):
                with open(self._file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            else:
                self._data = self._empty_template()
                self._save_raw()
        except Exception as e:
            print(f"[RulesManager] 加载规则失败: {e}")
            self._data = {}
            raise ValueError(f"规则文件格式错误: {self._file_path}: {e}") from e
        self._loaded = True
        return self._data

    def save_rules(self) -> bool:
        """持久化到磁盘"""
        try:
            self._data["updated_at"] = datetime.now().isoformat()
            self._save_raw()
            return True
        except Exception as e:
            print(f"[RulesManager] 保存规则失败: {e}")
            return False

    # ── 规则 CRUD ──

    def add_rule(self, rule: Dict[str, Any]) -> str:
        """添加一条规则，返回 rule id"""
        return self.add_rules([rule])[0]

    def add_rules(self, rules_to_add: List[Dict[str, Any]]) -> List[str]:
        """批量添加规则，只执行一次磁盘写入。"""
        self.load()
        rules: List[Dict] = self._data.setdefault("rules", [])
        entries = []
        for rule in rules_to_add:
            entries.append({
                "id": rule.get("id") or uuid.uuid4().hex[:12],
                "created_at": datetime.now().isoformat(),
                "category": rule.get("category", "general"),
                "title": rule.get("title", ""),
                "content": rule.get("content", ""),
                "priority": rule.get("priority", "should"),
                "examples": rule.get("examples") or [],
                "history": rule.get("history") or [],
            })
        rules.extend(entries)
        self.save_rules()
        return [entry["id"] for entry in entries]

    def update_rule(self, rule_id: str, patch: Dict[str, Any]) -> bool:
        """更新某条规则的部分字段"""
        self.load()
        for rule in self._data.get("rules", []):
            if rule.get("id") == rule_id:
                for key in ("title", "content", "category", "priority", "examples"):
                    if key in patch:
                        rule[key] = patch[key]
                rule["updated_at"] = datetime.now().isoformat()
                self.save_rules()
                return True
        return False

    def delete_rule(self, rule_id: str) -> bool:
        """删除规则"""
        self.load()
        rules = self._data.get("rules", [])
        new_rules = [r for r in rules if r.get("id") != rule_id]
        if len(new_rules) == len(rules):
            return False
        self._data["rules"] = new_rules
        self.save_rules()
        return True

    def get_rules_context(self, priority_filter: Optional[List[str]] = None) -> str:
        """
        生成可注入写作 prompt 的规则摘要。
        priority_filter: 可选 ['must'] 只返回高优先级规则
        """
        self.load()
        rules: List[Dict] = self._data.get("rules", [])
        preferences = self._data.get("global_preferences", {})
        if not rules and not preferences:
            return ""

        lines = ["【用户设定的写作规则 — 必须遵守】", ""]

        # 分类展示
        by_category: Dict[str, List[Dict]] = {}
        for rule in rules:
            if priority_filter and rule.get("priority") not in priority_filter:
                continue
            cat = rule.get("category", "general")
            by_category.setdefault(cat, []).append(rule)

        cat_labels = {
            "writing_style": "文笔风格",
            "character": "人物塑造",
            "plot": "情节安排",
            "dialogue": "对话写法",
            "pacing": "节奏控制",
            "worldbuilding": "世界观构建",
            "general": "通用规则",
        }

        for cat, cat_rules in by_category.items():
            label = cat_labels.get(cat, cat)
            lines.append(f"## {label}")
            for r in cat_rules:
                priority_mark = "🔴" if r.get("priority") == "must" else "🟡" if r.get("priority") == "should" else "🟢"
                lines.append(f"- {priority_mark} **{r.get('title', '')}**：{r.get('content', '')}")
                examples = r.get("examples")
                if examples:
                    for ex in examples[:2]:
                        lines.append(f"  - 示例：{ex}")
            lines.append("")

        # 全局偏好
        if preferences:
            lines.append("## 全局偏好")
            if preferences.get("style_notes"):
                lines.append(f"- 风格备注：{preferences['style_notes']}")
            taboos = preferences.get("taboos", [])
            if taboos:
                lines.append(f"- 禁忌：{' / '.join(taboos)}")

        return "\n".join(lines)

    def set_global_preferences(self, prefs: Dict[str, Any]) -> bool:
        """设置全局偏好（风格备注、禁忌等）"""
        self.load()
        self._data["global_preferences"] = prefs
        return self.save_rules()

    # ── 内部 ──

    def _empty_template(self) -> Dict[str, Any]:
        return {
            "novel_id": self.novel_id,
            "created_at": datetime.now().isoformat(),
            "rules": [],
            "global_preferences": {},
        }

    def _save_raw(self):
        os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)


# ── 规则对话 Prompt ──

RULES_DIALOGUE_SYSTEM_PROMPT = """你是一位专业的网文写作教练，正在帮助作者梳理和建立他的小说写作规则。

你在和作者对话，目标是帮他明确：
1. **写作风格**：偏好什么文风？忌讳什么腔调？
2. **情节偏好**：喜欢快节奏还是慢热？爽点密度？虐点偏好？
3. **人物塑造**：主角性格定位？配角作用？感情线尺度？
4. **对话/描写比例**：对话多还是叙述多？环境描写的详细程度？
5. **特殊禁忌**：绝对不能出现的内容（如现代梗、第一人称、特定套路等）

## 规则优先级说明
- 🔴 must（必须遵守）：强制规则，违反即打回
- 🟡 should（建议遵守）：强烈建议，有理由可以破例
- 🟢 may（可以尝试）：探索性建议，不强制

## 对话策略
- 先从作者最关心的方向开始聊，不要一次问太多
- 每次只深入 1-2 个维度，问清楚再换下一个
- 给具体例子让用户选择："你喜欢 A 风格还是 B 风格？比如……"
- 当用户表达模糊时，用对比追问："你说的'爽'是指打脸逆袭还是扮猪吃虎？"
- 每个维度聊完后做一个小结确认

## 确认时机
当你觉得至少聊清楚了 2-3 个维度的规则，给出确认总结（stage=confirming），总结包含：
- 已明确的规则要点
- 每条规则的优先级建议

## 格式要求
返回纯 JSON（不要 markdown 代码块）：
{"question":"你的提问/确认内容","options":["选项1","选项2","选项3"],"stage":"clarifying|confirming|done","rule_updates":[]}

当 stage=confirming 或 done 时，将提取的规则填入 rule_updates 数组；每个可独立执行的要求必须是单独一项：
{"rule_updates":[{"category":"writing_style","title":"规则标题","content":"规则内容","priority":"must|should|may","examples":["示例"]}]}

对话已结束返回：
{"question":"规则已梳理完成！你随时可以回来继续完善。","options":["回顾已有规则","添加新规则","微调某条规则","结束对话"],"stage":"done","rule_update":null}
"""


def build_rules_dialogue_messages(
    messages: List[Dict[str, Any]],
    novel_context: Dict[str, Any],
    existing_rules: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """构建规则对话的消息列表"""
    title = novel_context.get("title", "未命名小说")
    tags = novel_context.get("tags", {})

    # 上下文字符串
    tag_str = json.dumps(tags, ensure_ascii=False) if tags else "暂无"
    rules_str = json.dumps(existing_rules, ensure_ascii=False, indent=2) if existing_rules else "暂无规则"

    user_turns = sum(1 for m in messages if m.get("role") == "user")

    if user_turns == 0:
        stage_hint = "这是第 1 轮。作者刚刚开始，先问他想建立什么方面的规则（写作风格/情节/人物/对话/禁忌），给 4-5 个具体选项引导他。"
    else:
        stage_hint = (
            f"这是第 {user_turns + 1} 轮。根据之前的对话判断：如果还有维度没聊清楚，继续深入追问；"
            "如果至少 2-3 个维度已经明确，可以给确认总结（stage=confirming）。不要急着结束，确保作者充分表达。"
        )

    system_prompt = RULES_DIALOGUE_SYSTEM_PROMPT + f"""

## 当前小说信息
- 书名：{title}
- 标签：{tag_str}

## 已有规则
{rules_str}

{stage_hint}
"""

    llm_messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        llm_messages.append({"role": role, "content": content})

    if not messages:
        llm_messages.append({"role": "user", "content": "我想为这本小说建立一些写作规则"})

    return llm_messages
