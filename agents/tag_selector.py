"""
标签选择智能体
负责根据用户需求推荐和选择小说标签
"""
from base_agent import BaseAgent
from typing import Dict, List, Any
import config


class TagSelectorAgent(BaseAgent):
    """标签选择智能体"""
    
    def __init__(self):
        super().__init__("标签选择智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理标签选择请求"""
        user_requirements = input_data.get("user_requirements", "")
        
        # 分析用户需求并推荐标签
        recommended_tags = self._analyze_and_recommend_tags(user_requirements)
        
        # 如果用户没有明确选择，使用推荐标签
        selected_tags = input_data.get("selected_tags", recommended_tags)
        
        # 确保selected_tags不为None
        if selected_tags is None:
            selected_tags = recommended_tags
        
        return {
            "recommended_tags": recommended_tags,
            "selected_tags": selected_tags,
            "tag_categories": config.TAG_CATEGORIES
        }
    
    def _analyze_and_recommend_tags(self, user_requirements: str) -> Dict[str, List[str]]:
        """分析用户需求并推荐标签"""
        if not user_requirements:
            return self._get_default_tags()
        
        # 构建提示词
        prompt = f"""
        根据用户需求分析并推荐合适的小说标签。
        
        用户需求：{user_requirements}
        
        可选的标签分类：
        {self._format_tag_categories()}
        
        请分析用户需求中的关键词，推荐最合适的标签组合。
        返回JSON格式：
        {{
            "类型标签": ["推荐的类型标签"],
            "主题标签": ["推荐的主题标签"],
            "风格标签": ["推荐的风格标签"],
            "受众标签": ["推荐的受众标签"]
        }}
        
        推荐原则：
        1. 根据关键词匹配（如"侦探"→悬疑，"未来"→科幻）
        2. 考虑标签的兼容性
        3. 每个分类推荐1-5个最合适的标签
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的小说标签推荐助手，擅长分析用户需求并推荐合适的标签组合。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        # 验证和修正推荐结果
        return self._validate_and_fix_tags(result)
    
    def _format_tag_categories(self) -> str:
        """格式化标签分类信息"""
        formatted = ""
        for category, tags in config.TAG_CATEGORIES.items():
            formatted += f"{category}: {', '.join(tags)}\n"
        return formatted
    
    def _get_default_tags(self) -> Dict[str, List[str]]:
        """获取默认标签组合"""
        return {
            "类型标签": ["都市"],
            "主题标签": ["成长"],
            "风格标签": ["轻松愉快"],
            "受众标签": ["全年龄"]
        }
    
    def _validate_and_fix_tags(self, tags: Dict[str, Any]) -> Dict[str, List[str]]:
        """验证和修正标签"""
        valid_tags = {}
        
        for category, tag_list in config.TAG_CATEGORIES.items():
            if category in tags and isinstance(tags[category], list):
                # 验证标签是否在可选范围内
                valid_tag_list = [tag for tag in tags[category] if tag in tag_list]
                if not valid_tag_list:
                    # 如果没有有效标签，使用默认值
                    valid_tag_list = [tag_list[0]]
                valid_tags[category] = valid_tag_list
            else:
                # 如果没有该分类，使用默认值
                valid_tags[category] = [tag_list[0]]
        
        return valid_tags
