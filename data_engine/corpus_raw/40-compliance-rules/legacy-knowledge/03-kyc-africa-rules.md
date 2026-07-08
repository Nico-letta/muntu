# Legacy Knowledge — 03-kyc-africa-rules

```json
{
  "title": "Règles KYC Afrique — Smile ID (source: smile-id-id-rules.ts)",
  "version": "1.0.0",
  "source_file": "src/kyc/smile-id-id-rules.ts",
  "supported_countries": [
    "CI",
    "GH",
    "KE",
    "NG",
    "ZA",
    "UG",
    "ZM",
    "ZW"
  ],
  "not_in_biometric_rules": {
    "CM": "Cameroun — defaults Onafriq uniquement, pas de règles biometric Smile ID dans AfriWallet",
    "CG": "Congo — document verification (job_type 11) uniquement, pas biometric registry"
  },
  "global_validations": {
    "country": {
      "format": "ISO 3166-1 alpha-2",
      "regex": "^[A-Z]{2}$"
    },
    "dob": {
      "format": "yyyy-mm-dd",
      "regex": "^\\d{4}-\\d{2}-\\d{2}$"
    },
    "idNumber": {
      "max_length": 32
    }
  },
  "countries": {
    "CI": {
      "name": "Côte d'Ivoire",
      "region": "west_africa",
      "currency_zone": "UEMOA (XOF)",
      "id_types": {
        "NATIONAL_ID_NO_PHOTO": {
          "regex": "^(?:\\d{11}|[A-Za-z]\\d{10})$",
          "required_fields": [],
          "description": "11 chiffres OU 1 lettre + 10 chiffres"
        },
        "RESIDENT_ID_NO_PHOTO": {
          "regex": "^(?:\\d{11}|[A-Za-z]\\d{10})$",
          "required_fields": [],
          "description": "Même format que NATIONAL_ID_NO_PHOTO"
        }
      }
    },
    "GH": {
      "name": "Ghana",
      "region": "west_africa",
      "id_types": {
        "GHANA_CARD": {
          "regex": "^[A-Z]{3}-?\\d{9}-?\\d$",
          "case_insensitive": true,
          "example": "GHA-123456789-0",
          "description": "3 lettres + 9 chiffres + 1 chiffre de contrôle"
        },
        "GHANA_CARD_NO_PHOTO": {
          "regex": "^[A-Z]{3}-?\\d{9}-?\\d$",
          "case_insensitive": true
        },
        "PASSPORT": {
          "regex": "^[A-Z0-9]{7,9}$",
          "description": "7 à 9 caractères alphanumériques"
        },
        "VOTER_ID": {
          "regex": "^\\d{10}$",
          "description": "10 chiffres"
        }
      }
    },
    "KE": {
      "name": "Kenya",
      "region": "east_africa",
      "id_types": {
        "ALIEN_CARD": {
          "regex": "^\\d{6,9}$",
          "description": "6 à 9 chiffres"
        },
        "KRA_PIN": {
          "regex": "^\\d{1,9}$",
          "description": "Kenya Revenue Authority PIN, 1 à 9 chiffres"
        },
        "NATIONAL_ID": {
          "regex": "^\\d{1,9}$"
        },
        "NATIONAL_ID_NO_PHOTO": {
          "regex": "^\\d{1,9}$"
        },
        "PASSPORT": {
          "regex": "^[A-Z0-9]{7,9}$"
        },
        "TAX_INFORMATION": {
          "regex": "^[Aa]\\d{9}[A-Za-z]$",
          "description": "Format KRA: A + 9 chiffres + lettre"
        }
      }
    },
    "NG": {
      "name": "Nigeria",
      "region": "west_africa",
      "regulator_hint": "CBN (Central Bank of Nigeria), NIMC pour NIN",
      "id_types": {
        "BANK_ACCOUNT": {
          "regex": "^\\d{10}$",
          "required_fields": [
            "bankCode"
          ],
          "description": "Numéro compte 10 chiffres + code banque obligatoire"
        },
        "BVN": {
          "regex": "^\\d{11}$",
          "description": "Bank Verification Number — identifiant bancaire unique 11 chiffres"
        },
        "NIN": {
          "regex": "^\\d{11}$",
          "description": "National Identification Number"
        },
        "NIN_V2": {
          "regex": "^\\d{11}$",
          "description": "NIN version 2 — template AfriWallet par défaut"
        },
        "NIN_SLIP": {
          "regex": "^\\d{11}$",
          "description": "NIN sur slip temporaire"
        },
        "V_NIN": {
          "regex": "^[A-Za-z0-9]{16}$",
          "description": "Virtual NIN — 16 caractères alphanumériques"
        },
        "PHONE_NUMBER": {
          "regex": "^\\d{11}$",
          "description": "Numéro téléphone 11 chiffres comme ID"
        },
        "VOTER_ID": {
          "regex": "^[A-Za-z0-9 ]{9,29}$",
          "case_insensitive": true,
          "description": "9 à 29 caractères alphanumériques avec espaces"
        }
      },
      "biometric_template": {
        "file": "docs/smile-id/templates/biometric-kyc-ng-nin_v2.info.json",
        "images_required": [
          "selfie.jpg",
          "liveness_1.jpg through liveness_8.jpg"
        ],
        "image_type_ids": {
          "selfie": 0,
          "liveness": 4
        }
      }
    },
    "ZA": {
      "name": "Afrique du Sud",
      "region": "southern_africa",
      "id_types": {
        "NATIONAL_ID": {
          "regex": "^\\d{13}$",
          "description": "13 chiffres — format ID sud-africain"
        },
        "NATIONAL_ID_NO_PHOTO": {
          "regex": "^\\d{13}$"
        },
        "PHONE_NUMBER": {
          "regex": "^\\d{10}$"
        },
        "REFUGEE_ID": {
          "regex": "^[A-Za-z]{3,6}\\d{9,12}$",
          "description": "3-6 lettres + 9-12 chiffres"
        }
      }
    },
    "UG": {
      "name": "Ouganda",
      "region": "east_africa",
      "id_types": {
        "NATIONAL_ID_NO_PHOTO": {
          "regex": "^[A-Z0-9]{14}$",
          "case_insensitive": true,
          "required_fields": [
            "secondaryIdNumber",
            "dob"
          ],
          "description": "14 caractères alphanumériques + ID secondaire + date naissance obligatoires"
        }
      }
    },
    "ZM": {
      "name": "Zambie",
      "region": "southern_africa",
      "id_types": {
        "BANK_ACCOUNT": {
          "regex": "^\\d{13}$",
          "required_fields": [
            "bankCode"
          ],
          "description": "13 chiffres + code banque"
        },
        "TPIN": {
          "regex": "^\\d{10}$",
          "description": "Tax Payer Identification Number"
        }
      }
    },
    "ZW": {
      "name": "Zimbabwe",
      "region": "southern_africa",
      "id_types": {
        "NATIONAL_ID_NO_PHOTO": {
          "regex": "^[0-9]{8,9}[A-Za-z]\\d{2}$",
          "description": "8-9 chiffres + lettre + 2 chiffres"
        }
      }
    }
  },
  "document_verification_cg": {
    "country": "CG",
    "name": "Congo (Brazzaville)",
    "job_type": 11,
    "id_types": [
      "DRIVERS_LICENSE",
      "IDENTITY_CARD",
      "PASSPORT",
      "RESIDENT_ID",
      "TAX_ID",
      "TRAVEL_DOC"
    ],
    "template": "docs/smile-id/templates/document-verification-cg.info.json",
    "images_required": [
      "selfie",
      "id_front (type 1)",
      "id_back (type 5)"
    ],
    "note": "Seul pays document verification dans AfriWallet — biometric registry CM non supporté"
  },
  "smile_id_job_types": {
    "1": {
      "name": "Biometric KYC",
      "job_id_prefix": "kyc_",
      "updates_kyc_status": true
    },
    "2": {
      "name": "SmartSelfie Auth",
      "job_id_prefix": "ssauth_",
      "updates_kyc_status": false
    },
    "4": {
      "name": "SmartSelfie Register",
      "job_id_prefix": "ssreg_",
      "updates_kyc_status": false
    },
    "11": {
      "name": "Document Verification",
      "job_id_prefix": "doc_",
      "updates_kyc_status": true
    }
  },
  "smartselfie_auth_reasons": [
    "large_withdrawal",
    "pin_reset",
    "high_risk_device",
    "wallet_recovery"
  ],
  "kyc_status_flow": {
    "PENDING": "Session KYC ouverte, en attente résultat Smile ID",
    "VERIFIED": "Webhook job_success=true — accès paiements et cartes",
    "REJECTED": "Webhook job_success=false — accès paiements bloqué"
  },
  "smile_error_codes": {
    "2215": "job_id déjà existant — générer nouveau jobId ou retry:true",
    "2209": "job type incompatible — user déjà enrolled SmartSelfie",
    "2304": "job introuvable"
  },
  "image_type_ids": {
    "0": "Selfie file (.jpg/.png)",
    "1": "ID card front",
    "4": "Liveness image",
    "5": "ID card back"
  }
}
```
