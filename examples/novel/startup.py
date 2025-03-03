import asyncio
import os
from typing import Dict, List, Optional

import fire

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.team import Team

# Import actions from our module
from examples.novel.actions.write_outline import GenerateOutline

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


class OutlineGenerator(Role):
    """负责生成小说大纲的角色"""
    name: str = "大纲生成器"
    profile: str = "OutlineGenerator"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateOutline()])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: {self.rc.todo.name}")
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]
        text = await todo.run(msg.content)
        self.context.outline = text
        msg = Message(content=text, role=self.profile, cause_by=type(todo))
        return msg


class CharacterDesigner(Role):
    """负责设计小说角色的角色"""
    name: str = "角色设计师"
    profile: str = "CharacterDesigner"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([GenerateOutline])  # 监听行动而不是角色
        self.set_actions([DesignCharacters()])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: {self.rc.todo.name}")
        todo = self.rc.todo
        characters = await todo.run(self.context)
        self.context.characters = characters
        msg = Message(content=characters, role=self.profile, cause_by=type(todo))
        return msg


class PlotCreator(Role):
    """负责创建小说剧情的角色"""
    name: str = "剧情创作者"
    profile: str = "PlotCreator"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([DesignCharacters])  # 监听行动而不是角色
        self.set_actions([CreatePlot()])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: {self.rc.todo.name}")
        todo = self.rc.todo
        plot = await todo.run(self.context)
        self.context.plot = plot
        msg = Message(content=plot, role=self.profile, cause_by=type(todo))
        return msg


class ChapterListGenerator(Role):
    """负责生成章节列表的角色"""
    name: str = "章节列表生成器"
    profile: str = "ChapterListGenerator"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([CreatePlot])  # 修改为监听行动而不是角色
        self.set_actions([GenerateChapterList()])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: {self.rc.todo.name}")
        todo = self.rc.todo
        chapter_list = await todo.run(self.context)
        self.context.chapter_list = chapter_list
        msg = Message(content=chapter_list, role=self.profile, cause_by=type(todo))
        return msg


class NovelWriter(Role):
    """负责撰写小说内容的角色"""
    name: str = "小说作家"
    profile: str = "NovelWriter"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([GenerateChapterList])  # 修改为监听行动而不是角色
        self.set_actions([WriteChapter()])
        self.chapter_count = 0
        self.total_chapters = 0
        self.completed = False

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: {self.rc.todo.name}")
        todo = self.rc.todo
        
        # 如果已完成所有章节，则返回消息
        if self.completed:
            return Message(
                content="所有章节已完成撰写",
                role=self.profile,
                cause_by=type(todo)
            )
            
        # 初始化章节总数（仅在第一次运行时）
        if self.total_chapters == 0:
            # 解析章节列表，估算章节总数
            # 这里使用简单的方法，可以根据实际章节列表格式优化
            chapter_text = self.context.chapter_list
            # 先尝试计算"第X章"或"章节X"的出现次数
            import re
            chapters = re.findall(r'第\s*\d+\s*章|章节\s*\d+', chapter_text)
            if chapters:
                self.total_chapters = len(chapters)
            else:
                # 如果没找到明确的章节标记，保守估计为20章
                self.total_chapters = 20
            
            logger.info(f"检测到总章节数: {self.total_chapters}")
        
        # 增加章节计数
        self.chapter_count += 1
        
        # 检查是否已达到最大章节数
        if self.chapter_count > self.total_chapters:
            self.completed = True
            return Message(
                content="所有章节已完成撰写",
                role=self.profile,
                cause_by=type(todo)
            )
        
        # 撰写当前章节
        chapter_content = await todo.run(self.context, chapter_num=self.chapter_count)
        
        # 存储章节内容
        self.context.content[str(self.chapter_count)] = chapter_content
        
        # 创建消息
        msg = Message(
            content=f"已完成第{self.chapter_count}章的撰写，内容长度：{len(chapter_content)}字",
            role=self.profile, 
            cause_by=type(todo)
        )
        
        # 在消息中添加是否继续写下一章的状态信息
        if self.chapter_count >= self.total_chapters:
            self.completed = True
            msg.content += "。所有章节已完成撰写。"
        else:
            msg.content += f"。还有{self.total_chapters - self.chapter_count}章待完成。"
            
        return msg


async def write_novel_to_file(context: NovelContext, output_dir: str = "novel_output"):
    """将小说内容写入文件"""
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 写入大纲
    if context.outline:
        with open(f"{output_dir}/outline.md", "w", encoding="utf-8") as f:
            f.write(context.outline)
    else:
        print("警告: 大纲未生成")
    
    # 写入角色设定
    if context.characters:
        with open(f"{output_dir}/characters.md", "w", encoding="utf-8") as f:
            f.write(context.characters)
    else:
        print("警告: 角色未生成")
    
    # 写入剧情
    if context.plot:
        with open(f"{output_dir}/plot.md", "w", encoding="utf-8") as f:
            f.write(context.plot)
    else:
        print("警告: 剧情未生成")
    
    # 写入章节列表
    if context.chapter_list:
        with open(f"{output_dir}/chapter_list.md", "w", encoding="utf-8") as f:
            f.write(context.chapter_list)
    else:
        print("警告: 章节列表未生成")
    
    # 写入各章节内容
    if context.content:
        for chapter_num, content in context.content.items():
            with open(f"{output_dir}/chapter_{chapter_num}.md", "w", encoding="utf-8") as f:
                f.write(content)
    else:
        print("警告: 未生成任何章节内容")
    
    # 写入完整小说（合并所有章节）
    with open(f"{output_dir}/full_novel.md", "w", encoding="utf-8") as f:
        f.write("# 小说全文\n\n")
        
        if context.outline:
            f.write(f"## 大纲\n\n{context.outline}\n\n")
        
        if context.characters:
            f.write(f"## 角色\n\n{context.characters}\n\n")
        
        # 添加所有章节
        if context.content:
            for i in range(1, len(context.content) + 1):
                chapter_num = str(i)
                if chapter_num in context.content:
                    f.write(f"## 第{chapter_num}章\n\n")
                    f.write(f"{context.content[chapter_num]}\n\n")


def main(
    idea: str = "一个关于人工智能觉醒的科幻小说",
    max_chapters: int = 3,
    output_dir: str = "novel_output",
):
    """
    运行多Agent小说创作系统
    
    参数：
        idea: 小说创作的核心创意
        max_chapters: 最大生成章节数
        output_dir: 小说输出目录
    """
    print(f"开始创作小说，主题：{idea}")
    context = NovelContext()
    
    # 创建角色
    outline_generator = OutlineGenerator(context=context)
    character_designer = CharacterDesigner(context=context)
    plot_creator = PlotCreator(context=context)
    chapter_list_generator = ChapterListGenerator(context=context)
    novel_writer = NovelWriter(context=context)
    
    # 构建团队
    team = Team(
        context=context,
    )
    
    # 添加团队成员
    team.hire([
        outline_generator,
        character_designer,
        plot_creator,
        chapter_list_generator,
        novel_writer,
    ])
    
    # 启动创作流程
    team.run_project(idea=idea)  # 首先发布任务需求
    
    # 运行足够的轮次以完成整个小说
    asyncio.run(team.run(n_round=max_chapters + 4))  # +4 是为了前面的4个角色
    
    # 保存小说到文件
    asyncio.run(write_novel_to_file(context, output_dir))
    
    print(f"小说创作完成，输出目录：{output_dir}")
    return "小说创作完成"


if __name__ == "__main__":
    fire.Fire(main)
