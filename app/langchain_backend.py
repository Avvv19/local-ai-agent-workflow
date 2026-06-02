"""LangChain backend.

Wraps the local Ollama model in a LangChain `Runnable` pipeline
(prompt -> model -> string). This demonstrates LangChain orchestration while
reusing the exact same prompts the other backends use. Imports are lazy so the
project installs and runs without LangChain unless this backend is selected.

Select it with:  LLM_BACKEND=langchain  (requires `langchain-ollama` + Ollama).
"""
from __future__ import annotations

from . import config
from .llm_client import LLMClient


class LangChainClient(LLMClient):
    def __init__(self, model: str | None = None, host: str | None = None):
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "LangChain backend needs `langchain-ollama`. "
                "Install with: pip install langchain-ollama"
            ) from exc

        self._llm = ChatOllama(
            model=model or config.OLLAMA_MODEL,
            base_url=host or config.OLLAMA_HOST,
            temperature=0.0,
        )
        self._template = ChatPromptTemplate.from_messages(
            [("system", "{system}"), ("human", "{prompt}")]
        )
        # LangChain Expression Language pipeline
        self._chain = self._template | self._llm | StrOutputParser()

    def generate(self, prompt: str, system: str | None = None,
                 json_mode: bool = False) -> str:
        return self._chain.invoke({"prompt": prompt, "system": system or ""})
