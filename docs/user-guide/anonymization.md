# DICOM Anonymization

MedVista provides DICOM anonymization to remove or replace patient-identifying information while preserving the clinical data for research and sharing.

## What Gets Anonymized

The following DICOM tags are modified:

| Tag | Description | Action |
|-----|-------------|--------|
| (0010,0010) | Patient Name | Replaced with anonymous ID |
| (0010,0020) | Patient ID | Replaced with anonymous ID |
| (0010,0030) | Patient Birth Date | Cleared or shifted |
| (0010,0040) | Patient Sex | Preserved (not identifying) |
| (0008,0050) | Accession Number | Replaced |
| (0008,0080) | Institution Name | Replaced |
| (0008,0081) | Institution Address | Cleared |
| (0008,1010) | Station Name | Cleared |
| (0008,1030) | Study Description | Preserved |
| (0008,1070) | Operators Name | Cleared |

Tags NOT modified (preserved for clinical relevance):
- Study Date (0008,0020)
- Modality (0008,0060)
- Image position/orientation
- Pixel data
- All measurement and structure data

## Anonymization Profiles

MedVista supports several anonymization profiles:

| Profile | Description |
|---------|-------------|
| **Basic** | Name and ID only |
| **Research** | All identifying tags removed or replaced |
| **HIPAA** | Full HIPAA Safe Harbor compliance |
| **Custom** | User-defined tag list |

## Using Anonymization

### Via the Web UI

1. Navigate to the **Anonymization** page
2. Select a dataset from the session
3. Choose an anonymization profile
4. Preview changes before applying
5. Click **"Anonymize"**
6. Download the anonymized DICOM files

### Via the API

```bash
# Anonymize with Research profile
curl -X POST http://localhost:8000/api/anonymization/anonymize \
  -F "files=@scan1.dcm" \
  -F "profile=research"

# Custom anonymization
curl -X POST http://localhost:8000/api/anonymization/anonymize \
  -F "files=@scan1.dcm" \
  -F "profile=custom" \
  -F "tags=(0010,0010),(0010,0020),(0010,0030)"
```

## Custom Anonymization Rules

Create custom rules to handle specific requirements:

```json
{
  "rules": [
    {"tag": "(0010,0010)", "action": "replace", "value": "ANON-001"},
    {"tag": "(0010,0030)", "action": "shift", "days": 365},
    {"tag": "(0008,0050)", "action": "hash", "algorithm": "sha256"},
    {"tag": "(0008,1010)", "action": "clear"}
  ]
}
```

### Actions

| Action | Description |
|--------|-------------|
| `replace` | Replace with a fixed value |
| `clear` | Set to empty string |
| `shift` | Shift dates by a random offset |
| `hash` | Replace with a hash of the original value |
| `keep` | Preserve the original value |

## De-anonymization

For research workflows that need to re-identify data:

1. MedVista stores a secure mapping between original and anonymized IDs
2. Only authorized users with the mapping key can de-anonymize
3. Use the API endpoint `/api/anonymization/de-anonymize` with the mapping key

```bash
curl -X POST http://localhost:8000/api/anonymization/de-anonymize \
  -H "Authorization: Bearer <mapping_key>" \
  -F "files=@anonymized_scan.dcm"
```

## Compliance Notes

- **HIPAA**: Use the `hipaa` profile for full Safe Harbor compliance
- **GDPR**: Anonymization is irreversible when using hash or clear actions
- **IRB**: Custom profiles allow fine-grained control for institutional review board requirements
- All anonymization operations are logged for audit trail purposes
