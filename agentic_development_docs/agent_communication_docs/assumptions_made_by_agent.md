# Assumptions — 2025-10-30

- Users will authorise FileVyasa to access only explicit directories; system locations (~/Library, /System) remain out-of-scope for automation unless future policy rules expand coverage.
- macOS is the primary deployment target through V2; Linux and Windows support will be validated during V3 packaging work.
- Constella library will be available as a local dependency during early development; packaging to PyPI is not required until broader distribution phases.