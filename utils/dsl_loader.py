import os
import re
from typing import Dict, Any
from pathlib import Path


class DSLTemplateLoader:
    """Load and process Kotlin DSL templates from files."""

    def __init__(self, templates_dir: str = "test_data/dsl_templates"):
        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            raise FileNotFoundError(f"DSL templates directory not found: {templates_dir}")

    def load_template(self, template_name: str, **kwargs) -> str:
        """
        Load a DSL template and substitute variables.

        Args:
            template_name: Name of the template file (without .kts extension)
            **kwargs: Variables to substitute in the template

        Returns:
            Processed DSL content
        """
        template_path = self.templates_dir / f"{template_name}.kts"

        if not template_path.exists():
            available = [f.stem for f in self.templates_dir.glob("*.kts")]
            raise FileNotFoundError(
                f"Template '{template_name}' not found. Available: {available}"
            )

        # Read template content
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Substitute variables using Python string formatting
        # try:
        #     test = content.format(**kwargs)
        #     return test
        # except KeyError as e:
        #     raise ValueError(f"Missing template variable: {e}")

    def load_parametrized_template(self, template_name: str, parameters: Dict[str, Any]) -> str:
        """Load template with complex parameter substitution."""
        content = self.load_template(template_name, **parameters)

        # Handle special cases like repeated blocks
        if 'build_count' in parameters:
            content = self._generate_multiple_builds(content, parameters['build_count'])

        return content

    def _generate_multiple_builds(self, template: str, build_count: int) -> str:
        """Generate multiple build configurations from template."""
        # Look for build template markers in the DSL
        build_template_pattern = r'// BUILD_TEMPLATE_START(.*?)// BUILD_TEMPLATE_END'
        build_template = re.search(build_template_pattern, template, re.DOTALL)

        if not build_template:
            return template

        template_content = build_template.group(1)
        builds = []
        build_declarations = []

        for i in range(build_count):
            build_name = f"Build{i + 1}"
            build_declarations.append(f"    buildType({build_name})")

            # Substitute variables in template
            build_content = template_content.format(
                build_name=build_name,
                build_number=i + 1,
                build_description=f"Automated build configuration {i + 1}"
            )
            builds.append(build_content)

        # Replace template markers with generated content
        result = re.sub(build_template_pattern, '\n'.join(builds), template, flags=re.DOTALL)
        result = result.replace('// BUILD_DECLARATIONS', '\n'.join(build_declarations))

        return result

    def list_available_templates(self) -> list:
        """List all available DSL templates."""
        return [f.stem for f in self.templates_dir.glob("*.kts")]