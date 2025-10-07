"""
API Key Manager MCP Server

Provides secure API key management and multi-provider AI routing through MCP protocol.
"""

import json
import asyncio
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from pydantic import AnyUrl

from .tools import (
    get_manager,
    get_validator,
    get_tracker,
    get_router
)
from .resources import (
    get_providers_resource,
    get_usage_stats_resource
)
from .config import ensure_files_exist


# Initialize MCP server
app = Server("api-key-manager")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available MCP resources"""
    return [
        Resource(
            uri=AnyUrl("api://providers"),
            name="AI Providers Configuration",
            mimeType="application/json",
            description="List of available AI providers with configuration and status"
        ),
        Resource(
            uri=AnyUrl("api://usage"),
            name="API Usage Statistics",
            mimeType="application/json",
            description="Current API usage statistics and cost tracking"
        ),
        Resource(
            uri=AnyUrl("api://routing"),
            name="Routing Configuration",
            mimeType="application/json",
            description="AI provider routing configuration and recommendations"
        )
    ]


@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read a resource by URI"""
    uri_str = str(uri)

    if uri_str == "api://providers":
        return get_providers_resource()

    elif uri_str == "api://usage":
        return get_usage_stats_resource()

    elif uri_str == "api://routing":
        router = get_router()
        recommendations = router.get_routing_recommendations()
        return json.dumps(recommendations, indent=2)

    else:
        raise ValueError(f"Unknown resource URI: {uri}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="add_api_key",
            description="Add or update an API key for a provider",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Provider name (anthropic, openai, google, local)",
                        "enum": ["anthropic", "openai", "google", "local"]
                    },
                    "api_key": {
                        "type": "string",
                        "description": "API key to store (optional if using env_var)"
                    },
                    "env_var": {
                        "type": "string",
                        "description": "Environment variable containing the key (optional)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description for the key"
                    },
                    "expiration_date": {
                        "type": "string",
                        "description": "Optional expiration date (ISO format)"
                    }
                },
                "required": ["provider"]
            }
        ),
        Tool(
            name="remove_api_key",
            description="Remove an API key for a provider",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Provider name"
                    }
                },
                "required": ["provider"]
            }
        ),
        Tool(
            name="rotate_key",
            description="Rotate an API key for a provider",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Provider name"
                    },
                    "new_api_key": {
                        "type": "string",
                        "description": "New API key (optional if using env_var)"
                    },
                    "env_var": {
                        "type": "string",
                        "description": "Environment variable with new key (optional)"
                    }
                },
                "required": ["provider"]
            }
        ),
        Tool(
            name="list_api_keys",
            description="List all configured API keys (without revealing actual keys)",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Include metadata in response (default: true)"
                    }
                }
            }
        ),
        Tool(
            name="validate_key",
            description="Validate an API key for a provider",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Provider name"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "API key to validate (optional, validates stored key if not provided)"
                    }
                },
                "required": ["provider"]
            }
        ),
        Tool(
            name="validate_all_keys",
            description="Validate all stored API keys",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_usage",
            description="Get API usage statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Filter by provider (optional)"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days for recent stats (default: 30)"
                    }
                }
            }
        ),
        Tool(
            name="estimate_cost",
            description="Estimate cost for an API request",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Provider name"
                    },
                    "input_tokens": {
                        "type": "integer",
                        "description": "Estimated input tokens"
                    },
                    "output_tokens": {
                        "type": "integer",
                        "description": "Estimated output tokens"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model name (optional)"
                    }
                },
                "required": ["provider", "input_tokens", "output_tokens"]
            }
        ),
        Tool(
            name="check_budget",
            description="Check budget status and limits",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="route_request",
            description="Route a request to the best available provider",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_type": {
                        "type": "string",
                        "description": "Type of task",
                        "enum": [
                            "code_generation",
                            "code_review",
                            "embeddings",
                            "analysis",
                            "chat",
                            "summarization",
                            "data_extraction"
                        ]
                    },
                    "preferred_provider": {
                        "type": "string",
                        "description": "Preferred provider (optional)"
                    },
                    "model": {
                        "type": "string",
                        "description": "Specific model (optional)"
                    },
                    "enable_fallback": {
                        "type": "boolean",
                        "description": "Enable fallback to other providers (default: true)"
                    }
                },
                "required": ["task_type"]
            }
        ),
        Tool(
            name="get_routing_recommendations",
            description="Get routing recommendations and warnings",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_provider_stats",
            description="Get detailed statistics about all providers",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="track_request",
            description="Track an API request for usage statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Provider name"
                    },
                    "input_tokens": {
                        "type": "integer",
                        "description": "Input tokens used"
                    },
                    "output_tokens": {
                        "type": "integer",
                        "description": "Output tokens used"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model used"
                    },
                    "success": {
                        "type": "boolean",
                        "description": "Whether request was successful (default: true)"
                    }
                },
                "required": ["provider", "input_tokens", "output_tokens", "model"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls"""
    manager = get_manager()
    validator = get_validator()
    tracker = get_tracker()
    router = get_router()

    try:
        # Key management tools
        if name == "add_api_key":
            result = manager.add_key(**arguments)

        elif name == "remove_api_key":
            result = manager.remove_key(arguments["provider"])

        elif name == "rotate_key":
            result = manager.rotate_key(**arguments)

        elif name == "list_api_keys":
            include_metadata = arguments.get("include_metadata", True)
            result = manager.list_keys(include_metadata)

        # Validation tools
        elif name == "validate_key":
            result = validator.validate_key(**arguments)

        elif name == "validate_all_keys":
            result = validator.validate_all_keys()

        # Usage tracking tools
        elif name == "get_usage":
            result = tracker.get_usage_stats(**arguments)

        elif name == "estimate_cost":
            result = tracker.estimate_cost(**arguments)

        elif name == "check_budget":
            result = tracker.check_budget()

        elif name == "track_request":
            result = tracker.track_request(**arguments)

        # Routing tools
        elif name == "route_request":
            result = router.route_request(**arguments)

        elif name == "get_routing_recommendations":
            result = router.get_routing_recommendations()

        elif name == "get_provider_stats":
            result = router.get_provider_stats()

        else:
            result = {
                "success": False,
                "error": f"Unknown tool: {name}"
            }

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }, indent=2)
        )]


async def main():
    """Run the MCP server"""
    # Ensure config files exist
    ensure_files_exist()

    # Run the server
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
