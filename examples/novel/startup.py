import asyncio
import re
import subprocess
from typing import Dict, List, Optional

import fire

from metagpt.actions import Action
from metagpt.context import Context
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.team import Team


class NovelContext(Context):
    """共享的小说创作上下文"""

    outline: Optional[str] = None
    characters: List[str] = []
    chapters: List[str] = []
    content: Dict[str, str] = {}


class GenerateOutline(Action):
    PROMPT_TEMPLATE: str = """
    作为专业小说家，请生成关于'{instruction}'的详细大纲，包含：
      - 世界观设定
      - 故事开端（200字）
      - 3个关键冲突事件
      - 高潮场景描述
      - 结局类型（开放式/大团圆/悲剧）
    """

    name: str = "GenerateOutline"

    async def run(self, instruction: str):
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction)
        outline = await self._aask(prompt)
        return outline


class DesignCharacters(Action):
    PROMPT_TEMPLATE: str = """
    根据以下大纲设计主要角色：
    {context.outline}
    每个角色需要包含：
    - 姓名
    - 背景故事
    - 性格特征
    - 角色发展弧线
    - 与其他角色的关系
    """

    name: str = "DesignCharacters"

    async def run(self, context: NovelContext):
        prompt = self.PROMPT_TEMPLATE.format(context=context)
        characters = await self._aask(prompt)
        return characters


class GenerateChapterList(Action):
    """生成章节列表"""

    async def run(self, context: NovelContext):
        prompt = f"""
        根据以下大纲生成详细的章节列表：
        {context.outline}
        要求：
        - 每个章节需要标题和概要
        - 标注关键章节类型（铺垫/转折/高潮等）
        - 包含章节间的逻辑衔接
        - 总章节数在20-30章之间
        """
        return await self._aask(prompt)


class WriteChapter(Action):
    """撰写具体章节内容"""

    async def run(self, context: NovelContext, chapter) -> str:
        prompt = f"""
        根据以下信息撰写章节内容：
        大纲：{context.outline}
        角色列表：{context.characters}
        章节信息：{chapter}

        要求：
        - 保持3000-5000字
        - 包含场景描写和角色对话
        - 符合章节类型特点
        - 设置悬念引导后续章节
        """
        return await self._aask(prompt)


class OutlineGenerator(Role):
    name: str = "文抄公"
    profile: str = "OutlineGenerator"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateOutline()])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]
        text = await todo.run(msg.content)
        self.context.outline = text
        msg = Message(content=text, role=self.profile, cause_by=type(todo))

        return msg


class CharacterDesigner(Role):
    name: str = "角色大师"
    profile: str = "CharacterDesigner"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([GenerateOutline()])
        self.set_actions([DesignCharacters()])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        characters = await todo.run(self.context.outline)
        self.context.characters = characters
        msg = Message(content=characters, role=self.profile, cause_by=type(todo))

        return msg


class ChapterLister(Role):
    name: str = "章节列表大师"
    profile: str = "ChapterLister"

    def __init__(self):
        super().__init__()
        self._watch([DesignCharacters()])
        self.set_actions([GenerateChapterList])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        chapters = await todo.run(self.context)
        self.context.chapters = chapters
        msg = Message(content=chapters, role=self.profile, cause_by=type(todo))

        return msg


class WriteChapter(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([DesignCharacters()])
        self.set_actions([WriteChapter()])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]  # find the most recent messages
        characters = await todo.run(msg.content)
        print(characters)
        msg = Message(content=characters, role=self.profile, cause_by=type(todo))

        return msg


# def main(msg="斗罗大陆同人小说"):
#     role = OutlineGenerator()
#     logger.info(msg)
#     result = asyncio.run(role.run(msg))
#     logger.info(result)


async def main(
    idea: str = "斗罗大陆同人小说",
    investment: float = 3.0,
    n_round: int = 5,
    add_human: bool = False,
):
    logger.info(idea)
    context = NovelContext()
    team = Team(context=context)
    team.hire(
        [
            OutlineGenerator(),
            CharacterDesigner(),
            ChapterLister(),
            # SimpleReviewer(is_human=add_human),
        ]
    )

    # team.invest(investment=investment)
    team.run_project(idea)
    await team.run(n_round=n_round)


if __name__ == "__main__":
    fire.Fire(main)
