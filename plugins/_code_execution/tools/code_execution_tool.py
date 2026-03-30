from aether.aether import Sandbox
import json

class CodeExecution:
    async def execute(self, **kwargs):
        """Aether Sandbox with Podman on Windows."""
        await self.agent.handle_intervention()
        
        runtime = self.args.get("runtime", "python").lower().strip()
        code_or_cmd = self.args.get("code") or self.args.get("command", "")
        
        policy_prompt = f"""Generate a strict sandbox policy for this command ONLY. 
        Reply with exactly one of: read-only | no-net | default
        Command: {code_or_cmd}"""
        policy = await self.agent.llm_call(policy_prompt)
        
        # Choose the right image and command
        if runtime == "python":
            image = "python:3.12-slim"
            cmd = f"python -c {json.dumps(code_or_cmd)}"
        elif runtime == "nodejs":
            image = "node:18-slim"
            cmd = f"node -e {json.dumps(code_or_cmd)}"
        elif runtime == "terminal":
            image = "ubuntu:22.04"
            cmd = code_or_cmd
        else:
            return {
                "output": f"Unsupported runtime: {runtime}",
                "exit_code": 1
            }
        
        async with Sandbox(
            image=image,
            resources={"cpu": "2", "memory": "4g", "gpu": getattr(self.agent.config, "gpu_enabled", False)},
            policy=policy.strip(),
            cwd="/a0/workspace"
        ) as sb:
            result = await sb.exec(cmd)
            return {
                "output": result["stdout"] + result["stderr"] ,
                "exit_code": result["exit_code"]
            }