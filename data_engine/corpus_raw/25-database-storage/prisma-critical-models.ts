/**
 * Golden Snippet — Modeles Prisma critiques (AfriWallet)
 * Source: afriwallet_codebase/prisma/schema.prisma
 */

/// Wallet principal (compte en FCFA) d’un utilisateur.
model Wallet {
  id              String          @id @default(cuid())
  createdAt       DateTime        @default(now())
  updatedAt       DateTime        @updatedAt

  user            User            @relation(fields: [userId], references: [id])
  userId          String          @unique

  /// Solde disponible en FCFA (représenté en unités entières).
  balanceFcfa     BigInt          @default(0)

  virtualCards    VirtualCard[]
  transactions    Transaction[]
}

/// Carte virtuelle AfriWallet, représentée par un jeton fournisseur.
model VirtualCard {
  id              String      @id @default(cuid())
  createdAt       DateTime    @default(now())

  wallet          Wallet      @relation(fields: [walletId], references: [id])
  walletId        String

  provider        CardProvider

  /// Quatre derniers chiffres pour l’affichage seulement.
  lastFour        String      @db.VarChar(4)

  /// Jeton renvoyé par Onafriq (ou autre partenaire).
  cardToken       String

  isFrozen        Boolean     @default(false)
}

/// Mouvement financier immuable (journal comptable).
model Transaction {
  id              String             @id @default(cuid())
  createdAt       DateTime           @default(now())

  wallet          Wallet             @relation(fields: [walletId], references: [id])
  walletId        String

  /// Montant en FCFA (entier).
  amountFcfa      BigInt
  /// Frais appliqués (même unité que amountFcfa).
  feeFcfa         BigInt             @default(0)
  /// Devise d'origine de l'événement (utile si provider renvoie USD, etc.).
  currency        String             @default("XAF")
  /// Libellé métier (debug + support).
  description     String?

  type            TransactionType
  status          TransactionStatus  @default(PENDING)
  /// Pourquoi un échec (si status = FAILED par ex.)
  failureReason   String?

  /// Fournisseur externe à l’origine du mouvement (MoMo, Airtel, Bridge, Onafriq, etc.).
  provider        PaymentProvider?

  /// Identifiant de transaction côté fournisseur (pour la réclamation / idempotence).
  providerTxId    String?            @unique

  /// Référence idempotente interne (clé pour éviter les doublons de traitement).
  idempotencyKey  String?            @unique

  /// Métadonnées JSON sérialisées (corps du webhook, etc.).
  metadata        Json?

  @@index([walletId, createdAt])
}

/// Demande d’OTP SMS pour authentification par numéro.
model OtpRequest {
  id          String   @id @default(cuid())
  createdAt   DateTime @default(now())
  phoneNumber String
  code        String
  expiresAt   DateTime
  attempts    Int      @default(0)

  @@index([phoneNumber, createdAt])
}

/// Événements webhook entrants (audit + idempotence).
model WebhookEvent {
  id          String   @id @default(cuid())
  createdAt   DateTime @default(now())

  provider    PaymentProvider
  /// Clé d'idempotence (ex: job_id Smile, providerTxId, ou fallback signature+timestamp).
  eventKey    String   @unique

  userId      String?
  /// Référence de session KYC au moment du webhook (si applicable).
  kycReference String?

  /// Payload brut sérialisé (debug/audit).
  payload     Json

  processedAt DateTime?
  /// Erreur de traitement (si le processing échoue).
  error       String?
}

// --- excerpt ---

enum KycStatus {
  PENDING
  VERIFIED
  REJECTED
}

enum TransactionType {
  CASH_IN_MOMO
  CASH_OUT_MOMO
  CASH_IN_AIRTEL
  CARD_ISSUANCE_FEE
  CARD_PAYMENT
  CARD_REFUND
  ADJUSTMENT
}

enum TransactionStatus {
  PENDING
  SUCCESS
  FAILED
}

enum PaymentProvider {
  MTN_MOMO
  AIRTEL
  BRIDGE
  ONAFRIQ
  SMILE_ID
}

enum CardProvider {
  ONAFRIQ
}
