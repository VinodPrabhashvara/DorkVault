<<<<<<< HEAD
# Technique Catalog Build Report

- Source: `P:\Ethical Hacking\Pentesting\CLI tools\DorkVault\INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt`
- Output directory: `P:\Ethical Hacking\Pentesting\CLI tools\DorkVault\src\dorkvault\data\techniques`
- Generated supplemental drafts: `958`
- Final bundled techniques: `1054`
- Raw-source exclusions: `303`
- Duplicate removals: `53`

## Final Pack Counts

- `api_discovery.json`: 58 technique(s)
- `censys_queries.json`: 74 technique(s)
- `cloud_storage.json`: 162 technique(s)
- `cms_queries.json`: 116 technique(s)
- `ct_logs.json`: 56 technique(s)
- `exposed_files.json`: 150 technique(s)
- `github_queries.json`: 83 technique(s)
- `google_dorks.json`: 219 technique(s)
- `shodan_queries.json`: 74 technique(s)
- `wayback_queries.json`: 62 technique(s)

## Raw Import Exclusion Summary

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

## Duplicate Removal Summary

- 26 removal(s): it is an exact normalized template duplicate
- 23 removal(s): its name already exists in the same category
- 4 removal(s): it is a near-duplicate of an existing query intent

## Sample Duplicate Removals

- `Admin Login Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Admin Login Search`.
  Removed: `site:{domain} inurl:/admin/login.php`
  Kept: `site:{domain} intitle:"admin login" inurl:admin`
- `Admin Surface Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Admin Surface Search`.
  Removed: `site:{domain} inurl:admin`
  Kept: `site:{domain} intitle:"Admin Panel" inurl:admin`
- `Admin Surface Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Admin Surface Search`.
  Removed: `site:{domain} inurl:admin intitle:"login"`
  Kept: `site:{domain} intitle:"Admin Panel" inurl:admin`
- `Directory Listing Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because it is a near-duplicate of an existing query intent. Kept `Directory Listing Search`.
  Removed: `site:{domain} intitle:"index of"`
  Kept: `site:{domain} intext:"Index of /" intitle:"index of"`
- `Grafana Interface Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Grafana Interface Search`.
  Removed: `site:{domain} inurl:":3000" intitle:"Grafana"`
  Kept: `site:{domain} intitle:"Grafana" inurl:"/login"`
- `Jupyter Interface Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Jupyter Interface Search`.
  Removed: `site:{domain} inurl:":8888" intitle:"Jupyter"`
  Kept: `site:{domain} intitle:"Jupyter" inurl:"/tree"`
- `Kibana Interface Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Kibana Interface Search`.
  Removed: `site:{domain} inurl:":5601" intitle:"Kibana"`
  Kept: `site:{domain} inurl:"/kibana"`
- `Log File Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Log File Search`.
  Removed: `site:{domain} intext:"at com.microsoft." filetype:log`
  Kept: `site:{domain} intext:"Call Stack" filetype:log`
- `Log File Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Log File Search`.
  Removed: `site:{domain} intext:"Connection refused" filetype:log`
  Kept: `site:{domain} intext:"Call Stack" filetype:log`
- `Remote Desktop Web Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Remote Desktop Web Search`.
  Removed: `site:{domain} inurl:":3389" intitle:"Remote Desktop"`
  Kept: `site:{domain} intitle:"Remote Desktop" inurl:"/rdweb/pages/en-US/login.aspx"`
- `Tomcat Manager Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Tomcat Manager Search`.
  Removed: `site:{domain} inurl:":8443/manager/html"`
  Kept: `site:{domain} inurl:":8080/manager/html" intitle:"Tomcat"`
- `Tomcat Manager Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Tomcat Manager Search`.
  Removed: `site:{domain} intitle:"Apache Tomcat" inurl:8080`
  Kept: `site:{domain} inurl:":8080/manager/html" intitle:"Tomcat"`
- `Backup Directory Listing Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because it is a near-duplicate of an existing query intent. Kept `Backup Directory Listing Search`.
  Removed: `site:{domain} intitle:"index of" inurl:backup`
  Kept: `site:{domain} intitle:"index of" "backup"`
- `Directory Listing Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Directory Listing Search`.
  Removed: `site:{domain} intitle:"index of" "wwwroot"`
  Kept: `site:{domain} intitle:"index of" "parent directory"`
- `Directory Listing Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Directory Listing Search`.
  Removed: `site:{domain} intitle:"index of" "htdocs"`
  Kept: `site:{domain} intitle:"index of" "parent directory"`
- `Directory Listing Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Directory Listing Search`.
  Removed: `site:{domain} intitle:"index of" "src"`
  Kept: `site:{domain} intitle:"index of" "parent directory"`
- `Directory Listing Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Directory Listing Search`.
  Removed: `site:{domain} intitle:"index of" "source"`
  Kept: `site:{domain} intitle:"index of" "parent directory"`
- `Log File Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Log File Search`.
  Removed: `site:{domain} filetype:log "access denied"`
  Kept: `site:{domain} filetype:log "error"`
- `Public DOC Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Public DOC Search`.
  Removed: `site:{domain} filetype:doc "confidential"`
  Kept: `site:{domain} filetype:doc "internal use only"`
- `Public PDF Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because it is a near-duplicate of an existing query intent. Kept `Public PDF Search`.
  Removed: `site:{domain} filetype:pdf "confidential"`
  Kept: `site:{domain} filetype:pdf intext:"confidential"`
- `Public PDF Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Public PDF Search`.
  Removed: `site:{domain} filetype:pdf "not for distribution"`
  Kept: `site:{domain} filetype:pdf "internal use only"`
- `Drupal Surface Search` [cms_queries] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Drupal Surface Search`.
  Removed: `site:{domain} inurl:"/?q=user/login" intitle:"Drupal"`
  Kept: `site:{domain} inurl:"/user/login" intitle:"Drupal"`
- `Joomla Surface Search` [cms_queries] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Joomla Surface Search`.
  Removed: `site:{domain} inurl:"/index.php?option=com_config"`
  Kept: `site:{domain} inurl:"/index.php?option=com_users"`
- `Magento Surface Search` [cms_queries] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Magento Surface Search`.
  Removed: `site:{domain} inurl:"/downloader/" intitle:"Magento"`
  Kept: `site:{domain} inurl:"/index.php/admin/" intitle:"Magento"`
- `WordPress Surface Search` [cms_queries] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `WordPress Surface Search`.
  Removed: `site:{domain} inurl:"/?author=1" inurl:"wordpress"`
  Kept: `site:{domain} inurl:"/?p=" intitle:"WordPress"`

## Sample Raw Exclusions

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
=======
# Technique Catalog Build Report

- Source: `P:\Ethical Hacking\Pentesting\CLI tools\DorkVault\INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt`
- Output directory: `P:\Ethical Hacking\Pentesting\CLI tools\DorkVault\src\dorkvault\data\techniques`
- Generated supplemental drafts: `958`
- Final bundled techniques: `1054`
- Raw-source exclusions: `303`
- Duplicate removals: `53`

## Final Pack Counts

- `api_discovery.json`: 58 technique(s)
- `censys_queries.json`: 74 technique(s)
- `cloud_storage.json`: 162 technique(s)
- `cms_queries.json`: 116 technique(s)
- `ct_logs.json`: 56 technique(s)
- `exposed_files.json`: 150 technique(s)
- `github_queries.json`: 83 technique(s)
- `google_dorks.json`: 219 technique(s)
- `shodan_queries.json`: 74 technique(s)
- `wayback_queries.json`: 62 technique(s)

## Raw Import Exclusion Summary

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

## Duplicate Removal Summary

- 26 removal(s): it is an exact normalized template duplicate
- 23 removal(s): its name already exists in the same category
- 4 removal(s): it is a near-duplicate of an existing query intent

## Sample Duplicate Removals

- `Admin Login Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Admin Login Search`.
  Removed: `site:{domain} inurl:/admin/login.php`
  Kept: `site:{domain} intitle:"admin login" inurl:admin`
- `Admin Surface Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Admin Surface Search`.
  Removed: `site:{domain} inurl:admin`
  Kept: `site:{domain} intitle:"Admin Panel" inurl:admin`
- `Admin Surface Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Admin Surface Search`.
  Removed: `site:{domain} inurl:admin intitle:"login"`
  Kept: `site:{domain} intitle:"Admin Panel" inurl:admin`
- `Directory Listing Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because it is a near-duplicate of an existing query intent. Kept `Directory Listing Search`.
  Removed: `site:{domain} intitle:"index of"`
  Kept: `site:{domain} intext:"Index of /" intitle:"index of"`
- `Grafana Interface Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Grafana Interface Search`.
  Removed: `site:{domain} inurl:":3000" intitle:"Grafana"`
  Kept: `site:{domain} intitle:"Grafana" inurl:"/login"`
- `Jupyter Interface Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Jupyter Interface Search`.
  Removed: `site:{domain} inurl:":8888" intitle:"Jupyter"`
  Kept: `site:{domain} intitle:"Jupyter" inurl:"/tree"`
- `Kibana Interface Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Kibana Interface Search`.
  Removed: `site:{domain} inurl:":5601" intitle:"Kibana"`
  Kept: `site:{domain} inurl:"/kibana"`
- `Log File Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Log File Search`.
  Removed: `site:{domain} intext:"at com.microsoft." filetype:log`
  Kept: `site:{domain} intext:"Call Stack" filetype:log`
- `Log File Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Log File Search`.
  Removed: `site:{domain} intext:"Connection refused" filetype:log`
  Kept: `site:{domain} intext:"Call Stack" filetype:log`
- `Remote Desktop Web Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Remote Desktop Web Search`.
  Removed: `site:{domain} inurl:":3389" intitle:"Remote Desktop"`
  Kept: `site:{domain} intitle:"Remote Desktop" inurl:"/rdweb/pages/en-US/login.aspx"`
- `Tomcat Manager Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Tomcat Manager Search`.
  Removed: `site:{domain} inurl:":8443/manager/html"`
  Kept: `site:{domain} inurl:":8080/manager/html" intitle:"Tomcat"`
- `Tomcat Manager Search` [google_dorks] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Tomcat Manager Search`.
  Removed: `site:{domain} intitle:"Apache Tomcat" inurl:8080`
  Kept: `site:{domain} inurl:":8080/manager/html" intitle:"Tomcat"`
- `Backup Directory Listing Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because it is a near-duplicate of an existing query intent. Kept `Backup Directory Listing Search`.
  Removed: `site:{domain} intitle:"index of" inurl:backup`
  Kept: `site:{domain} intitle:"index of" "backup"`
- `Directory Listing Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Directory Listing Search`.
  Removed: `site:{domain} intitle:"index of" "wwwroot"`
  Kept: `site:{domain} intitle:"index of" "parent directory"`
- `Directory Listing Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Directory Listing Search`.
  Removed: `site:{domain} intitle:"index of" "htdocs"`
  Kept: `site:{domain} intitle:"index of" "parent directory"`
- `Directory Listing Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Directory Listing Search`.
  Removed: `site:{domain} intitle:"index of" "src"`
  Kept: `site:{domain} intitle:"index of" "parent directory"`
- `Directory Listing Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Directory Listing Search`.
  Removed: `site:{domain} intitle:"index of" "source"`
  Kept: `site:{domain} intitle:"index of" "parent directory"`
- `Log File Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Log File Search`.
  Removed: `site:{domain} filetype:log "access denied"`
  Kept: `site:{domain} filetype:log "error"`
- `Public DOC Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Public DOC Search`.
  Removed: `site:{domain} filetype:doc "confidential"`
  Kept: `site:{domain} filetype:doc "internal use only"`
- `Public PDF Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because it is a near-duplicate of an existing query intent. Kept `Public PDF Search`.
  Removed: `site:{domain} filetype:pdf "confidential"`
  Kept: `site:{domain} filetype:pdf intext:"confidential"`
- `Public PDF Search` [exposed_files] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Public PDF Search`.
  Removed: `site:{domain} filetype:pdf "not for distribution"`
  Kept: `site:{domain} filetype:pdf "internal use only"`
- `Drupal Surface Search` [cms_queries] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Drupal Surface Search`.
  Removed: `site:{domain} inurl:"/?q=user/login" intitle:"Drupal"`
  Kept: `site:{domain} inurl:"/user/login" intitle:"Drupal"`
- `Joomla Surface Search` [cms_queries] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Joomla Surface Search`.
  Removed: `site:{domain} inurl:"/index.php?option=com_config"`
  Kept: `site:{domain} inurl:"/index.php?option=com_users"`
- `Magento Surface Search` [cms_queries] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `Magento Surface Search`.
  Removed: `site:{domain} inurl:"/downloader/" intitle:"Magento"`
  Kept: `site:{domain} inurl:"/index.php/admin/" intitle:"Magento"`
- `WordPress Surface Search` [cms_queries] from `raw:INSANE PK   GOOGLE DORKS COMPLETE COLLECTION.txt` removed because its name already exists in the same category. Kept `WordPress Surface Search`.
  Removed: `site:{domain} inurl:"/?author=1" inurl:"wordpress"`
  Kept: `site:{domain} inurl:"/?p=" intitle:"WordPress"`

## Sample Raw Exclusions

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
>>>>>>> 7feb2e5449bafaaae0a9fb02ebce5e34d1e3682c
