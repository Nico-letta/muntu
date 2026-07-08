# Domaine — Règles KYC par Pays (Smile ID)

> **Couche** : `40-compliance-rules` · **Bounded context** : identité africaine  
> **Source** : `src/kyc/smile-id-id-rules.ts`

## Contexte

Les LLM occidentaux ignorent les formats d'identité africains. **Avant** d'appliquer une regex pays, consulter la matrice régionale :

- `cemac-cobac.md` — CM, CG (XAF) — **CM sans biometric**
- `uemoa-bceao.md` — CI (XOF)
- `cbn-nigeria.md` — NG (NIN/BVN) — **ne pas appliquer sur CM/CG/CI**

## Validations globales

Tous les pays biometric exigent :
- `country` : ISO alpha-2 (`^[A-Z]{2}$`)
- `dob` : `yyyy-mm-dd`
- `idNumber` : max 32 caractères

## Contrat — Pays supportés (biometric registry)

```json
{
  "supported_countries": ["CI", "GH", "KE", "NG", "ZA", "UG", "ZM", "ZW"],
  "global_validations": {
    "country": { "regex": "^[A-Z]{2}$" },
    "dob": { "regex": "^\\d{4}-\\d{2}-\\d{2}$" },
    "idNumber": { "max_length": 32 }
  }
}
```

## Contrat — Nigeria (NG) — priorité Afrique de l'Ouest

```json
{
  "NG": {
    "regulators": ["CBN", "NIMC"],
    "id_types": {
      "NIN": { "regex": "^\\d{11}$" },
      "NIN_V2": { "regex": "^\\d{11}$", "default_template": true },
      "NIN_SLIP": { "regex": "^\\d{11}$" },
      "BVN": { "regex": "^\\d{11}$" },
      "V_NIN": { "regex": "^[A-Za-z0-9]{16}$" },
      "BANK_ACCOUNT": { "regex": "^\\d{10}$", "required_fields": ["bankCode"] },
      "PHONE_NUMBER": { "regex": "^\\d{11}$" },
      "VOTER_ID": { "regex": "^[A-Za-z0-9 ]{9,29}$", "case_insensitive": true }
    },
    "biometric_images": {
      "selfie": { "image_type_id": 0, "file": "selfie.jpg" },
      "liveness": { "image_type_id": 4, "files": "liveness_1.jpg … liveness_8.jpg" }
    }
  }
}
```

## Contrat — Ghana (GH)

```json
{
  "GH": {
    "GHANA_CARD": { "regex": "^[A-Z]{3}-?\\d{9}-?\\d$", "example": "GHA-123456789-0" },
    "PASSPORT": { "regex": "^[A-Z0-9]{7,9}$" },
    "VOTER_ID": { "regex": "^\\d{10}$" }
  }
}
```

## Contrat — Ouganda (UG) — champs extra obligatoires

```json
{
  "UG": {
    "NATIONAL_ID_NO_PHOTO": {
      "regex": "^[A-Z0-9]{14}$",
      "required_fields": ["secondaryIdNumber", "dob"]
    }
  }
}
```

## Contrat — Afrique du Sud (ZA)

```json
{
  "ZA": {
    "NATIONAL_ID": { "regex": "^\\d{13}$" },
    "PHONE_NUMBER": { "regex": "^\\d{10}$" },
    "REFUGEE_ID": { "regex": "^[A-Za-z]{3,6}\\d{9,12}$" }
  }
}
```

## Contrat — Autres pays (CI, KE, ZM, ZW)

```json
{
  "CI": {
    "NATIONAL_ID_NO_PHOTO": { "regex": "^(?:\\d{11}|[A-Za-z]\\d{10})$" }
  },
  "KE": {
    "KRA_PIN": { "regex": "^\\d{1,9}$" },
    "TAX_INFORMATION": { "regex": "^[Aa]\\d{9}[A-Za-z]$" }
  },
  "ZM": {
    "BANK_ACCOUNT": { "regex": "^\\d{13}$", "required_fields": ["bankCode"] },
    "TPIN": { "regex": "^\\d{10}$" }
  },
  "ZW": {
    "NATIONAL_ID_NO_PHOTO": { "regex": "^[0-9]{8,9}[A-Za-z]\\d{2}$" }
  }
}
```

## Contrat — Document verification Congo (CG)

```json
{
  "document_verification_CG": {
    "job_type": 11,
    "country": "CG",
    "id_types": ["DRIVERS_LICENSE", "IDENTITY_CARD", "PASSPORT", "RESIDENT_ID", "TAX_ID", "TRAVEL_DOC"],
    "images": { "selfie": 0, "id_front": 1, "id_back": 5 }
  }
}
```

## Contrat — Smile ID job types

```json
{
  "job_types": {
    "1": { "name": "Biometric KYC", "prefix": "kyc_", "updates_kyc_status": true },
    "2": { "name": "SmartSelfie Auth", "prefix": "ssauth_", "updates_kyc_status": false },
    "4": { "name": "SmartSelfie Register", "prefix": "ssreg_", "updates_kyc_status": false },
    "11": { "name": "Document Verification", "prefix": "doc_", "updates_kyc_status": true }
  },
  "error_codes": {
    "2215": "job_id duplicate",
    "2209": "job type incompatible",
    "2304": "job not found"
  }
}
```

## Voir aussi

- [Flux metier AfriWallet](../35-business-flows/afriwallet-business-flows.md)
- [Provider specs Smile ID](../provider-specs.md)
