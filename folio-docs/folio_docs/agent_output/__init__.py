"""Agent-readable documentation emitted by Folio Docs."""

from folio_docs.agent_output.artifacts import AgentArtifacts
from folio_docs.agent_output.llm_output import generate_llms_full_txt, generate_llms_txt

__all__ = ["AgentArtifacts", "generate_llms_full_txt", "generate_llms_txt"]
