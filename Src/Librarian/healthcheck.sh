#!/bin/sh
# Health check script for Librarian service
# Runs a lightweight subset of critical tests to verify service health

# Run tests in quiet mode with short traceback
pytest Src/Librarian/tests/ --tb=short -q

# Exit code 0 = healthy, non-zero = unhealthy
exit $?

