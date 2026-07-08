# Golden Snippet — `src/kyc/smile-id-id-rules.ts`

> **Couche:** `30-system-integrations` · **Source:** `afriwallet_codebase/src/kyc/smile-id-id-rules.ts`

Validation regex ID par pays africain pour KYC Smile ID.

```typescript
import { BadRequestException } from '@nestjs/common';

type IdRule = {
  regex?: RegExp;
  requiredFields?: Array<'bankCode' | 'secondaryIdNumber' | 'dob'>;
};

type CountryRules = Record<string, IdRule>;

const KYC_ID_RULES: Record<string, CountryRules> = {
  CI: {
    NATIONAL_ID_NO_PHOTO: { regex: /^(?:\d{11}|[A-Za-z]\d{10})$/ },
    RESIDENT_ID_NO_PHOTO: { regex: /^(?:\d{11}|[A-Za-z]\d{10})$/ },
  },
  GH: {
    GHANA_CARD: { regex: /^[A-Z]{3}-?\d{9}-?\d$/i },
    GHANA_CARD_NO_PHOTO: { regex: /^[A-Z]{3}-?\d{9}-?\d$/i },
    PASSPORT: { regex: /^[A-Z0-9]{7,9}$/ },
    VOTER_ID: { regex: /^\d{10}$/ },
  },
  KE: {
    ALIEN_CARD: { regex: /^\d{6,9}$/ },
    KRA_PIN: { regex: /^\d{1,9}$/ },
    NATIONAL_ID: { regex: /^\d{1,9}$/ },
    NATIONAL_ID_NO_PHOTO: { regex: /^\d{1,9}$/ },
    PASSPORT: { regex: /^[A-Z0-9]{7,9}$/ },
    TAX_INFORMATION: { regex: /^[Aa]\d{9}[A-Za-z]$/ },
  },
  NG: {
    BANK_ACCOUNT: { regex: /^\d{10}$/, requiredFields: ['bankCode'] },
    BVN: { regex: /^\d{11}$/ },
    NIN: { regex: /^\d{11}$/ },
    NIN_V2: { regex: /^\d{11}$/ },
    NIN_SLIP: { regex: /^\d{11}$/ },
    V_NIN: { regex: /^[A-Za-z0-9]{16}$/ },
    PHONE_NUMBER: { regex: /^\d{11}$/ },
    VOTER_ID: { regex: /^[A-Za-z0-9 ]{9,29}$/i },
  },
  ZA: {
    NATIONAL_ID: { regex: /^\d{13}$/ },
    NATIONAL_ID_NO_PHOTO: { regex: /^\d{13}$/ },
    PHONE_NUMBER: { regex: /^\d{10}$/ },
    REFUGEE_ID: { regex: /^[A-Za-z]{3,6}\d{9,12}$/ },
  },
  UG: {
    NATIONAL_ID_NO_PHOTO: {
      regex: /^[A-Z0-9]{14}$/i,
      requiredFields: ['secondaryIdNumber', 'dob'],
    },
  },
  ZM: {
    BANK_ACCOUNT: { regex: /^\d{13}$/, requiredFields: ['bankCode'] },
    TPIN: { regex: /^\d{10}$/ },
  },
  ZW: {
    NATIONAL_ID_NO_PHOTO: { regex: /^[0-9]{8,9}[A-Za-z]\d{2}$/ },
  },
};

export const SUPPORTED_COUNTRIES = Object.keys(KYC_ID_RULES);

export function getSupportedIdTypes(country: string): string[] {
  return Object.keys(KYC_ID_RULES[country] ?? {});
}

type ValidationInput = {
  country: string;
  idType: string;
  idNumber: string;
  bankCode?: string;
  secondaryIdNumber?: string;
  dob?: string;
};

export function validateSmileIdKycInput(input: ValidationInput): void {
  const country = input.country.trim().toUpperCase();
  const idType = input.idType.trim().toUpperCase();
  const idNumber = input.idNumber.trim();

  const countryRules = KYC_ID_RULES[country];
  if (!countryRules) {
    throw new BadRequestException(
      `Unsupported country '${country}'. Supported countries: ${SUPPORTED_COUNTRIES.join(', ')}`,
    );
  }

  const rule = countryRules[idType];
  if (!rule) {
    throw new BadRequestException(
      `Unsupported idType '${idType}' for country '${country}'. Supported types: ${getSupportedIdTypes(country).join(', ')}`,
    );
  }

  if (rule.regex && !rule.regex.test(idNumber)) {
    throw new BadRequestException(
      `Invalid idNumber format for ${country}/${idType}. Please follow Smile ID regex format.`,
    );
  }

  if (rule.requiredFields?.includes('bankCode') && !input.bankCode?.trim()) {
    throw new BadRequestException(`bankCode is required for ${country}/${idType}.`);
  }
  if (
    rule.requiredFields?.includes('secondaryIdNumber') &&
    !input.secondaryIdNumber?.trim()
  ) {
    throw new BadRequestException(`secondaryIdNumber is required for ${country}/${idType}.`);
  }
  if (rule.requiredFields?.includes('dob') && !input.dob?.trim()) {
    throw new BadRequestException(`dob is required for ${country}/${idType}.`);
  }
}

```
