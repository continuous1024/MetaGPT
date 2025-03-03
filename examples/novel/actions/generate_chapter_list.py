from metagpt.actions import Action
from novel_context import NovelContext


class GenerateChapterList(Action):
    """生成章节列表的行动"""
    PROMPT_TEMPLATE: str = """
    根据以下信息生成详细的章节列表：

    大纲：
    {context.outline}

    角色：
    {context.characters}

    剧情：
    {context.plot}

    请创建20-30个章节的详细列表，每个章节包含：
    1. 章节号和标题
    2. 章节内容简介（100-200字）
    3. 章节中的关键事件
    4. 章节中出场的主要角色
    5. 章节类型（铺垫/转折/高潮/结局等）

    请确保章节之间有合理的逻辑衔接，并形成完整的故事弧线。
    请以结构化形式呈现。
    """

    name: str = "GenerateChapterList"

    async def run(self, context: NovelContext):
        prompt = self.PROMPT_TEMPLATE.format(context=context)
        chapter_list = await self._aask(prompt)
        return chapter_list