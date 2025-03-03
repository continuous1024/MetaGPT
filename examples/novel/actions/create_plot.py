from metagpt.actions import Action
from novel_context import NovelContext


class CreatePlot(Action):
    """创建小说剧情的行动"""
    PROMPT_TEMPLATE: str = """
    根据以下小说大纲和角色设定，创建详细的剧情发展：

    大纲：
    {context.outline}

    角色：
    {context.characters}

    请提供以下内容：
    1. 主要故事线
    2. 次要故事线（如有）
    3. 主要冲突和障碍
    4. 转折点和关键事件
    5. 高潮场景
    6. 情节发展的节奏安排
    7. 情感发展轨迹

    请确保剧情逻辑连贯，人物行为符合其设定，并且有足够的冲突和悬念保持读者兴趣。
    请以结构化形式呈现。
    """

    name: str = "CreatePlot"

    async def run(self, context: NovelContext):
        prompt = self.PROMPT_TEMPLATE.format(context=context)
        plot = await self._aask(prompt)
        return plot
