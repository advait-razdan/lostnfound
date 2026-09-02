#!/usr/bin/env bash
#
# Local email-testing harness. Configures Django to write every outgoing email
# to .eml files under ./sent_emails/ instead of hitting real SMTP/OAuth, then
# runs whatever command you pass (defaults to the dev server).
#
# Usage:
#   ./local_email_test.sh                       # run the dev server
#   ./local_email_test.sh <any manage.py args>  # e.g. simulate a student email
#
# Examples:
#   ./local_email_test.sh
#   ./local_email_test.sh simulate_student_email \
#       --from "Priya Sharma <psharma@tisb.ac.in>" \
#       --subject "Lost blue Hydroflask water bottle" \
#       --body "Left it in the science block on Tuesday."
#
set -euo pipefail
cd "$(dirname "$0")"

# --- Local email config: file-based backend, no real credentials needed ------
export EMAIL_BACKEND="django.core.mail.backends.filebased.EmailBackend"
export EMAIL_FILE_PATH="$(pwd)/sent_emails"
export LF_EMAIL_ADDRESS="trace@tisb.local"
export EMAIL_HOST_USER="trace@tisb.local"
export DEFAULT_FROM_EMAIL="trace@tisb.local"
# Where broadcasts go (BCC recipients). Override by exporting before calling.
export LF_BROADCAST_RECIPIENTS="${LF_BROADCAST_RECIPIENTS:-school-all@tisb.local}"

mkdir -p "$EMAIL_FILE_PATH"

# Activate the project venv if present.
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

if [ "$#" -eq 0 ]; then
  echo "Emails will be written to: $EMAIL_FILE_PATH"
  echo "Starting dev server on http://127.0.0.1:8000 ..."
  exec python manage.py runserver
else
  exec python manage.py "$@"
fi
