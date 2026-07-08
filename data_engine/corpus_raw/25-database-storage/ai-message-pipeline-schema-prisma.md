# Prisma Schema — IA message pipeline (source complete)

> Source: `ai_message_codebase/prisma/schema.prisma`

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "mysql"
}

enum UserTier {
  PROSPECT      // Anciennement VISITEUR
  VERIFIED      // Anciennement FIDELE_REGULIER
  PREMIUM       // Anciennement MEMBRE
  ADMIN         // Anciennement RESPONSABLE
}

enum AppState {
  IDLE
  AWAITING_KYC_DOC
  KYC_IN_PROGRESS
  AWAITING_PIN
  AWAITING_AMOUNT
  CONFIRM_TRANSACTION
}

model Session {
  id                String   @id @default(uuid())
  whatsappId        String   @unique
  currentState      AppState @default(IDLE) 
  contextData       Json?
  lastUpdated       DateTime @updatedAt
  kycExternalId     String?
  user              User?    @relation(fields: [userId], references: [id])
  userId            String?  @unique 
  lastInteractionAt DateTime @default(now())

  @@map("sessions") // Ajouté pour la cohérence globale
}

enum EscalationStatus {
  PENDING
  IN_PROGRESS
  RESOLVED
}

model User {
  id          String   @id @default(uuid())
  whatsappId  String   @unique
  nom         String?
  prenom      String?
  tier        UserTier @default(PROSPECT) // Corrigé (nom du champ et valeur par défaut)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  messages    MessageLog[]
  escalations Escalation[]
  session     Session?

  @@map("users")
}

model MessageLog {
  id           String   @id @default(uuid())
  userId       String?  
  user         User?    @relation(fields: [userId], references: [id], onDelete: SetNull)
  role         String   // "user" ou "assistant"
  content      String   @db.Text
  createdAt    DateTime @default(now())
  intent       String?  
  actionStatus String?  // "PENDING", "EXECUTED", "REJECTED"

  @@index([userId]) 
  @@map("message_logs")
}

// Table d'archivage pour la stratégie de rotation des logs
model MessageLogArchive {
  id           String   @id
  userId       String?
  role         String
  content      String   @db.Text
  createdAt    DateTime
  intent       String?
  actionStatus String?
  archivedAt   DateTime @default(now())

  @@map("message_logs_archive")
}

model KnowledgeBase {
  id          String   @id @default(uuid())
  title       String
  fileType    String
  storagePath String
  isApproved  Boolean  @default(false)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@map("knowledge_base")
}

model Escalation {
  id          String           @id @default(uuid())
  userId      String
  user        User             @relation(fields: [userId], references: [id], onDelete: Cascade)
  status      EscalationStatus @default(PENDING)
  reason      String?
  frozenUntil DateTime?
  createdAt   DateTime         @default(now())
  updatedAt   DateTime         @updatedAt

  @@index([userId])
  @@index([status])
  @@map("escalations")
}

model SystemPrompt {
  id        String   @id @default(uuid())
  tier      UserTier @unique // Corrigé pour s'aligner sur UserTier
  content   String   @db.Text
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@map("system_prompts")
}
```
