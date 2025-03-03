import asyncio
from datetime import datetime
from typing import Dict

from metagpt.const import DATA_PATH
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.utils.file import File
from examples.novel.actions.write_review import WriteNovelDirectory, WriteNovelContent


class NovelAssistant(Role):
    """Writer assistant, input one sentence to generate a novel document in markdown format.

    Args:
        name: The name of the role.
        profile: The role profile description.
        goal: The goal of the role.
        constraints: Constraints or requirements for the role.
        language: The language in which the tutorial documents will be generated.
    """

    name: str = "winter"
    profile: str = "Novel Assistant"
    goal: str = "Generate novel"
    constraints: str = "Strictly follow Markdown's syntax, with neat and standardized layout"
    language: str = "Chinese"

    topic: str = ""
    main_title: str = ""
    total_content: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteNovelDirectory(language=self.language)])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _handle_directory(self, titles: Dict) -> Message:
        """Handle the directories for the tutorial document.

        Args:
            titles: A dictionary containing the titles and directory structure,
                    such as {"title": "xxx", "directory": [{"dir 1": ["sub dir 1", "sub dir 2"]}]}

        Returns:
            A message containing information about the directory.
        """
        self.main_title = titles.get("title")
        directory = f"{self.main_title}\n"
        self.total_content += f"# {self.main_title}"
        actions = list(self.actions)
        for first_dir in titles.get("directory"):
            actions.append(WriteNovelContent(language=self.language, directory=first_dir))
            key = list(first_dir.keys())[0]
            directory += f"- {key}\n"
            for second_dir in first_dir[key]:
                directory += f"  - {second_dir}\n"
        self.set_actions(actions)
        self.rc.max_react_loop = len(self.actions)
        return Message()

    async def _act(self) -> Message:
        """Perform an action as determined by the role.

        Returns:
            A message containing the result of the action.
        """
        todo = self.rc.todo
        if type(todo) is WriteNovelDirectory:
            msg = self.rc.memory.get(k=1)[0]
            self.topic = msg.content
            resp = await todo.run(topic=self.topic)
            logger.info(resp)
            return await self._handle_directory(resp)
        resp = await todo.run(topic=self.topic)
        logger.info(resp)
        if self.total_content != "":
            self.total_content += "\n\n\n"
        self.total_content += resp
        return Message(content=resp, role=self.profile)

    async def react(self) -> Message:
        msg = await super().react()
        root_path = DATA_PATH / "novels" / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        await File.write(root_path, f"{self.main_title}.md", self.total_content.encode("utf-8"))
        msg.content = str(root_path / f"{self.main_title}.md")
        return msg


async def main():
    topic = "Write a novel about 玄幻长生"
    role = NovelAssistant(language="Chinese")
    await role.run(topic)


if __name__ == "__main__":
    asyncio.run(main())