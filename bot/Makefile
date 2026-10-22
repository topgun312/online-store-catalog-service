# Contains basic auxiliary commands for working with a project.

UV := uv run

# run linters
lint:
	$(UV) isort .
	$(UV) black .
	$(UV) ruff check . --config=pyproject.toml --fix
