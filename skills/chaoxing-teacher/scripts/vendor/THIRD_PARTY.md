# Bundled HTTP dependencies

This directory contains pure-Python copies of the HTTP packages required by the Skill. They are
bundled so the teacher-facing runtime does not download or install packages.

| Package | Version | License file |
| --- | --- | --- |
| requests | 2.34.2 | `licenses/requests-LICENSE` and `licenses/requests-NOTICE` |
| urllib3 | 2.7.0 | `licenses/urllib3-LICENSE.txt` |
| certifi | 2026.7.22 | `licenses/certifi-LICENSE` |
| idna | 3.19 | `licenses/idna-LICENSE.md` |
| charset-normalizer | 3.5.1 | `licenses/charset-normalizer-LICENSE` |

Platform-specific extension modules are intentionally excluded; `charset-normalizer` uses its
portable Python implementation on every supported host.
