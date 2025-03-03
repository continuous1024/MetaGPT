from metagpt.actions import Action
from examples.novel.startup import NovelContext


class WriteChapter(Action):
    """撰写具体章节内容的行动"""
    PROMPT_TEMPLATE: str = """
    根据以下信息，撰写章节{chapter_num}的内容：
    
    大纲：
    {context.outline}
    
    角色：
    {context.characters}
    
    剧情：
    {context.plot}
    
    章节列表：
    {context.chapter_list}
    
    要求：
    1. 章节内容应该符合章节列表中的描述
    2. 包含丰富的场景描写、人物对话和内心活动
    3. 保持3000-5000字的篇幅
    4. 注意人物语言和行为的一致性
    5. 适当设置悬念，引导读者阅读下一章节
    6. 保持叙述风格的连贯性
    
    请直接撰写章节内容，无需添加额外的说明。
    """

    name: str = "WriteChapter"

    async def run(self, context: NovelContext, chapter_num: int) -> str:
        if chapter_num < 1:
            return "章节编号无效"
            
        prompt = self.PROMPT_TEMPLATE.format(context=context, chapter_num=chapter_num)
        content = await self._aask(prompt)
        return content