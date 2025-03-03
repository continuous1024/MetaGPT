from metagpt.context import Context
from typing import Dict, Optional


class NovelContext(Context):
    """小说写作上下文，存储整个小说创作过程中的信息"""
    outline: Optional[str] = None
    characters: Optional[str] = None
    plot: Optional[str] = None
    chapter_list: Optional[str] = None
    content: Dict[str, str] = {}
