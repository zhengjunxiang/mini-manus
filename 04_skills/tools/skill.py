"""Skill 工具 - 加载和管理 Skills"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import httpx

from .base import BaseTool


def clone_skill_from_github(repo_url: str, target_dir: Path) -> dict[str, Any] | None:
    if "github.com" in repo_url:
        parts = repo_url.rstrip("/").split("/")
        repo = f"{parts[-2]}/{parts[-1]}"
    else:
        repo = repo_url

    api_url = f"https://api.github.com/repos/{repo}"

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(api_url)
            if resp.status_code != 200:
                return None

            repo_info = resp.json()
            clone_url = repo_info.get("clone_url", "")

            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(target_dir)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return None

            return load_skill_from_file(target_dir)

    except Exception:
        return None


def load_skill_from_file(skill_path: Path) -> dict[str, Any] | None:
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return None

    content = skill_md.read_text()

    name = skill_path.name
    description = ""
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            body = parts[2].strip()

            for line in frontmatter.split("\n"):
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip('"').strip("'")

    return {
        "name": name,
        "description": description,
        "body": body,
        "path": str(skill_path),
    }


def discover_skills(skills_dir: Path) -> list[dict[str, Any]]:
    skills = []

    if not skills_dir.exists():
        return skills

    for item in skills_dir.iterdir():
        if item.is_dir():
            skill = load_skill_from_file(item)
            if skill:
                skills.append(skill)

    return skills


class SkillTool(BaseTool):
    def __init__(self):
        self.skills_dir = Path(__file__).parent.parent.parent / ".claude" / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_skills: dict[str, dict] = {}

    @property
    def name(self) -> str:
        return "skill"

    @property
    def description(self) -> str:
        return "Manage skills: install from GitHub, list installed skills, load a skill's instructions."

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: install, list, load, create",
                    "enum": ["install", "list", "load", "create"],
                },
                "repo_url": {
                    "type": "string",
                    "description": "GitHub repo URL for install",
                },
                "skill_name": {
                    "type": "string",
                    "description": "Name of skill to load or create",
                },
                "skill_content": {
                    "type": "string",
                    "description": "Skill content (markdown) for create",
                },
            },
            "required": ["action"],
        }

    def execute(self, **kwargs) -> tuple[bool, str]:
        action = kwargs.get("action", "")

        if action == "install":
            return self._install_skill(kwargs)
        elif action == "list":
            return self._list_skills(kwargs)
        elif action == "load":
            return self._load_skill(kwargs)
        elif action == "create":
            return self._create_skill(kwargs)
        else:
            return False, f"Unknown action: {action}"

    def _install_skill(self, kwargs: dict) -> tuple[bool, str]:
        repo_url = kwargs.get("repo_url", "")
        if not repo_url:
            return False, "Error: repo_url is required for install"

        with tempfile.TemporaryDirectory() as tmpdir:
            skill = clone_skill_from_github(repo_url, Path(tmpdir))

            if not skill:
                return False, f"Failed to install skill from {repo_url}"

            skill_name = skill["name"]
            target_dir = self.skills_dir / skill_name

            if target_dir.exists():
                shutil.rmtree(target_dir)

            shutil.move(Path(tmpdir) / skill_name, target_dir)

            self._loaded_skills[skill_name] = skill
            return False, f"Skill '{skill_name}' installed successfully!"

    def _list_skills(self, kwargs: dict) -> tuple[bool, str]:
        skills = discover_skills(self.skills_dir)

        if not skills:
            return False, "No skills installed. Use 'install' action to add skills."

        result = []
        for s in skills:
            result.append(f"- {s['name']}: {s['description']}")

        return False, "Installed skills:\n" + "\n".join(result)

    def _load_skill(self, kwargs: dict) -> tuple[bool, str]:
        skill_name = kwargs.get("skill_name", "")
        if not skill_name:
            return False, "Error: skill_name is required for load"

        skill_path = self.skills_dir / skill_name
        if not skill_path.exists():
            return False, f"Skill '{skill_name}' not found."

        skill = load_skill_from_file(skill_path)
        if not skill:
            return False, f"Failed to load skill '{skill_name}'"

        self._loaded_skills[skill_name] = skill
        return False, f"Skill '{skill_name}' loaded!\n\nInstructions:\n{skill['body']}"

    def _create_skill(self, kwargs: dict) -> tuple[bool, str]:
        skill_name = kwargs.get("skill_name", "")
        content = kwargs.get("skill_content", "")

        if not skill_name or not content:
            return False, "Error: skill_name and skill_content are required for create"

        skill_dir = self.skills_dir / skill_name
        skill_dir.mkdir(exist_ok=True)

        # 生成 YAML frontmatter
        frontmatter = f"""---
name: {skill_name}
description: A custom skill
version: 1.0.0
---

{content}"""

        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(frontmatter)

        return False, f"Skill '{skill_name}' created at {skill_dir}"
