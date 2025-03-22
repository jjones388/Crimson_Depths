from collections import deque
from ..config import MAX_MESSAGES

class MessageLog:
    def __init__(self, max_messages=MAX_MESSAGES):
        self.messages = deque(maxlen=max_messages)
    
    def add_message(self, message, color=(255, 255, 255)):
        # Ensure message is a string
        self.messages.append((str(message), color))
