# Security

Do not open public issues for secrets, credential leaks, or vulnerabilities.
Report security-sensitive concerns to Wavenumber maintainers through the
private channel used for the affected project.

Public repositories must not commit `.env` files, tokens, private package
credentials, proprietary corpora, or customer data. Local root `.env` files are
acceptable only when they are untracked and ignored by Git. Use `.env.example`
for documented environment variables.
