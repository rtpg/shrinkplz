# CHANGELOG

## Unreleased Changes

## 0.1.2 (2025-08-10)

- Add a `--min-test-size` option. Shrinking will be considered complete
  once we hit the mininum test size (in lines).
  
  This defaults to 1 (meaning we don't shrink down to an empty test file).
  This is likely what you want (as empty tests likely look spurious) but 
  might prevent you from seeing that your test fails with empty inputs.
  
- Print out to stderr instead of stdout
- Remove printing of internal data structure during marking

## 0.1.1 (2025-07-15)

- Add licensing information

## 0.1.0 (2025-07-15)

- Initial release

