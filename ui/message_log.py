from collections import deque, namedtuple
from config import MAX_MESSAGES

# Define a Message namedtuple to store text and color
Message = namedtuple('Message', ['text', 'color'])

class MessageLog:
    def __init__(self, max_messages=MAX_MESSAGES):
        self.messages = deque(maxlen=max_messages)
    
    def add_message(self, text, color=(255, 255, 255)):
        # Create a Message object and add it to the log
        self.messages.append(Message(str(text), color))
