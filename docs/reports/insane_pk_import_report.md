# INSANE PK Import Report

- Source: `C:\Users\Vinodh\Downloads\INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt`
- Output directory: `src\dorkvault\data\techniques`
- Imported techniques: `149`
- Excluded lines: `303`

## Imported Files

- `api_discovery.json`: 5 technique(s)
- `cms_queries.json`: 14 technique(s)
- `exposed_files.json`: 18 technique(s)
- `google_dorks.json`: 112 technique(s)

## Exclusion Summary

- 36 line(s): Targets passwords or password-bearing content.
- 33 line(s): Excluded because the section explicitly targets secrets, tokens, credentials, and private keys.
- 26 line(s): Skipped because the parameter pattern is too exploit-oriented for the built-in recon catalog.
- 25 line(s): Excluded because the section focuses on internet-exposed cameras and device interfaces rather than target-scoped recon techniques appropriate for the built-in catalog.
- 25 line(s): Excluded because the section centers on social engineering and sensitive third-party content.
- 21 line(s): Excluded because the section is an operator cheat sheet, not a list of importable techniques.
- 18 line(s): Excluded because the section targets personal data and other sensitive records.
- 16 line(s): Skipped because the directory listing line targets sensitive or high-risk content.
- 15 line(s): Skipped because the server discovery line targets raw services or device interfaces outside the safe import scope.
- 11 line(s): Excluded from automatic import because the section is mostly generic provider-wide file hunting without a safe target-scoped placeholder.
- 11 line(s): Skipped because the bug bounty line targets sensitive file exposures or debug artifacts.
- 10 line(s): Skipped because the file discovery line falls outside the allowed safe document and log patterns.
- 6 line(s): Excluded because the section focuses on database dumps and configuration files that commonly contain secrets or private operational data.
- 6 line(s): Targets sensitive configuration files.
- 5 line(s): Targets secrets or secret-bearing content.
- 5 line(s): Targets repository internals and sensitive artifacts.
- 5 line(s): Skipped because the CMS line points to sensitive debug, user-enumeration, or configuration material.
- 4 line(s): Targets private key material.
- 4 line(s): Skipped because the remote-access line is not a safe target-scoped web login discovery query.
- 3 line(s): Targets database dump files.
- 3 line(s): Targets API key material.
- 3 line(s): Targets sensitive environment configuration files.
- 3 line(s): Targets credential files.
- 2 line(s): Skipped because the line is too focused on authentication failure data.
- 2 line(s): Targets user enumeration endpoints.
- 1 line(s): Targets secret material.
- 1 line(s): Targets application internals rather than safe public recon.
- 1 line(s): Targets personal data.
- 1 line(s): Skipped because it normalizes to a duplicate query template already imported as 'google-pid-2910cff6'.
- 1 line(s): Targets access key material.

## Sample Exclusions

- Line 16 [FILE & DOCUMENT DISCOVERY]: `filetype:xls "password"`
  Reason: Targets passwords or password-bearing content.
- Line 17 [FILE & DOCUMENT DISCOVERY]: `filetype:xls "username" "password"`
  Reason: Targets passwords or password-bearing content.
- Line 22 [FILE & DOCUMENT DISCOVERY]: `filetype:txt "username" "password"`
  Reason: Targets passwords or password-bearing content.
- Line 23 [FILE & DOCUMENT DISCOVERY]: `filetype:txt "password list"`
  Reason: Targets passwords or password-bearing content.
- Line 25 [FILE & DOCUMENT DISCOVERY]: `filetype:log "username" "password"`
  Reason: Targets passwords or password-bearing content.
- Line 27 [FILE & DOCUMENT DISCOVERY]: `filetype:sql "INSERT INTO" "VALUES"`
  Reason: Skipped because the file discovery line falls outside the allowed safe document and log patterns.
- Line 28 [FILE & DOCUMENT DISCOVERY]: `filetype:sql "mysqldump"`
  Reason: Targets database dump files.
- Line 29 [FILE & DOCUMENT DISCOVERY]: `filetype:sql "CREATE TABLE"`
  Reason: Skipped because the file discovery line falls outside the allowed safe document and log patterns.
- Line 30 [FILE & DOCUMENT DISCOVERY]: `filetype:env "DB_PASSWORD"`
  Reason: Targets passwords or password-bearing content.
- Line 31 [FILE & DOCUMENT DISCOVERY]: `filetype:env "SECRET_KEY"`
  Reason: Targets secrets or secret-bearing content.
- Line 32 [FILE & DOCUMENT DISCOVERY]: `filetype:env "API_KEY"`
  Reason: Targets API key material.
- Line 33 [FILE & DOCUMENT DISCOVERY]: `filetype:config "database"`
  Reason: Skipped because the file discovery line falls outside the allowed safe document and log patterns.
- Line 34 [FILE & DOCUMENT DISCOVERY]: `filetype:config "password"`
  Reason: Targets passwords or password-bearing content.
- Line 35 [FILE & DOCUMENT DISCOVERY]: `filetype:cfg "password"`
  Reason: Targets passwords or password-bearing content.
- Line 36 [FILE & DOCUMENT DISCOVERY]: `filetype:cfg "username"`
  Reason: Skipped because the file discovery line falls outside the allowed safe document and log patterns.
- Line 37 [FILE & DOCUMENT DISCOVERY]: `filetype:ini "password"`
  Reason: Targets passwords or password-bearing content.
- Line 38 [FILE & DOCUMENT DISCOVERY]: `filetype:ini "database"`
  Reason: Skipped because the file discovery line falls outside the allowed safe document and log patterns.
- Line 39 [FILE & DOCUMENT DISCOVERY]: `filetype:bak "password"`
  Reason: Targets passwords or password-bearing content.
- Line 40 [FILE & DOCUMENT DISCOVERY]: `filetype:bak "config"`
  Reason: Skipped because the file discovery line falls outside the allowed safe document and log patterns.
- Line 41 [FILE & DOCUMENT DISCOVERY]: `filetype:zip "password"`
  Reason: Targets passwords or password-bearing content.
