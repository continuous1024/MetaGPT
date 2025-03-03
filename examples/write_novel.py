import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.memory import Memory

# 定义常量
OUTLINE_FILE = "outline.md"
VOLUMES_FILE = "volumes.md"
CHAPTER_DIR = "chapters"

PROMPT_TEMPLATE = """
你是一个专业的小说创作助手，请根据以下要求进行创作：
{instruction}
"""

class GenerateOutline(Action):
    """生成小说大纲的Action"""
    async def run(self, instruction: str) -> str:
        prompt = PROMPT_TEMPLATE.format(
            instruction="生成小说大纲，包含：\n"
                        "1. 故事背景\n2. 主要角色\n3. 核心冲突\n4. 主要剧情线\n5. 预期结局"
        )
        rsp = await self._aask(prompt)
        return rsp

class SplitVolumes(Action):
    """将大纲分卷的Action"""
    async def run(self, context: str) -> str:
        prompt = PROMPT_TEMPLATE.format(
            instruction=f"基于以下大纲将小说分为{k}卷，每卷包含核心冲突和主要剧情：\n{context}"
        )
        rsp = await self._aask(prompt)
        return rsp

class WriteChapter(Action):
    """撰写具体章节的Action"""
    def __init__(self, index: int, **kwargs):
        super().__init__(**kwargs)
        self.index = index

    async def run(self, context: str) -> str:
        prompt = PROMPT_TEMPLATE.format(
            instruction=f"根据以下上下文撰写第{self.index}章内容：\n{context}\n"
                        "要求：\n1. 保持剧情连贯\n2. 包含角色互动\n3. 推进冲突发展"
        )
        rsp = await self._aask(prompt)
        return rsp

class ReviewChapter(Action):
    """章节审阅Action"""
    async def run(self, context: str) -> bool:
        print(f"\n=== 第{context['index']}章生成完成 ===")
        print(context['content'])
        choice = input("\n是否通过？(y/n/q) ").lower()
        return choice

class NovelWriter(Role):
    """小说创作主角色"""
    def __init__(
        self,
        mode: str = "auto",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.mode = mode
        self.volume_num = 0
        self.chapter_index = 1
        self._init_action([GenerateOutline, SplitVolumes, WriteChapter])
        self.set_memory(Memory())

    async def _act(self) -> Message:
        todo = self.rc.todo
        
        if isinstance(todo, GenerateOutline):
            instruction = "开始创作一部奇幻小说"
            rsp = await todo.run(instruction)
            self._save_content(OUTLINE_FILE, rsp)
            msg = Message(content=rsp, role=self.profile, cause_by=type(todo))
            
        elif isinstance(todo, SplitVolumes):
            outline = self.get_memories(k=1)[0].content
            rsp = await todo.run(outline)
            self._save_content(VOLUMES_FILE, rsp)
            msg = Message(content=rsp, role=self.profile, cause_by=type(todo))
            
        elif isinstance(todo, WriteChapter):
            context = "\n".join([m.content for m in self.get_memories()])
            rsp = await todo.run(context)
            self._save_chapter(todo.index, rsp)
            msg = Message(
                content={"index": todo.index, "content": rsp},
                role=self.profile,
                cause_by=type(todo)
            )
            
        self.rc.memory.add(msg)
        return msg

    def _save_content(self, filename: str, content: str):
        Path(filename).write_text(content, encoding="utf-8")
        logger.info(f"内容已保存到 {filename}")

    def _save_chapter(self, index: int, content: str):
        Path(CHAPTER_DIR).mkdir(exist_ok=True)
        path = Path(CHAPTER_DIR) / f"chapter_{index}.md"
        path.write_text(content, encoding="utf-8")
        logger.info(f"章节已保存到 {path}")

    async def run_interactive(self):
        """交互式运行模式"""
        print("=== 小说创作开始 ===")
        await self._generate_outline()
        await self._split_volumes()
        
        while True:
            await self._write_chapter()
            if not await self._review_chapter():
                break
            self.chapter_index += 1

    async def run_auto(self):
        """自动运行模式"""
        await self._generate_outline()
        await self._split_volumes()
        
        for _ in range(10):  # 默认生成10章
            await self._write_chapter()
            self.chapter_index += 1

    async def _generate_outline(self):
        self.rc.todo = GenerateOutline()
        await self._act()

    async def _split_volumes(self):
        self.rc.todo = SplitVolumes()
        await self._act()

    async def _write_chapter(self):
        self.rc.todo = WriteChapter(index=self.chapter_index)
        await self._act()

    async def _review_chapter(self) -> bool:
        if self.mode != "interactive":
            return True

        review = ReviewChapter()
        msg = self.rc.memory.get(k=1)[0]
        choice = await review.run(msg.content)
        
        if choice == "q":
            return False
        elif choice == "n":
            await self._adjust_chapter()
        return True

    async def _adjust_chapter(self):
        """调整章节参数"""
        print("\n=== 调整参数 ===")
        new_content = input("请输入修改建议：")
        self.rc.memory.add(Message(content=new_content, role="USER", cause_by=ReviewChapter))

async def main(mode: str = "auto"):
    writer = NovelWriter(mode=mode)
    if mode == "interactive":
        await writer.run_interactive()
    else:
        await writer.run_auto()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["auto", "interactive"], default="auto")
    args = parser.parse_args()
    
    asyncio.run(main(args.mode))