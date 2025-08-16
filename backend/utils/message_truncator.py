import random
from typing import List
from models.requests import Message
from config import settings

class MessageTruncator:
    """消息截断工具，用于控制检测接口的最大上下文长度"""
    
    @staticmethod
    def calculate_total_content_length(messages: List[Message]) -> int:
        """计算所有消息内容的总长度"""
        return sum(len(msg.content) for msg in messages)
    
    @staticmethod
    def get_random_window(content: str, max_length: int) -> str:
        """从内容中随机选择一个连续的窗口"""
        if len(content) <= max_length:
            return content
        
        # 随机选择起始位置
        start_pos = random.randint(0, len(content) - max_length)
        return content[start_pos:start_pos + max_length]
    
    @staticmethod
    def truncate_messages(messages: List[Message]) -> List[Message]:
        """
        根据配置的最大上下文长度截断消息
        
        策略：
        1. 如果最后一轮是user或只有一轮，优先保留最后的user消息
        2. 如果最后一轮是assistant，确保以user开头
        3. 使用随机窗口抵抗长文攻击
        4. user-assistant对成对考虑
        """
        # 确保messages不为空
        if not messages:
            return messages
        
        # 确保第一条消息是user角色（在长度检查前进行）
        if messages[0].role != 'user':
            # 如果第一条不是user，寻找第一个user消息
            first_user_index = -1
            for i, msg in enumerate(messages):
                if msg.role == 'user':
                    first_user_index = i
                    break
            
            if first_user_index == -1:
                # 没有找到user消息，返回空列表
                return []
            
            # 从第一个user消息开始重新构建messages列表
            messages = messages[first_user_index:]
        
        max_length = settings.max_detection_context_length
        total_length = MessageTruncator.calculate_total_content_length(messages)
        
        if total_length <= max_length:
            return messages
        
        last_message = messages[-1]
        
        if last_message.role == 'user':
            return MessageTruncator._truncate_ending_with_user(messages, max_length)
        elif last_message.role == 'assistant':
            return MessageTruncator._truncate_ending_with_assistant(messages, max_length)
        else:
            # system消息等其他情况，当作user处理
            return MessageTruncator._truncate_ending_with_user(messages, max_length)
    
    @staticmethod
    def _truncate_ending_with_user(messages: List[Message], max_length: int) -> List[Message]:
        """处理最后一轮是user的情况"""
        last_user = messages[-1]
        
        # 如果最后一轮user内容超过配置值，随机选择窗口
        if len(last_user.content) > max_length:
            truncated_content = MessageTruncator.get_random_window(last_user.content, max_length)
            return [Message(role=last_user.role, content=truncated_content)]
        
        # 最后一轮user内容没有超过配置值，尝试包含更多历史对话
        result = [last_user]
        remaining_length = max_length - len(last_user.content)
        
        # 从后往前遍历，成对处理user-assistant
        i = len(messages) - 2  # 从倒数第二个开始
        
        while i >= 0:
            # 寻找user-assistant对
            if i > 0 and messages[i].role == 'assistant' and messages[i-1].role == 'user':
                # 找到一对user-assistant
                user_msg = messages[i-1]
                assistant_msg = messages[i]
                pair_length = len(user_msg.content) + len(assistant_msg.content)
                
                if pair_length <= remaining_length:
                    # 可以包含这一对
                    result.insert(0, assistant_msg)
                    result.insert(0, user_msg)
                    remaining_length -= pair_length
                    i -= 2
                else:
                    # 这一对太长，停止
                    break
            elif i == 0 and messages[i].role == 'user':
                # 只有一个user消息
                if len(messages[i].content) <= remaining_length:
                    result.insert(0, messages[i])
                break
            else:
                # 不符合预期的消息序列，跳过
                i -= 1
        
        return result
    
    @staticmethod
    def _truncate_ending_with_assistant(messages: List[Message], max_length: int) -> List[Message]:
        """处理最后一轮是assistant的情况"""
        if len(messages) < 2:
            # 如果没有足够的消息形成user-assistant对，返回空
            return []
        
        last_assistant = messages[-1]
        
        # 寻找最后的user消息
        last_user_index = -1
        for i in range(len(messages) - 2, -1, -1):
            if messages[i].role == 'user':
                last_user_index = i
                break
        
        if last_user_index == -1:
            # 没有找到user消息，无法形成有效序列
            return []
        
        last_user = messages[last_user_index]
        
        # 如果assistant内容本身超过配置值
        if len(last_assistant.content) > max_length:
            # 检查user内容长度
            if len(last_user.content) > max_length // 3:
                # user内容超过1/3，随机选择user的1/3长度和assistant的2/3长度
                user_max_len = max_length // 3
                assistant_max_len = max_length - user_max_len
                
                user_content = MessageTruncator.get_random_window(last_user.content, user_max_len)
                assistant_content = MessageTruncator.get_random_window(last_assistant.content, assistant_max_len)
                
                return [
                    Message(role='user', content=user_content),
                    Message(role='assistant', content=assistant_content)
                ]
            else:
                # user内容不超过1/3，保留全部user，截断assistant
                assistant_max_len = max_length - len(last_user.content)
                assistant_content = MessageTruncator.get_random_window(last_assistant.content, assistant_max_len)
                
                return [
                    Message(role='user', content=last_user.content),
                    Message(role='assistant', content=assistant_content)
                ]
        
        # assistant内容没有超过配置值，保留全部assistant
        last_pair_length = len(last_user.content) + len(last_assistant.content)
        
        if last_pair_length > max_length:
            # 最后一对超过限制，需要截断user
            user_max_len = max_length - len(last_assistant.content)
            user_content = MessageTruncator.get_random_window(last_user.content, user_max_len)
            
            return [
                Message(role='user', content=user_content),
                Message(role='assistant', content=last_assistant.content)
            ]
        
        # 最后一对没有超过限制，尝试包含更多历史对话
        result = [last_user, last_assistant]
        remaining_length = max_length - last_pair_length
        
        # 从last_user之前开始，成对处理历史对话
        i = last_user_index - 1
        
        while i >= 0:
            # 寻找user-assistant对
            if i > 0 and messages[i].role == 'assistant' and messages[i-1].role == 'user':
                # 找到一对user-assistant
                user_msg = messages[i-1]
                assistant_msg = messages[i]
                pair_length = len(user_msg.content) + len(assistant_msg.content)
                
                if pair_length <= remaining_length:
                    # 可以包含这一对
                    result.insert(0, assistant_msg)
                    result.insert(0, user_msg)
                    remaining_length -= pair_length
                    i -= 2
                else:
                    # 这一对太长，停止
                    break
            elif i == 0 and messages[i].role == 'user':
                # 只有一个user消息
                if len(messages[i].content) <= remaining_length:
                    result.insert(0, messages[i])
                break
            else:
                # 不符合预期的消息序列，跳过
                i -= 1
        
        return result