from metagpt.actions import Action


class GenerateOutline(Action):
    """生成小说大纲的行动"""
    PROMPT_TEMPLATE: str = """
    作为专业小说家，请根据以下主题生成详细小说大纲：
    '{theme}'

    请包含以下内容：
    - 小说标题
    - 世界观/背景设定
    - 故事主题与中心思想
    - 总体故事结构（起因、经过、高潮、结局）
    - 故事开端简述
    - 故事结局类型及简述

    请以结构化形式呈现。
    """

    name: str = "GenerateOutline"

    async def run(self, theme: str):
        prompt = self.PROMPT_TEMPLATE.format(theme=theme)
        outline = await self._aask(prompt)
        return outline
