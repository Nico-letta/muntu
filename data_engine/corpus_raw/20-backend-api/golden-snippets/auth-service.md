# Golden Snippet — `src/auth/auth.service.ts`

> **Couche:** `20-backend-api` · **Source:** `afriwallet_codebase/src/auth/auth.service.ts`

OTP SMS, rate limits, PIN bcrypt, JWT.

```typescript
import {
  BadRequestException,
  Injectable,
  InternalServerErrorException,
  HttpException,
  HttpStatus,
  UnauthorizedException,
} from '@nestjs/common';
import * as bcrypt from 'bcryptjs';
import { JwtService } from '@nestjs/jwt';
import { PrismaService } from '../prisma/prisma.service';
import { UsersService } from '../users/users.service';
import { SmsService } from '../providers/sms.service';

interface RequestOtpInput {
  phoneNumber: string;
}

interface VerifyOtpInput {
  phoneNumber: string;
  otp: string;
  pin: string;
}

@Injectable()
export class AuthService {
  private readonly otpTtlMinutes: number;

  constructor(
    private readonly prisma: PrismaService,
    private readonly usersService: UsersService,
    private readonly jwtService: JwtService,
    private readonly sms: SmsService,
  ) {
    const rawOtpTtl = Number(process.env.OTP_TTL_MINUTES ?? '5');
    this.otpTtlMinutes = Number.isFinite(rawOtpTtl) && rawOtpTtl > 0 ? rawOtpTtl : 5;
  }

  async requestOtp(input: RequestOtpInput) {
    const { phoneNumber } = input;
    if (!phoneNumber) {
      throw new BadRequestException('phoneNumber is required');
    }

    const existingUser = await this.usersService.findByPhoneNumber(phoneNumber);
    if (existingUser) {
      throw new HttpException(
        'Ce numero est deja active. Utilisez le PIN pour vous connecter.',
        HttpStatus.FORBIDDEN,
      );
    }

    return this.issueOtp(phoneNumber);
  }

  async requestPinResetOtp(input: RequestOtpInput) {
    const { phoneNumber } = input;
    if (!phoneNumber) {
      throw new BadRequestException('phoneNumber is required');
    }

    const existingUser = await this.usersService.findByPhoneNumber(phoneNumber);
    if (!existingUser) {
      throw new HttpException(
        'Aucun compte actif pour ce numero. Utilisez le flux OTP d activation.',
        HttpStatus.NOT_FOUND,
      );
    }

    return this.issueOtp(phoneNumber);
  }

  private async issueOtp(phoneNumber: string) {
    const now = new Date();

    // Cooldown 60s: empêche le spam "renvoyer".
    const last = await this.prisma.otpRequest.findFirst({
      where: { phoneNumber },
      orderBy: { createdAt: 'desc' },
      select: { createdAt: true },
    });
    if (last) {
      const deltaMs = now.getTime() - last.createdAt.getTime();
      if (deltaMs < 60_000) {
        throw new HttpException(
          'Veuillez attendre 60 secondes avant de redemander un code.',
          HttpStatus.TOO_MANY_REQUESTS,
        );
      }
    }

    // Quota 5/h et 10/j (par numéro).
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    const [countHour, countDay] = await this.prisma.$transaction([
      this.prisma.otpRequest.count({ where: { phoneNumber, createdAt: { gte: oneHourAgo } } }),
      this.prisma.otpRequest.count({ where: { phoneNumber, createdAt: { gte: oneDayAgo } } }),
    ]);

    if (countHour >= 5) {
      throw new HttpException(
        'Trop de demandes de code. Réessayez dans une heure.',
        HttpStatus.TOO_MANY_REQUESTS,
      );
    }
    if (countDay >= 10) {
      throw new HttpException(
        'Trop de demandes de code aujourd’hui. Réessayez demain.',
        HttpStatus.TOO_MANY_REQUESTS,
      );
    }

    // OTP: en prod il faut un vrai générateur + envoi SMS (provider).
    // En attendant, on génère un code et on ne le renvoie jamais en production.
    const code = (Math.floor(100000 + Math.random() * 900000)).toString();

    // On garde l'historique (utile support + anti-abus). Nettoyage minimal des expirés.
    await this.prisma.otpRequest.deleteMany({
      where: { phoneNumber, expiresAt: { lt: new Date() } },
    });

    // "Le dernier l'emporte": invalider tous les OTP précédents dès qu'on en émet un nouveau.
    await this.prisma.otpRequest.updateMany({
      where: { phoneNumber, expiresAt: { gt: now } },
      data: { expiresAt: now },
    });

    await this.prisma.otpRequest.create({
      data: {
        phoneNumber,
        code,
        expiresAt: new Date(Date.now() + this.otpTtlMinutes * 60 * 1000),
      },
    });

    const isProd = process.env.NODE_ENV === 'production';

    if (isProd && !this.sms.isConfigured()) {
      throw new InternalServerErrorException('SMS provider is required in production');
    }

    if (this.sms.isConfigured()) {
      await this.sms.sendSms({
        to: phoneNumber,
        body: `Votre code AfriWallet est: ${code}`,
      });
    }

    // En API-first: en prod on ne renvoie jamais le code.
    return isProd ? { phoneNumber, sent: true } : { phoneNumber, otp: code };
  }

  async verifyOtpAndSetPin(input: VerifyOtpInput) {
    const { phoneNumber, otp, pin } = input;
    if (!phoneNumber || !otp || !pin) {
      throw new BadRequestException('Le numéro, l’OTP et le PIN sont requis.');
    }

    const existingUser = await this.usersService.findByPhoneNumber(phoneNumber);
    if (existingUser) {
      throw new HttpException(
        'Ce numero est deja active. Utilisez pin/verify ou le reset PIN.',
        HttpStatus.FORBIDDEN,
      );
    }
  
    // 1. Récupération du dernier OTP
    const otpRecord = await this.prisma.otpRequest.findFirst({
      where: { phoneNumber },
      orderBy: { createdAt: 'desc' },
    });
  
    // FEEDBACK : Si pas d'OTP en base
    if (!otpRecord) {
      throw new UnauthorizedException("Aucune session d'authentification trouvée.");
    }
  
    // 2. Vérification de l'EXPIRATION (Feedback UX Prioritaire)
    // On vérifie le temps avant le code pour informer l'utilisateur qu'il est "trop tard"
    if (otpRecord.expiresAt < new Date()) {
      await this.prisma.otpRequest.deleteMany({ where: { phoneNumber } });
      // On utilise 410 (Gone) pour dire explicitement : "C'était là, mais c'est fini"
      throw new HttpException('Le code OTP a expiré. Veuillez en demander un nouveau.', HttpStatus.GONE);
    }
  
    // 3. Vérification du BLOCAGE (Tentatives)
    if (otpRecord.attempts >= 3) {
      throw new HttpException(
        'Ce code est bloqué suite à trop de tentatives infructueuses.',
        HttpStatus.FORBIDDEN,
      );
    }
  
    // 4. Vérification de la VALIDITÉ du code
    if (otpRecord.code !== otp) {
      await this.prisma.otpRequest.update({
        where: { id: otpRecord.id },
        data: { attempts: { increment: 1 } },
      });
      // On utilise 400 (Bad Request) car c'est une erreur de saisie utilisateur
      throw new BadRequestException('Le code saisi est incorrect.');
    }
  
    // --- LOGIQUE DE SUCCÈS ---
  
    // Hachage du PIN
    const salt = await bcrypt.genSalt(10);
    const pinHash = await bcrypt.hash(pin, salt);
  
    const user = await this.usersService.createUser(phoneNumber, pinHash);
  
    // NETTOYAGE : Crucial pour la sécurité, on ne laisse aucune trace de l'OTP utilisé
    await this.prisma.otpRequest.deleteMany({
      where: { phoneNumber },
    });
  
    const accessToken = await this.signToken(user.id, user.phoneNumber);
  
    return {
      id: user.id,
      phoneNumber: user.phoneNumber,
      wallets: user.wallets.map((w) => ({
        id: w.id,
        balanceFcfa: Number(w.balanceFcfa),
      })),
      accessToken,
    };
  }

  async verifyOtpAndResetPin(input: VerifyOtpInput) {
    const { phoneNumber, otp, pin } = input;
    if (!phoneNumber || !otp || !pin) {
      throw new BadRequestException('Le numéro, l’OTP et le PIN sont requis.');
    }

    const existingUser = await this.usersService.findByPhoneNumber(phoneNumber);
    if (!existingUser) {
      throw new HttpException(
        "Aucun compte pour ce numero. Utilisez le flux OTP d activation.",
        HttpStatus.NOT_FOUND,
      );
    }

    // 1. Récupération du dernier OTP
    const otpRecord = await this.prisma.otpRequest.findFirst({
      where: { phoneNumber },
      orderBy: { createdAt: 'desc' },
    });

    if (!otpRecord) {
      throw new UnauthorizedException("Aucune session d'authentification trouvée.");
    }

    if (otpRecord.expiresAt < new Date()) {
      await this.prisma.otpRequest.deleteMany({ where: { phoneNumber } });
      throw new HttpException('Le code OTP a expiré. Veuillez en demander un nouveau.', HttpStatus.GONE);
    }

    if (otpRecord.attempts >= 3) {
      throw new HttpException(
        'Ce code est bloque suite a trop de tentatives infructueuses.',
        HttpStatus.FORBIDDEN,
      );
    }

    if (otpRecord.code !== otp) {
      await this.prisma.otpRequest.update({
        where: { id: otpRecord.id },
        data: { attempts: { increment: 1 } },
      });
      throw new BadRequestException('Le code saisi est incorrect.');
    }

    const salt = await bcrypt.genSalt(10);
    const pinHash = await bcrypt.hash(pin, salt);

    const user = await this.prisma.user.update({
      where: { id: existingUser.id },
      data: { pinHash },
      include: { wallets: true },
    });

    await this.prisma.otpRequest.deleteMany({
      where: { phoneNumber },
    });

    const accessToken = await this.signToken(user.id, user.phoneNumber);

    return {
      id: user.id,
      phoneNumber: user.phoneNumber,
      wallets: user.wallets.map((w) => ({
        id: w.id,
        balanceFcfa: Number(w.balanceFcfa),
      })),
      accessToken,
    };
  }

  async verifyPin(phoneNumber: string, pin: string) {
    const user = await this.usersService.findByPhoneNumber(phoneNumber);
    if (!user || !user.pinHash) {
      throw new UnauthorizedException('Invalid credentials');
    }
    const ok = await bcrypt.compare(pin, user.pinHash);
    if (!ok) {
      throw new UnauthorizedException('Invalid credentials');
    }

    const accessToken = await this.signToken(user.id, user.phoneNumber);

    return {
      id: user.id,
      phoneNumber: user.phoneNumber,
      accessToken,
    };
  }

  private signToken(userId: string, phoneNumber: string): Promise<string> {
    const payload = { sub: userId, phoneNumber };
    return this.jwtService.signAsync(payload);
  }
}


```
