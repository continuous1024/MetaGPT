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
        self.set_actions([AgentAAction])
        self._watch({UserRequirement})
        self.subtasks = None
        self.current_task_index = 0
        self._watch({UserRequirement, AgentBAction})

    async def _act(self) -> Message:
        print("AgentA._act called")
        
        # 首次运行，获取所有子任务
        if self.subtasks is None:
            self.subtasks = await self.rc.todo.run(self.rc.history)
            print("AgentA got subtasks:", self.subtasks)
        
        # 检查最新消息是否为任务完成消息
        latest_msg = self.rc.history[-1] if self.rc.history else None
        print("latest_msg", latest_msg)
        if latest_msg and latest_msg.content == "处理完成" and self.current_task_index < len(self.subtasks):
            # 发送下一个子任务
            current_task = self.subtasks[self.current_task_index]
            print('send subtask: ', current_task)
            self.rc.env.publish_message(
                Message(content=current_task, cause_by=AgentAAction))
            self.current_task_index += 1
        # 首次运行时发送第一个任务
        elif self.current_task_index == 0 and len(self.rc.history) == 1:
            current_task = self.subtasks[self.current_task_index]
            print('send first subtask: ', current_task)
            self.rc.env.publish_message(
                Message(content=current_task, cause_by=AgentAAction))
            self.current_task_index += 1
            
        return Message(content="dummy message", send_to=MESSAGE_ROUTE_TO_NONE)


class AgentBAction(Action):
    async def run(
        self, with_messages: List[Message] = None, **kwargs
    ) -> Message:
        # 获取最新的消息
        content = with_messages[-1].content
        print("AgentB received message:", content)
        
        # 检查是否已经包含循环计数
        if "循环次数:" in content:
            parts = content.split("循环次数:")
            base_content = parts[0].strip()
            count = int(parts[1].strip())
            
            # 如果已经循环了3次，则不再继续处理
            if count >= 3:
                print("AgentB: 已达到最大循环次数，停止处理")
                return Message(content="处理完成", send_to=MESSAGE_ROUTE_TO_NONE)
            
            # 增加循环计数
            new_count = count + 1
            new_content = f"B processed: {base_content} 循环次数:{new_count}"
        else:
            # 首次处理（来自AgentA的新任务），添加循环计数
            new_content = f"B processed: {content} 循环次数:1"
        
        return Message(content=new_content, cause_by=AgentBAction)


class AgentB(Role):

    name: str = "B"
    profile: str = "AgentB"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_actions([AgentBAction])
        # 订阅来自Agent A和Agent D的消息
        self._watch({AgentAAction, AgentDAction})


class AgentCAction(Action):
    async def run(
        self, with_messages: List[Message] = None, **kwargs
    ) -> Message:
        # 获取最新的消息
        content = with_messages[-1].content
        print("AgentC received message:", content)
        
        # 保持循环计数不变，只处理内容
        if "循环次数:" in content:
            parts = content.split("循环次数:")
            base_content = parts[0].strip()
            count = parts[1].strip()
            new_content = f"C processed: {base_content} 循环次数:{count}"
        else:
            new_content = f"C processed: {content}"
        
        return Message(content=new_content, cause_by=AgentCAction)


class AgentC(Role):

    name: str = "C"
    profile: str = "AgentC"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_actions([AgentCAction])
        # 订阅来自Agent B的消息
        self._watch({AgentBAction})


class AgentDAction(Action):
    async def run(
        self, with_messages: List[Message] = None, **kwargs
    ) -> Message:
        # 获取最新的消息
        content = with_messages[-1].content
        print("AgentD received message:", content)
        
        # 保持循环计数不变，只处理内容
        if "循环次数:" in content:
            parts = content.split("循环次数:")
            base_content = parts[0].strip()
            count = parts[1].strip()
            new_content = f"D processed: {base_content} 循环次数:{count}"
        else:
            new_content = f"D processed: {content}"
        
        return Message(content=new_content, cause_by=AgentDAction)


class AgentD(Role):

    name: str = "D"
    profile: str = "AgentD"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_actions([AgentDAction])
        # 订阅来自Agent C的消息
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
