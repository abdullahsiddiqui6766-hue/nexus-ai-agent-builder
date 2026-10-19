from abc import ABC, abstractmethod

from services.groq_client import GroqClient


class BaseAgent(ABC):
    """Base class shared by all AI agents."""

    def __init__(
        self,
        name: str,
        groq_client: GroqClient,
        system_prompt: str,
    ) -> None:
        if not name.strip():
            raise ValueError("Agent name cannot be empty.")

        if not system_prompt.strip():
            raise ValueError("System prompt cannot be empty.")

        self.name = name
        self.groq_client = groq_client
        self.system_prompt = system_prompt

    @abstractmethod
    def run(self, task: str) -> str:
        """Execute the agent's task."""
        raise NotImplementedError

    def generate(self, task: str) -> str:
        """Generate a response using the shared Groq client."""

        if not task.strip():
            raise ValueError("Task cannot be empty.")

        return self.groq_client.generate(
            system_prompt=self.system_prompt,
            user_prompt=task,
        )