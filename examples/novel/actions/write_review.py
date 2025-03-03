from typing import Dict

from metagpt.actions import Action
from metagpt.utils.common import OutputParser

NOVEL_COMMON_PROMPT = """
You are now a seasoned expert in the field of novel writing.
We need you to write a novel with the topic "{topic}".
"""

NOVEL_DIRECTORY_PROMPT = (
    NOVEL_COMMON_PROMPT
    + """
Please provide the specific table of contents for this novel, strictly following the following requirements:
1. The output must be strictly in the specified language, {language}.
2. Answer strictly in the dictionary format like {{"title": "xxx", "directory": [{{"dir 1": ["sub dir 1", "sub dir 2"]}}, {{"dir 2": ["sub dir 3", "sub dir 4"]}}]}}.
3. The directory should be as specific and sufficient as possible, with a primary and secondary directory.The secondary directory is in the array.
4. Do not have extra spaces or line breaks.
5. Each directory title has practical significance.
"""
)

NOVEL_CONTENT_PROMPT = (
    NOVEL_COMMON_PROMPT
    + """
Now I will give you the module directory titles for the topic. 
Please output the detailed principle content of this title in detail. 

The module directory titles for the topic is as follows:
{directory}

Strictly limit output according to the following requirements:
1. Follow the Markdown syntax format for layout.
2. The output must be strictly in the specified language, {language}.
3. Do not have redundant output, including concluding remarks.
4. Strict requirement not to output the topic "{topic}".
5. 章节内容应该符合章节列表中的描述
6. 包含丰富的场景描写、人物对话和内心活动
7. 保持3000-5000字的篇幅
8. 注意人物语言和行为的一致性
9. 适当设置悬念，引导读者阅读下一章节
10. 保持叙述风格的连贯性
"""
)

class WriteNovelDirectory(Action):
    """Action class for writing tutorial directories.

    Args:
        name: The name of the action.
        language: The language to output, default is "Chinese".
    """

    name: str = "WriteNovelDirectory"
    language: str = "Chinese"

    async def run(self, topic: str, *args, **kwargs) -> Dict:
        """Execute the action to generate a tutorial directory according to the topic.

        Args:
            topic: The tutorial topic.

        Returns:
            the tutorial directory information, including {"title": "xxx", "directory": [{"dir 1": ["sub dir 1", "sub dir 2"]}]}.
        """
        prompt = NOVEL_DIRECTORY_PROMPT.format(topic=topic, language=self.language)
        resp = await self._aask(prompt=prompt)
        return OutputParser.extract_struct(resp, dict)


class WriteNovelContent(Action):
    """Action class for writing tutorial content.

    Args:
        name: The name of the action.
        directory: The content to write.
        language: The language to output, default is "Chinese".
    """

    name: str = "WriteNovelContent"
    directory: dict = dict()
    language: str = "Chinese"

    async def run(self, topic: str, *args, **kwargs) -> str:
        """Execute the action to write document content according to the directory and topic.

        Args:
            topic: The tutorial topic.

        Returns:
            The written tutorial content.
        """
        prompt = NOVEL_CONTENT_PROMPT.format(topic=topic, language=self.language, directory=self.directory)
        return await self._aask(prompt=prompt)
