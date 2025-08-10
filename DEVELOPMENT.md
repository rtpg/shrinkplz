# Development notes


## Releasing

(TODO: script this up when we've figured it all out)

- Set the version number properly in `pyproject.toml`
- Set the changelog entry correctly
- `rm -r dist`
- `uv build`
- `twine check dist/*` 
- `twine upload dist/*`
- Post release: set the version number to next `.dev`

