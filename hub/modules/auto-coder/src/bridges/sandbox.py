"""Bridge to E2B sandbox infrastructure."""
from pathlib import Path


class SandboxBridge:
    """
    Bridge to tools/agent-sandboxes infrastructure.

    Enables isolated code execution in E2B sandboxes.
    """

    def __init__(self):
        self.sandboxes_path = Path(__file__).parents[5] / "tools" / "agent-sandboxes"

    async def create_sandbox(self, repo_url: str, branch: str) -> str:
        """Create an E2B sandbox for isolated execution."""
        # Bridge to existing obox infrastructure
        # Returns sandbox_id
        pass

    async def run_coder(
        self,
        sandbox_id: str,
        subtask: str,
        context: dict | None = None,
    ) -> dict:
        """Run coder agent in sandbox."""
        # Execute in E2B sandbox
        pass

    async def get_files(self, sandbox_id: str, path: str = "/") -> list[str]:
        """Get files from sandbox."""
        pass

    async def destroy_sandbox(self, sandbox_id: str) -> bool:
        """Destroy a sandbox."""
        pass
