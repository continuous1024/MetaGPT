import asyncio
from typing import List

from metagpt.actions import Action, UserRequirement
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.const import MESSAGE_ROUTE_TO_NONE
from metagpt.environment import Environment
from metagpt.context import Context


class AgentAAction(Action):

    def split_10_subtask(self, content):
        return list(map(str, range(1, 11)))

    async def run(
        self, with_messages: List[Message] = None, **kwargs
    ) -> List[str]:
        subtasks: List[str] = self.split_10_subtask(with_messages[0].content)
        print(subtasks)
        return subtasks


class AgentA(Role):

    name: str = "A"
    profile: str = "AgentA"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Initialize actions specific to the Architect role
        self.set_actions([AgentAAction])  # 由于智能体只有1种action，所以不用改写_think函数。

        # 订阅消息
        self._watch({UserRequirement})  # UserRequirement是Message缺省的cause_by的值

    async def _act(self) -> Message:
        print("AgentA._act called")
        subtasks = await self.rc.todo.run(self.rc.history)
        print("AgentA got subtasks:", subtasks)
        for i in subtasks:
            print('send subtask: ', i)
            self.rc.env.publish_message(
                Message(content=i, cause_by=AgentAAction))
        print("AgentA._act completed")
        return Message(content="dummy message", send_to=MESSAGE_ROUTE_TO_NONE)


class AgentBAction(Action):
    async def run(
        self, with_messages: List[Message] = None, **kwargs
    ) -> Message:
        print("AgentB received message:", with_messages, kwargs)
        return Message(content=with_messages[0].content, cause_by=AgentBAction)


class AgentB(Role):

    name: str = "B"
    profile: str = "AgentB"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Initialize actions specific to the Architect role
        self.set_actions([AgentBAction])  # 由于智能体只有1种action，所以不用改写_think函数。

        # 订阅消息
        self._watch({AgentAAction, AgentDAction})
        

class AgentCAction(Action):
    async def run(
        self, with_messages: List[Message] = None, **kwargs
    ) -> Message:
        print("AgentC received message:", with_messages, kwargs)
        return Message(content=with_messages[0].content, cause_by=AgentCAction)


class AgentC(Role):

    name: str = "C"
    profile: str = "AgentC"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Initialize actions specific to the Architect role
        self.set_actions([AgentCAction])  # 由于智能体只有1种action，所以不用改写_think函数。

        # 订阅消息
        self._watch({AgentBAction})


class AgentDAction(Action):
    async def run(
        self, with_messages: List[Message] = None, **kwargs
    ) -> Message:
        print("AgentD received message:", with_messages, kwargs)
        return Message(content=with_messages[0].content, cause_by=AgentDAction)


class AgentD(Role):

    name: str = "D"
    profile: str = "AgentD"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Initialize actions specific to the Architect role
        self.set_actions([AgentDAction])  # 由于智能体只有1种action，所以不用改写_think函数。

        # 订阅消息
        self._watch({AgentCAction})


async def main():
    context = Context()  # Load config2.yaml
    print("Created context")
    env = Environment(context=context)
    print("Created environment")    
    # Check if roles are initialized properly
    agentA = AgentA()
    agentB = AgentB()
    agentC = AgentC()
    agentD = AgentD()

    print("Adding roles to environment...")
    env.add_roles([agentA, agentB, agentC, agentD])
    print("Publishing initial message...")
    print(f"Current env.is_idle: {env.is_idle}")
    initial_message = Message(content='New user requirements', send_to=agentA)
    env.publish_message(initial_message)
    print(agentA.is_idle)
    print(f"Current env.is_idle: {env.is_idle}")
    print("Starting environment loop...")
    while not env.is_idle:  # env.is_idle要等到所有Agent都没有任何新消息要处理后才会为True
        print("Running environment step...")
        await env.run()


if __name__ == "__main__":
    asyncio.run(main())
