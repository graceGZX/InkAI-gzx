"""
质量评估智能体
负责评估小说内容的质量
"""

from base_agent import BaseAgent
from typing import Dict, List, Any
import config


class QualityAssessorAgent(BaseAgent):
    """质量评估智能体"""
    
    def __init__(self):
        super().__init__("质量评估智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理质量评估请求"""
        content = input_data.get("content", {})
        content_type = input_data.get("content_type", "story")  # story, character, storyline
        user_requirements = input_data.get("user_requirements", "")
        
        # 根据内容类型选择评估方法
        if content_type == "character":
            return self._assess_character_quality(content, user_requirements)
        elif content_type == "storyline":
            # 获取额外的上下文信息
            previous_chapters = input_data.get("previous_chapters", None)
            overall_storyline = input_data.get("overall_storyline", None)
            return self._assess_storyline_quality(content, user_requirements, previous_chapters, overall_storyline)
        else:
            return self._assess_story_quality(content, user_requirements)
    
    def _assess_character_quality(self, character: Dict[str, Any], user_requirements: str = "") -> Dict[str, Any]:
        """评估人物质量"""
        prompt = f"""
        你是一位专业的文学评论家和小说编辑，请对以下小说角色进行深度质量评估：
        
        【评估背景】
        用户创作需求：{user_requirements if user_requirements else "无特定需求"}
        
        【角色信息】
        {self._format_character_for_assessment(character)}
        
        【专业评估维度】
        请从以下专业角度进行详细评估：
        
        1. 人物立体度 (0-100分)
           - 性格复杂性：角色是否具有多面性，避免脸谱化
           - 内在冲突：角色内心是否有合理的矛盾和挣扎
           - 成长潜力：角色是否有明确的成长弧线和变化空间
           - 细节丰富度：角色细节是否生动具体
        
        2. 心理学可信度 (0-100分)
           - 行为逻辑：角色行为是否符合心理学规律
           - 动机合理性：行为动机是否真实可信
           - 情感真实性：角色情感反应是否自然
           - 人格一致性：性格特征是否内在一致
        
        3. 故事功能性 (0-100分)
           - 情节推动：角色是否能有效推动故事发展
           - 冲突创造：角色是否能产生戏剧冲突
           - 主题体现：角色是否能体现故事主题
           - 读者共鸣：角色是否能引起读者情感共鸣
        
        4. 文学价值 (0-100分)
           - 独特性：角色是否具有独特的个性特征
           - 记忆点：角色是否有令人印象深刻的特质
           - 象征意义：角色是否具有深层象征意义
           - 文化价值：角色是否具有文化或社会意义
        
        5. 需求匹配度 (0-100分)
           - 类型适配：角色是否符合指定的小说类型
           - 风格一致：角色风格是否与整体风格匹配
           - 目标受众：角色是否适合目标读者群体
           - 商业价值：角色是否具有市场吸引力
        
        【评估标准】
        - 90-100分：优秀，达到出版标准
        - 80-89分：良好，需要小幅调整
        - 70-79分：一般，需要明显改进
        - 60-69分：较差，需要大幅修改
        - 60分以下：不合格，需要重新设计
        
        【输出要求】
        请返回详细的JSON格式评估报告：
        {{
            "scores": {{
                "dimensionality": 人物立体度分数,
                "psychological_credibility": 心理学可信度分数,
                "story_functionality": 故事功能性分数,
                "literary_value": 文学价值分数,
                "requirement_match": 需求匹配度分数
            }},
            "overall_score": 综合总分(0-100),
            "quality_level": "优秀/良好/一般/较差/不合格",
            "strengths": [
                "具体优点1（详细说明）",
                "具体优点2（详细说明）",
                "具体优点3（详细说明）"
            ],
            "weaknesses": [
                "具体缺点1（详细说明）",
                "具体缺点2（详细说明）",
                "具体缺点3（详细说明）"
            ],
            "suggestions": [
                "具体改进建议1（可操作）",
                "具体改进建议2（可操作）",
                "具体改进建议3（可操作）"
            ],
            "detailed_analysis": {{
                "character_depth": "角色深度分析（200字以上）",
                "psychological_insights": "心理学洞察分析（200字以上）",
                "story_potential": "故事潜力分析（200字以上）",
                "improvement_priority": "改进优先级排序"
            }},
            "is_high_quality": true/false,
            "recommendation": "建议：继续使用/需要改进/重新设计"
        }}
        """
        
        messages = [
            {"role": "system", "content": """你是一位世界级的文学评论家、小说编辑和创意写作导师，拥有以下专业背景：

1. 文学理论专长：精通各种文学理论和创作技巧
2. 心理学洞察：具备深厚的心理学知识，能分析角色的心理真实性
3. 市场经验：了解读者喜好和市场趋势
4. 编辑经验：拥有丰富的作品编辑和优化经验
5. 教学经验：指导过无数作家提升创作水平

你的评估原则：
- 客观公正：基于专业标准进行客观评估
- 建设性：提供具体可行的改进建议
- 全面性：从多个维度进行综合评估
- 实用性：评估结果要能指导实际创作
- 专业性：运用专业的文学和心理学理论

请用专业、细致、建设性的态度完成质量评估任务。"""},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _assess_storyline_quality(self, storyline: Dict[str, Any], user_requirements: str = "",
                                 previous_chapters: List[Dict[str, Any]] = None,
                                 overall_storyline: Dict[str, Any] = None) -> Dict[str, Any]:
        """评估故事线质量"""
        
        # 构建上下文信息
        context_info = ""
        if previous_chapters:
            context_info += f"\n前续章节信息：\n{self._format_previous_chapters(previous_chapters)}"
        
        if overall_storyline:
            context_info += f"\n整体故事线：\n{self._format_overall_storyline(overall_storyline)}"
        
        prompt = f"""
        请评估以下故事线的质量：
        
        用户创作需求：
        {user_requirements if user_requirements else "无特定需求"}
        
        当前章节故事线信息：
        {self._format_storyline_for_assessment(storyline)}
        {context_info}
        
        评估维度：
        1. 情节连贯性 (0-100分)：与前面章节的故事线是否连贯，逻辑是否清晰
        2. 整体协调性 (0-100分)：是否符合整体故事线的发展方向
        3. 结构完整性 (0-100分)：该章节是否有完整的故事结构
        4. 冲突设计 (0-100分)：冲突是否合理，是否有张力
        5. 创新性 (0-100分)：在保持连贯性的基础上是否有新意
        
        请返回JSON格式：
        {{
            "scores": {{
                "coherence": 情节连贯性分数,
                "coordination": 整体协调性分数,
                "structure": 结构完整性分数,
                "conflict": 冲突设计分数,
                "innovation": 创新性分数
            }},
            "overall_score": 总分(0-100),
            "strengths": ["优点1", "优点2"],
            "weaknesses": ["缺点1", "缺点2"],
            "suggestions": ["改进建议1", "改进建议2"],
            "is_high_quality": true/false
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的故事结构分析专家，擅长评估故事线的质量。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _assess_story_quality(self, story: Dict[str, Any], user_requirements: str = "") -> Dict[str, Any]:
        """评估故事内容质量"""
        prompt = f"""
        请评估以下故事内容的质量：
        
        用户创作需求：
        {user_requirements if user_requirements else "无特定需求"}
        
        故事内容：
        {self._format_story_for_assessment(story)}
        
        评估维度：
        1. 情节连贯性 (0-100分)：故事逻辑是否清晰，伏笔是否呼应
        2. 人物立体度 (0-100分)：角色是否生动，性格是否丰富
        3. 语言风格 (0-100分)：文笔是否流畅，风格是否统一
        4. 创新吸引力 (0-100分)：内容是否有新意，能否吸引读者
        
        请返回JSON格式：
        {{
            "scores": {{
                "coherence": 情节连贯性分数,
                "characterization": 人物立体度分数,
                "writing_style": 语言风格分数,
                "appeal": 创新吸引力分数
            }},
            "overall_score": 总分(0-100),
            "strengths": ["优点1", "优点2"],
            "weaknesses": ["缺点1", "缺点2"],
            "suggestions": ["改进建议1", "改进建议2"],
            "is_high_quality": true/false
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的小说质量评估专家，擅长全面评估故事内容的质量。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _format_character_for_assessment(self, character: Dict[str, Any]) -> str:
        """格式化人物信息用于评估"""
        basic_info = character.get("basic_info", {})
        personality = character.get("personality", {})
        background = character.get("background", {})
        
        return f"""
        基础信息：
        - 姓名: {basic_info.get('name', '未知')}
        - 年龄: {basic_info.get('age', '未知')}
        - 职业: {basic_info.get('occupation', '未知')}
        
        性格特质：
        - 外向性: {personality.get('extraversion', '未知')}
        - 宜人性: {personality.get('agreeableness', '未知')}
        - 尽责性: {personality.get('conscientiousness', '未知')}
        - 神经质: {personality.get('neuroticism', '未知')}
        - 开放性: {personality.get('openness', '未知')}
        - 描述: {personality.get('description', '未知')}
        
        背景动机：
        - 核心欲望: {background.get('core_desire', '未知')}
        - 主要恐惧: {background.get('fear', '未知')}
        - 过往经历: {background.get('past_experience', '未知')}
        - 行为动机: {background.get('motivation', '未知')}
        """
    
    def _format_storyline_for_assessment(self, storyline: Dict[str, Any]) -> str:
        """格式化故事线信息用于评估"""
        return f"""
        世界观: {storyline.get('world_setting', '未知')}
        主角目标: {storyline.get('main_goal', '未知')}
        核心冲突: {storyline.get('conflict', '未知')}
        
        第一幕: {storyline.get('act1', {}).get('setup', '未知')}
        第二幕: {storyline.get('act2', {}).get('confrontation', '未知')}
        第三幕: {storyline.get('act3', {}).get('climax', '未知')}
        
        主题: {', '.join(storyline.get('themes', []))}
        基调: {storyline.get('tone', '未知')}
        """
    
    def _format_story_for_assessment(self, story: Dict[str, Any]) -> str:
        """格式化故事内容用于评估"""
        if isinstance(story, dict):
            # 如果是字典，提取主要内容
            content = story.get("content", "")
            if not content:
                # 尝试从其他字段提取
                content = str(story)
        else:
            content = str(story)
        
        # 限制长度，避免提示词过长
        if len(content) > 2000:
            content = content[:2000] + "..."
        
        return content
    
    def _validate_assessment_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证评估结果"""
        # 确保必要字段存在
        if "scores" not in result:
            result["scores"] = {}
        
        if "overall_score" not in result:
            # 计算总分
            scores = result.get("scores", {})
            if scores:
                total = sum(score for score in scores.values() if isinstance(score, (int, float)))
                count = len([score for score in scores.values() if isinstance(score, (int, float))])
                result["overall_score"] = total / count if count > 0 else 0
            else:
                result["overall_score"] = 0
        
        # 判断是否高质量
        if "is_high_quality" not in result:
            result["is_high_quality"] = result["overall_score"] >= config.QUALITY_THRESHOLD
        
        # 确保其他字段存在
        for field in ["strengths", "weaknesses", "suggestions"]:
            if field not in result:
                result[field] = []
        
        return result
    
    def _format_previous_chapters(self, chapters: List[Dict[str, Any]]) -> str:
        """格式化前续章节信息"""
        if not chapters:
            return "无前续章节"
        
        formatted = ""
        for i, chapter in enumerate(chapters, 1):
            chapter_num = chapter.get("chapter_number", i)
            title = chapter.get("title", f"第{chapter_num}章")
            summary = chapter.get("summary", "无概要")
            key_events = chapter.get("key_events", [])
            
            formatted += f"第{chapter_num}章 - {title}:\n"
            formatted += f"  概要: {summary}\n"
            if key_events:
                formatted += f"  关键事件: {', '.join(key_events)}\n"
            formatted += "\n"
        
        return formatted
    
    def _format_overall_storyline(self, storyline: Dict[str, Any]) -> str:
        """格式化整体故事线信息"""
        if not storyline:
            return "无整体故事线信息"
        
        formatted = f"""
        整体故事线：
        - 世界观设定: {storyline.get('world_setting', '未知')}
        - 主角目标: {storyline.get('main_goal', '未知')}
        - 核心冲突: {storyline.get('conflict', '未知')}
        - 故事基调: {storyline.get('tone', '未知')}
        - 故事主题: {storyline.get('themes', [])}
        """
        
        # 添加三幕剧结构信息
        structure = storyline.get("structure", {})
        if structure:
            formatted += f"\n三幕剧结构:\n"
            for act, info in structure.items():
                formatted += f"  {act}: {info.get('description', '未知')}\n"
        
        return formatted
