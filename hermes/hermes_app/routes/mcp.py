"""
hermes_app/routes/mcp.py — MCP server routes.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from hermes_app.config import settings
from hermes_app.guardrails import GuardrailsManager

logger = logging.getLogger("hermes")

router = APIRouter(prefix="/mcp", tags=["MCP"])


class MCPInvokeRequest(BaseModel):
    """MCP invocation request."""
    server: str = Field(..., description="MCP server name")
    tool: str = Field(..., description="Tool to invoke")
    params: dict = Field(default_factory=dict, description="Tool parameters")


class MCPInvokeResponse(BaseModel):
    """MCP invocation response."""
    status: str
    server: str
    tool: str
    result: dict = Field(default_factory=dict)
    error: Optional[str] = None


def get_guardrails(request: Request) -> GuardrailsManager:
    """Get guardrails from app state."""
    return request.app.state.guardrails


@router.post(
    "/invoke",
    response_model=MCPInvokeResponse,
    summary="Invoke MCP tool",
    description="Invoke a tool on an MCP server with guardrail validation.",
)
async def invoke_mcp(
    request: MCPInvokeRequest,
    guardrails: GuardrailsManager = Depends(get_guardrails),
) -> MCPInvokeResponse:
    """Invoke an MCP tool with guardrails."""
    
    # Validate MCP server is allowed
    if not guardrails.is_mcp_server_allowed(request.server):
        logger.warning(f"[Guardrails] Blocked MCP server: {request.server}")
        return MCPInvokeResponse(
            status="blocked",
            server=request.server,
            tool=request.tool,
            error=f"MCP server '{request.server}' is not allowed",
        )
    
    # In production, this would actually call the MCP server
    # For now, simulate the call
    logger.info(f"[MCP] Invoking {request.server}.{request.tool}")
    
    return MCPInvokeResponse(
        status="completed",
        server=request.server,
        tool=request.tool,
        result={"message": "MCP call simulated"},
    )


@router.get(
    "/servers",
    summary="List allowed MCP servers",
)
async def list_mcp_servers(
    request: Request,
) -> dict:
    """List allowed MCP servers."""
    guardrails = request.app.state.guardrails
    
    return {
        "allowed_servers": list(guardrails.allowed_mcp_servers),
        "blocked_servers": list(guardrails.blocked_mcp_servers),
    }
