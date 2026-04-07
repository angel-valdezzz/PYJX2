from setuptools import setup, find_packages

setup(
    name="pyjx2",
    version="0.1.0",
    description="Jira/Xray automation tool with CLI, TUI, and scripting API",
    author="pyjx2",
    packages=find_packages(),
    include_package_data=True,
    package_data={"pyjx2": ["infrastructure/config/schema.json"]},
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.28",
        "typer>=0.9",
        "rich>=13",
        "textual>=0.40",
        "toml>=0.10",
        "jsonschema>=4",
    ],
    entry_points={
        "console_scripts": [
            "pyjx2=pyjx2.cli.app:app",
        ],
    },
)
