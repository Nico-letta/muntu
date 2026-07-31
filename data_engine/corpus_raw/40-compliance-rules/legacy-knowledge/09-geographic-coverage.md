# Legacy Knowledge — 09-geographic-coverage

```json
{
  "title": "Couverture géographique AfriWallet — Fintech Afrique",
  "version": "1.0.0",
  "summary": "AfriWallet couvre 10 pays africains via KYC, defaults opérationnels, ou intégrations Mobile Money multi-opco",
  "regions": {
    "west_africa": {
      "countries": [
        {
          "code": "NG",
          "name": "Nigeria",
          "kyc_biometric": true,
          "kyc_id_types": [
            "NIN",
            "NIN_V2",
            "NIN_SLIP",
            "BVN",
            "V_NIN",
            "BANK_ACCOUNT",
            "PHONE_NUMBER",
            "VOTER_ID"
          ],
          "mobile_money": "MTN MoMo opco mtnnigeria",
          "currency_note": "NGN localement — AfriWallet wallet en FCFA/XAF pour intégration régionale",
          "regulator": "CBN, NIMC",
          "reference_template": "biometric-kyc-ng-nin_v2.info.json"
        },
        {
          "code": "GH",
          "name": "Ghana",
          "kyc_biometric": true,
          "kyc_id_types": [
            "GHANA_CARD",
            "GHANA_CARD_NO_PHOTO",
            "PASSPORT",
            "VOTER_ID"
          ],
          "mobile_money": "MTN MoMo (Ghana opco)",
          "currency": "GHS",
          "regulator": "Bank of Ghana"
        },
        {
          "code": "CI",
          "name": "Côte d'Ivoire",
          "kyc_biometric": true,
          "kyc_id_types": [
            "NATIONAL_ID_NO_PHOTO",
            "RESIDENT_ID_NO_PHOTO"
          ],
          "mobile_money": "MTN MoMo",
          "currency_zone": "UEMOA XOF",
          "regulator": "BCEAO"
        }
      ]
    },
    "east_africa": {
      "countries": [
        {
          "code": "KE",
          "name": "Kenya",
          "kyc_biometric": true,
          "kyc_id_types": [
            "NATIONAL_ID",
            "NATIONAL_ID_NO_PHOTO",
            "KRA_PIN",
            "ALIEN_CARD",
            "TAX_INFORMATION",
            "PASSPORT"
          ],
          "mobile_money": "M-Pesa dominant — MTN MoMo présent",
          "currency": "KES",
          "regulator": "CBK"
        },
        {
          "code": "UG",
          "name": "Ouganda",
          "kyc_biometric": true,
          "kyc_id_types": [
            "NATIONAL_ID_NO_PHOTO"
          ],
          "special_requirements": [
            "secondaryIdNumber",
            "dob"
          ],
          "mobile_money": "MTN MoMo",
          "currency": "UGX",
          "regulator": "Bank of Uganda"
        }
      ]
    },
    "southern_africa": {
      "countries": [
        {
          "code": "ZA",
          "name": "Afrique du Sud",
          "kyc_biometric": true,
          "kyc_id_types": [
            "NATIONAL_ID",
            "NATIONAL_ID_NO_PHOTO",
            "PHONE_NUMBER",
            "REFUGEE_ID"
          ],
          "id_format": "13 chiffres",
          "currency": "ZAR",
          "regulator": "FSCA, SARB"
        },
        {
          "code": "ZM",
          "name": "Zambie",
          "kyc_biometric": true,
          "kyc_id_types": [
            "BANK_ACCOUNT",
            "TPIN"
          ],
          "currency": "ZMW",
          "regulator": "Bank of Zambia"
        },
        {
          "code": "ZW",
          "name": "Zimbabwe",
          "kyc_biometric": true,
          "kyc_id_types": [
            "NATIONAL_ID_NO_PHOTO"
          ],
          "id_format": "8-9 chiffres + lettre + 2 chiffres",
          "currency": "ZWL/USD multi",
          "regulator": "RBZ"
        }
      ]
    },
    "central_africa": {
      "countries": [
        {
          "code": "CM",
          "name": "Cameroun",
          "kyc_biometric": false,
          "kyc_note": "Pas dans smile-id-id-rules — pas de biometric registry Smile ID",
          "onafriq_defaults": true,
          "defaults": {
            "country": "CM",
            "phone_code": "237",
            "city": "Douala",
            "currency": "XAF"
          },
          "mobile_money": "MTN MoMo opco mtncameroon",
          "currency_zone": "CEMAC XAF",
          "regulator": "BEAC, COBAC",
          "example_test_phone": "+237670000000"
        },
        {
          "code": "CG",
          "name": "Congo (Brazzaville)",
          "kyc_document_verification": true,
          "kyc_biometric": false,
          "kyc_id_types": [
            "DRIVERS_LICENSE",
            "IDENTITY_CARD",
            "PASSPORT",
            "RESIDENT_ID",
            "TAX_ID",
            "TRAVEL_DOC"
          ],
          "mobile_money": "MTN MoMo opco mtncongo",
          "currency_zone": "CEMAC XAF",
          "regulator": "BEAC",
          "reference_template": "document-verification-cg.info.json"
        }
      ]
    }
  },
  "mobile_money_coverage": {
    "provider": "MTN_MOMO",
    "pattern": "Multi-opco via MTN_MOMO_TARGET_ENVIRONMENT",
    "known_opcos": [
      "sandbox",
      "mtnnigeria",
      "mtncameroon",
      "mtncongo"
    ],
    "sandbox_currency": "EUR",
    "production_currency": "XAF",
    "integration_type": "RequestToPay (collection) + Disbursement (transfer)"
  },
  "card_issuing_coverage": {
    "provider": "ONAFRIQ",
    "default_market": "CM (Cameroun)",
    "card_currency": "XAF",
    "note": "Onafriq couvre historiquement 40+ pays africains — AfriWallet configure defaults CM"
  },
  "gaps_for_enrichment": [
    "Réglementation BEAC/COBAC détaillée (CEMAC)",
    "Réglementation BCEAO détaillée (UEMOA)",
    "Orange Money, Wave, M-Pesa intégrations",
    "Airtel Money (enum AfriWallet non implémenté)",
    "KYC Cameroun biometric (CM absent des règles Smile ID)",
    "Multi-devises XOF vs XAF distinction métier",
    "Limites transactionnelles réglementaires par pays"
  ]
}
```
