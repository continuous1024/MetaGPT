from metagpt.actions import Action


class DesignCharacters(Action):
    """设计小说角色的行动"""
    PROMPT_TEMPLATE: str = """
    根据以下小说大纲，设计详细的角色列表：

    {outline}

    请为每个主要角色提供以下信息：
    1. 角色全名
    2. 角色身份/职业
    3. 年龄和外貌特征
    4. 性格特点
    5. 动机与目标
    6. 背景故事
    7. 与其他角色的关系
    8. 角色弧线（在故事中的成长或变化）

    至少设计3-5个主要角色，以及必要的配角。
    请以结构化形式呈现每个角色的信息。
    """

    name: str = "DesignCharacters"

    async def run(self, outline: str):
        prompt = self.PROMPT_TEMPLATE.format(outline=outline)
        characters = await self._aask(prompt)
        return characters
