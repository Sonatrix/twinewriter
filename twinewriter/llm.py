"""Lightweight LLM client factory for TwineWriter.

Provides a single get_llm() function that returns a small wrapper with an
`invoke(messages)` method used by the nodes. The factory inspects environment
variables and instantiates the appropriate langchain chat LLM adapter.
"""

from __future__ import annotations

import os
from typing import Any, List

_LLM_INSTANCE = None


class LLMWrapper:
    def __init__(self, llm: Any):
        self._llm = llm

    def invoke(self, messages: List[Any]) -> Any:
        """Invoke the underlying LLM using the most compatible method available.

        Returns an object with a `content` attribute (string). This matches the
        usage in the nodes which call `response.content`.
        """
        # If the model has an `invoke` method (some adapters expose it), use it
        if hasattr(self._llm, "invoke"):
            return self._llm.invoke(messages)

        # Try calling the model directly (some langchain chat models support __call__)
        try:
            out = self._llm(messages)
            # If the result has content attribute, return directly
            if hasattr(out, "content"):
                return out
            # If it's a plain string, wrap into a simple object
            if isinstance(out, str):

                class _R:
                    pass

                r = _R()
                r.content = out
                return r
        except Exception:
            pass

        # Fallback to generate() -> try to extract text
        if hasattr(self._llm, "generate"):
            gen = self._llm.generate(messages)
            # langchain generation objects vary; attempt common extraction patterns
            text = None
            try:
                # new langchain: gen.generations[0][0].text
                text = gen.generations[0][0].text
            except Exception:
                try:
                    # older shapes: gen.generations[0].text
                    text = gen.generations[0].text
                except Exception:
                    try:
                        text = str(gen)
                    except Exception:
                        text = ""

            class _R2:
                pass

            r2 = _R2()
            r2.content = text or ""
            return r2

        raise RuntimeError(
            "Unable to invoke underlying LLM: no compatible method found"
        )
    
    def stream(self, messages: List[Any]):
        """Stream the underlying LLM response token by token.
        
        Yields chunks of content as they are generated.
        """
        # If the model has a `stream` method, use it
        if hasattr(self._llm, "stream"):
            for chunk in self._llm.stream(messages):
                if hasattr(chunk, "content"):
                    yield chunk.content
                elif isinstance(chunk, str):
                    yield chunk
        else:
            # Fallback to non-streaming invoke
            response = self.invoke(messages)
            yield response.content


def _create_llm_from_config(
    llm_provider: str = "",
    openai_api_key: str = "",
    anthropic_api_key: str = "",
    ollama_model: str = "llama3.2",
    ollama_base_url: str = "http://localhost:11434"
) -> LLMWrapper:
    """Instantiate a langchain chat LLM based on provided configuration.

    Priority:
      1. openai_api_key -> langchain_openai.ChatOpenAI
      2. anthropic_api_key -> langchain_anthropic.ChatAnthropic
      3. llm_provider == "Ollama" -> langchain_ollama.ChatOllama
    """
    temp = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    try:
        # OpenAI
        if openai_api_key:
            from langchain_openai import ChatOpenAI

            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            llm = ChatOpenAI(model=model, temperature=temp, api_key=openai_api_key)
            return LLMWrapper(llm)

        # Anthropic
        if anthropic_api_key:
            from langchain_anthropic import ChatAnthropic

            model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            llm = ChatAnthropic(model=model, temperature=temp, api_key=anthropic_api_key)
            return LLMWrapper(llm)

        # Ollama (local)
        if llm_provider == "Ollama" and ollama_model:
            from langchain_ollama import ChatOllama

            llm = ChatOllama(model=ollama_model, base_url=ollama_base_url, temperature=temp)
            return LLMWrapper(llm)

    except Exception as e:
        # bubble up as runtime error to let callers set state.error
        raise RuntimeError(f"LLM initialization failed: {e}")

    raise RuntimeError(
        "No LLM configured. Provide API key or configure Ollama"
    )


def _create_llm_from_env() -> LLMWrapper:
    """Instantiate a langchain chat LLM based on environment variables.

    Priority:
      1. OPENAI_API_KEY -> langchain_openai.ChatOpenAI
      2. ANTHROPIC_API_KEY -> langchain_anthropic.ChatAnthropic
      3. USE_OLLAMA=true -> langchain_ollama.ChatOllama
    """
    # OpenAI
    try:
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key and openai_key.lower() != "false":
            from langchain_openai import ChatOpenAI

            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            temp = float(os.getenv("LLM_TEMPERATURE", "0.7"))
            llm = ChatOpenAI(model=model, temperature=temp, api_key=openai_key)
            return LLMWrapper(llm)

        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        if anthropic_key and anthropic_key.lower() != "false":
            from langchain_anthropic import ChatAnthropic

            model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            temp = float(os.getenv("LLM_TEMPERATURE", "0.7"))
            llm = ChatAnthropic(model=model, temperature=temp, api_key=anthropic_key)
            return LLMWrapper(llm)

        # Ollama (local)
        if os.getenv("USE_OLLAMA", "").lower() == "true":
            from langchain_ollama import ChatOllama

            model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            temp = float(os.getenv("LLM_TEMPERATURE", "0.7"))
            llm = ChatOllama(model=model_name, base_url=base_url, temperature=temp)
            return LLMWrapper(llm)

    except Exception as e:
        # bubble up as runtime error to let callers set state.error
        raise RuntimeError(f"LLM initialization failed: {e}")

    raise RuntimeError(
        "No LLM configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or USE_OLLAMA=true"
    )


def get_llm(state: dict = None) -> LLMWrapper:
    """Get LLM instance from state configuration or environment variables.
    
    If state is provided with LLM configuration, use that.
    Otherwise, fall back to environment variables with caching.
    """
    # If state has LLM configuration, create from state (no caching)
    if state and state.get("llm_provider"):
        return _create_llm_from_config(
            llm_provider=state.get("llm_provider", ""),
            openai_api_key=state.get("openai_api_key", ""),
            anthropic_api_key=state.get("anthropic_api_key", ""),
            ollama_model=state.get("ollama_model", "llama3.2"),
            ollama_base_url=state.get("ollama_base_url", "http://localhost:11434")
        )
    
    # Fall back to cached environment-based LLM
    global _LLM_INSTANCE
    if _LLM_INSTANCE is None:
        _LLM_INSTANCE = _create_llm_from_env()
    return _LLM_INSTANCE
