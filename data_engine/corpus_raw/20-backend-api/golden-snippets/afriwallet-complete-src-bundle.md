# AfriWallet Backend — Source TypeScript Complete Bundle

> Fichiers sous `afriwallet_codebase/src/` pour entrainement MoE MUNTU.

## `src/app.controller.spec.ts`

```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { AppController } from './app.controller';
import { AppService } from './app.service';

describe('AppController', () => {
  let appController: AppController;

  beforeEach(async () => {
    const app: TestingModule = await Test.createTestingModule({
      controllers: [AppController],
      providers: [AppService],
    }).compile();

    appController = app.get<AppController>(AppController);
  });

  describe('root', () => {
    it('should return "Hello World!"', () => {
      expect(appController.getHello()).toBe('Hello World!');
    });
  });
});

```

## `src/app.controller.ts`

```typescript
import { Controller, Get } from '@nestjs/common';
import { AppService } from './app.service';

@Controller()
export class AppController {
  constructor(private readonly appService: AppService) {}

  @Get()
  getHello(): string {
    return this.appService.getHello();
  }
}

```

## `src/app.module.ts`

```typescript
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { PrismaModule } from './prisma/prisma.module';
import { UsersModule } from './users/users.module';
import { WebhooksModule } from './webhooks/webhooks.module';
import { VirtualCardsModule } from './virtual-cards/virtual-cards.module';
import { WalletsModule } from './wallets/wallets.module';
import { AuthModule } from './auth/auth.module';
import { KycModule } from './kyc/kyc.module';
import { PaymentsModule } from './payments/payments.module';
import { MaintenanceModule } from './maintenance/maintenance.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    PrismaModule,
    UsersModule,
    WebhooksModule,
    VirtualCardsModule,
    WalletsModule,
    AuthModule,
    KycModule,
    PaymentsModule,
    MaintenanceModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}

```

## `src/app.service.ts`

```typescript
import { Injectable } from '@nestjs/common';

@Injectable()
export class AppService {
  getHello(): string {
    return 'Hello World!';
  }
}

```

## `src/auth/auth.controller.ts`

```typescript
import { Body, Controller, Post } from '@nestjs/common';
import { IsNotEmpty, IsString } from 'class-validator';
import { AuthService } from './auth.service';
import { Throttle } from '@nestjs/throttler';

class RequestOtpDto {
  @IsString()
  @IsNotEmpty()
  phoneNumber!: string;
}

class VerifyOtpDto {
  @IsString()
  @IsNotEmpty()
  phoneNumber!: string;

  @IsString()
  @IsNotEmpty()
  otp!: string;

  @IsString()
  @IsNotEmpty()
  pin!: string;
}

class VerifyPinDto {
  @IsString()
  @IsNotEmpty()
  phoneNumber!: string;

  @IsString()
  @IsNotEmpty()
  pin!: string;
}

@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  // Anti-abus OTP (par IP): 5/min par défaut.
  @Throttle({ default: { ttl: 60_000, limit: 5 } })
  @Post('otp/request')
  async requestOtp(@Body() body: RequestOtpDto) {
    return this.authService.requestOtp(body);
  }

  @Post('otp/verify')
  async verifyOtp(@Body() body: VerifyOtpDto) {
    return this.authService.verifyOtpAndSetPin(body);
  }

  @Post('pin/verify')
  async verifyPin(@Body() body: VerifyPinDto) {
    return this.authService.verifyPin(body.phoneNumber, body.pin);
  }

  @Throttle({ default: { ttl: 60_000, limit: 5 } })
  @Post('pin/reset/request')
  async requestPinResetOtp(@Body() body: RequestOtpDto) {
    return this.authService.requestPinResetOtp(body);
  }

  @Post('pin/reset/verify')
  async verifyOtpAndResetPin(@Body() body: VerifyOtpDto) {
    return this.authService.verifyOtpAndResetPin(body);
  }
}


```

## `src/auth/auth.module.ts`

```typescript
import { Module, OnModuleInit } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { AuthService } from './auth.service';
import { AuthController } from './auth.controller';
import { UsersModule } from '../users/users.module';
import { JwtStrategy } from './jwt.strategy';
import { SmsService } from '../providers/sms.service';
import { ThrottlerModule } from '@nestjs/throttler';
import { ConfigModule, ConfigService } from '@nestjs/config';

@Module({
  imports: [
    UsersModule,
    ConfigModule,
    PassportModule,
    ThrottlerModule.forRoot([
      // Limites globales raisonnables; on renforcera surtout l'OTP via décorateur si besoin.
      { ttl: 60_000, limit: 120 },
    ]),
    JwtModule.registerAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => {
        const secret = config.get<string>('JWT_SECRET');
        if (!secret) {
          throw new Error('JWT_SECRET is required');
        }
        const rawExpiresIn = config.get<string>('JWT_EXPIRES_IN') ?? '15m';
        // jsonwebtoken interprète les strings numériques en millisecondes.
        // Si la valeur est purement numérique (ex: "3600"), on la convertit en nombre (secondes).
        const expiresIn: string | number = /^\d+$/.test(rawExpiresIn)
        ? Number(rawExpiresIn)
        : rawExpiresIn;
        return { 
          secret, 
          signOptions: { 
            expiresIn: expiresIn as NonNullable<Parameters<typeof JwtModule.register>[0]['signOptions']>['expiresIn'] 
          }
        };
      },
    }),
  ],
  providers: [AuthService, JwtStrategy, SmsService],
  controllers: [AuthController],
  exports: [JwtModule],
})
export class AuthModule implements OnModuleInit {
  onModuleInit() {
    if (!process.env.JWT_SECRET) {
      throw new Error('JWT_SECRET is required');
    }
  }
}


```

## `src/auth/auth.service.ts`

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

## `src/auth/jwt-auth.guard.ts`

```typescript
import { Injectable } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';

@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {}


```

## `src/auth/jwt.strategy.ts`

```typescript
import { Injectable } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';

export interface JwtPayload {
  sub: string;
  phoneNumber: string;
}

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor() {
    const secret = process.env.JWT_SECRET;
    if (!secret) {
      // En prod, un fallback silencieux est dangereux.
      throw new Error('JWT_SECRET is required');
    }
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: secret,
    });
  }

  async validate(payload: JwtPayload) {
    return { userId: payload.sub, phoneNumber: payload.phoneNumber };
  }
}


```

## `src/kyc/kyc.controller.ts`

```typescript
import {
  BadRequestException,
  Body,
  Controller,
  ForbiddenException,
  Logger,
  Post,
  Req,
  UseGuards,
} from '@nestjs/common';
import {
  IsArray,
  IsBoolean,
  IsIn,
  IsNotEmpty,
  IsOptional,
  IsString,
  MaxLength,
  Matches,
  ValidateNested,
} from 'class-validator';
import { KycService } from './kyc.service';
import { SmileIdService } from '../providers/smile-id.service';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import type { Request } from 'express';
import { Type } from 'class-transformer';
import { validateSmileIdKycInput } from './smile-id-id-rules';

type AuthRequest = Request & { user?: { userId?: string; phoneNumber?: string } };

class StartKycDto {
  @IsString()
  @IsOptional()
  userId?: string;
}

class BiometricKycDto {
  @IsString()
  @IsOptional()
  userId?: string;

  @IsString()
  @IsNotEmpty()
  firstName!: string;

  @IsString()
  @IsNotEmpty()
  lastName!: string;

  @IsString()
  @IsNotEmpty()
  @MaxLength(32)
  idNumber!: string;

  @IsString()
  @IsOptional()
  bankCode?: string;

  @IsString()
  @IsOptional()
  secondaryIdNumber?: string;

  @IsString()
  @IsNotEmpty()
  @Matches(/^[A-Z]{2}$/)
  country!: string;

  @IsString()
  @IsOptional()
  @IsIn([
    'NIN',
    'NIN_V2',
    'NIN_SLIP',
    'BVN',
    'V_NIN',
    'PHONE_NUMBER',
    'VOTER_ID',
    'BANK_ACCOUNT',
    'NATIONAL_ID',
    'NATIONAL_ID_NO_PHOTO',
    'GHANA_CARD',
    'GHANA_CARD_NO_PHOTO',
    'TAX_INFORMATION',
    'ALIEN_CARD',
    'TPIN',
    'PASSPORT',
    'REFUGEE_ID',
    'RESIDENT_ID_NO_PHOTO',
  ])
  idType?: string = 'NIN';

  @IsString()
  @Matches(/^\d{4}-\d{2}-\d{2}$/)
  dob!: string; // yyyy-mm-dd

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => SmileImageDetailDto)
  imageDetails!: SmileImageDetailDto[];

  @IsOptional()
  @IsBoolean()
  returnJobStatus?: boolean;

  @IsOptional()
  @IsBoolean()
  returnHistory?: boolean;

  @IsOptional()
  @IsBoolean()
  returnImageLinks?: boolean;
}

class SmartSelfieAuthDto {
  @IsString()
  @IsOptional()
  userId?: string;

  @IsString()
  @IsOptional()
  jobId?: string;

  @IsString()
  @IsNotEmpty()
  @IsIn(['large_withdrawal', 'pin_reset', 'high_risk_device', 'wallet_recovery'])
  reason!: string;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => SmileImageDetailDto)
  imageDetails!: SmileImageDetailDto[];

  @IsOptional()
  @IsBoolean()
  returnJobStatus?: boolean;

  @IsOptional()
  @IsBoolean()
  returnHistory?: boolean;

  @IsOptional()
  @IsBoolean()
  returnImageLinks?: boolean;
}

class JobStatusDto {
  @IsString()
  @IsOptional()
  userId?: string;

  @IsString()
  @IsNotEmpty()
  jobId!: string;

  @IsOptional()
  @IsIn(['1', '2', '4', '11'])
  jobType?: string;

  @IsOptional()
  @IsBoolean()
  history?: boolean;

  @IsOptional()
  @IsBoolean()
  imageLinks?: boolean;
}

class SmartSelfieConfirmDto {
  @IsString()
  @IsNotEmpty()
  jobId!: string;

  @IsOptional()
  @IsBoolean()
  history?: boolean;

  @IsOptional()
  @IsBoolean()
  imageLinks?: boolean;
}

class IdNumberRateLimitResetDto {
  @IsString()
  @Matches(/^[A-Z]{2}$/)
  country!: string;

  @IsString()
  @IsNotEmpty()
  idType!: string;

  @IsString()
  @IsNotEmpty()
  idNumber!: string;

  @IsString()
  @IsOptional()
  bankCode?: string;

  @IsString()
  @IsOptional()
  secondaryIdNumber?: string;
}

class RequestUploadUrlDto {
  @IsString()
  @IsOptional()
  userId?: string;

  @IsString()
  @IsNotEmpty()
  @Matches(/^[A-Z]{2}$/)
  country!: string;

  @IsString()
  @IsNotEmpty()
  idType!: string;

  @IsString()
  @IsNotEmpty()
  @MaxLength(32)
  idNumber!: string;

  @IsString()
  @IsOptional()
  bankCode?: string;

  @IsString()
  @IsOptional()
  secondaryIdNumber?: string;

  @IsString()
  @Matches(/^\d{4}-\d{2}-\d{2}$/)
  dob!: string;

  @IsString()
  @IsNotEmpty()
  firstName!: string;

  @IsString()
  @IsNotEmpty()
  lastName!: string;

  @IsString()
  @IsOptional()
  fileName?: string;

  @IsOptional()
  modelParameters?: Record<string, unknown>;

  @IsString()
  @IsOptional()
  callbackUrl?: string;

  @IsOptional()
  @IsBoolean()
  retry?: boolean;

  @IsString()
  @IsOptional()
  @IsIn(['0', '1', '2'])
  sandboxResult?: string;
}

class UploadZipDto {
  @IsString()
  @IsNotEmpty()
  @Matches(/^https?:\/\/.+/)
  uploadUrl!: string;

  @IsString()
  @IsNotEmpty()
  zipBase64!: string;
}

class SmartSelfieUploadUrlDto {
  @IsString()
  @IsOptional()
  userId?: string;

  @IsString()
  @IsNotEmpty()
  @IsIn(['large_withdrawal', 'pin_reset', 'high_risk_device', 'wallet_recovery'])
  reason!: string;

  @IsString()
  @IsOptional()
  jobId?: string;

  @IsString()
  @IsOptional()
  callbackUrl?: string;

  @IsString()
  @IsOptional()
  fileName?: string;

  @IsOptional()
  modelParameters?: Record<string, unknown>;

  @IsOptional()
  @IsBoolean()
  retry?: boolean;

  @IsString()
  @IsOptional()
  @IsIn(['0', '1', '2'])
  sandboxResult?: string;
}

class DocumentVerificationDto {
  @IsString()
  @IsOptional()
  userId?: string;

  @IsString()
  @IsNotEmpty()
  @Matches(/^[A-Z]{2}$/)
  country!: string;

  @IsString()
  @IsNotEmpty()
  @IsIn(['DRIVERS_LICENSE', 'IDENTITY_CARD', 'PASSPORT', 'RESIDENT_ID', 'TAX_ID', 'TRAVEL_DOC'])
  idType!: string;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => SmileImageDetailDto)
  imageDetails!: SmileImageDetailDto[];
}

class DocumentVerificationUploadUrlDto {
  @IsString()
  @IsOptional()
  userId?: string;

  @IsString()
  @IsNotEmpty()
  @Matches(/^[A-Z]{2}$/)
  country!: string;

  @IsString()
  @IsNotEmpty()
  @IsIn(['DRIVERS_LICENSE', 'IDENTITY_CARD', 'PASSPORT', 'RESIDENT_ID', 'TAX_ID', 'TRAVEL_DOC'])
  idType!: string;

  @IsString()
  @IsOptional()
  callbackUrl?: string;

  @IsString()
  @IsOptional()
  fileName?: string;

  @IsOptional()
  modelParameters?: Record<string, unknown>;

  @IsOptional()
  @IsBoolean()
  retry?: boolean;

  @IsString()
  @IsOptional()
  @IsIn(['0', '1', '2'])
  sandboxResult?: string;
}

class SmileImageDetailDto {
  @IsNotEmpty()
  image_type_id!: number;

  @IsString()
  @IsNotEmpty()
  image!: string; // base64
}

@Controller('kyc')
export class KycController {
  private readonly logger = new Logger(KycController.name);

  constructor(
    private readonly kycService: KycService,
    private readonly smileIdService: SmileIdService,
  ) {}

  // Démarrage KYC côté backend (optionnel si tu utilises surtout le SDK Smile ID).
  @UseGuards(JwtAuthGuard)
  @Post('start')
  async start(@Req() req: AuthRequest, @Body() body: StartKycDto) {
    const authUserId = req.user?.userId;
    if (!authUserId) {
      throw new ForbiddenException('Missing authenticated user');
    }
    if (body.userId && body.userId !== authUserId) {
      throw new ForbiddenException('Cannot start KYC for another user');
    }
    return this.kycService.startKyc(authUserId);
  }

  // Signature pour le frontend (Flutter) qui utilise le SDK Smile ID.
  @Post('signature')
  async signature() {
    return this.smileIdService.generateSignatureForClient();
  }

  // Biometric KYC (à appeler depuis le backend ou après un job Smile ID spécifique).
  @UseGuards(JwtAuthGuard)
  @Post('biometric')
  async biometric(@Req() req: AuthRequest, @Body() body: BiometricKycDto) {
    const authUserId = req.user?.userId;
    if (!authUserId) {
      throw new ForbiddenException('Missing authenticated user');
    }
    if (body.userId && body.userId !== authUserId) {
      throw new ForbiddenException('Cannot run KYC for another user');
    }
    this.assertBiometricIdentityConsistency(body);

    const jobId = `kyc_${authUserId}_${Date.now()}`;

    // On ouvre la session KYC AVEC une référence corrélable au webhook (job_id Smile).
    const session = await this.kycService.openKycSession(authUserId, jobId);

    const smile = await this.smileIdService.submitBiometricKyc({
      userId: authUserId,
      jobId,
      imageDetails: body.imageDetails,
      firstName: body.firstName,
      lastName: body.lastName,
      country: body.country,
      idType: body.idType ?? 'NIN',
      idNumber: body.idNumber,
      dob: body.dob,
      bankCode: body.bankCode,
      secondaryIdNumber: body.secondaryIdNumber,
      options: {
        return_job_status: body.returnJobStatus ?? true,
        return_history: body.returnHistory ?? false,
        return_image_links: body.returnImageLinks ?? false,
      },
    });

    this.logger.log(`Biometric KYC submitted for user=${authUserId} jobId=${jobId}`);
    return { session, jobId, smile };
  }

  // REST API recommandé Smile: étape 1 => récupérer un upload_url (v1/upload)
  @UseGuards(JwtAuthGuard)
  @Post('biometric/upload-url')
  async biometricUploadUrl(@Req() req: AuthRequest, @Body() body: RequestUploadUrlDto) {
    const authUserId = req.user?.userId;
    if (!authUserId) {
      throw new ForbiddenException('Missing authenticated user');
    }
    if (body.userId && body.userId !== authUserId) {
      throw new ForbiddenException('Cannot run KYC for another user');
    }
    this.validateSmileIdInput(
      body.country,
      body.idType,
      body.idNumber,
      body.bankCode,
      body.secondaryIdNumber,
      body.dob,
    );

    const jobId = `kyc_${authUserId}_${Date.now()}`;
    const session = await this.kycService.openKycSession(authUserId, jobId);
    const upload = await this.smileIdService.requestUploadUrl({
      userId: authUserId,
      jobId,
      jobType: 1,
      callbackUrl: body.callbackUrl,
      fileName: body.fileName,
      modelParameters: body.modelParameters,
      retry: body.retry,
      extraPartnerParams: {
        country: body.country,
        id_type: body.idType,
        id_number: body.idNumber,
        first_name: body.firstName,
        last_name: body.lastName,
        dob: body.dob,
        bank_code: body.bankCode,
        secondary_id_number: body.secondaryIdNumber,
        sandbox_result: body.sandboxResult,
      },
    });
    return { session, jobId, upload };
  }

  // REST API recommandé Smile: étape 2 => upload du ZIP vers l'URL pré-signée.
  @UseGuards(JwtAuthGuard)
  @Post('biometric/upload-zip')
  async biometricUploadZip(@Body() body: UploadZipDto) {
    return this.smileIdService.uploadZipToSmile({
      uploadUrl: body.uploadUrl,
      zipBase64: body.zipBase64,
    });
  }

  // SmartSelfie Auth : endpoint pour valider une action sensible après réussite côté Smile ID.
  @UseGuards(JwtAuthGuard)
  @Post('smartselfie/auth')
  async smartselfieAuth(@Req() req: AuthRequest, @Body() body: SmartSelfieAuthDto) {
    const authUserId = req.user?.userId;
    if (!authUserId) {
      throw new ForbiddenException('Missing authenticated user');
    }
    if (body.userId && body.userId !== authUserId) {
      throw new ForbiddenException('Cannot run KYC for another user');
    }
    const normalizedReason = body.reason.trim().toLowerCase();
    if (!normalizedReason) {
      throw new BadRequestException('reason is required');
    }

    const jobId = body.jobId ?? `ssauth_${authUserId}_${normalizedReason}_${Date.now()}`;

    const session = await this.kycService.openKycSession(authUserId, jobId);

    const smile = await this.smileIdService.submitSmartSelfieAuth({
      userId: authUserId,
      jobId,
      imageDetails: body.imageDetails,
      options: {
        return_job_status: body.returnJobStatus ?? true,
        return_history: body.returnHistory ?? false,
        return_image_links: body.returnImageLinks ?? false,
      },
    });

    this.logger.log(
      `SmartSelfie auth submitted for user=${authUserId} jobId=${jobId} reason=${normalizedReason}`,
    );
    return { session, jobId, reason: normalizedReason, smile };
  }

  @UseGuards(JwtAuthGuard)
  @Post('smartselfie/auth/upload-url')
  async smartselfieAuthUploadUrl(@Req() req: AuthRequest, @Body() body: SmartSelfieUploadUrlDto) {
    const authUserId = req.user?.userId;
    if (!authUserId) {
      throw new ForbiddenException('Missing authenticated user');
    }
    if (body.userId && body.userId !== authUserId) {
      throw new ForbiddenException('Cannot run KYC for another user');
    }
    const normalizedReason = body.reason.trim().toLowerCase();
    const jobId = body.jobId ?? `ssauth_${authUserId}_${normalizedReason}_${Date.now()}`;
    const session = await this.kycService.openKycSession(authUserId, jobId);
    const upload = await this.smileIdService.requestUploadUrl({
      userId: authUserId,
      jobId,
      jobType: 2,
      callbackUrl: body.callbackUrl,
      fileName: body.fileName,
      modelParameters: body.modelParameters,
      retry: body.retry,
      extraPartnerParams: { reason: normalizedReason, sandbox_result: body.sandboxResult },
    });
    return { session, jobId, reason: normalizedReason, upload };
  }

  @UseGuards(JwtAuthGuard)
  @Post('smartselfie/register/upload-url')
  async smartselfieRegisterUploadUrl(
    @Req() req: AuthRequest,
    @Body() body: SmartSelfieUploadUrlDto,
  ) {
    const authUserId = req.user?.userId;
    if (!authUserId) {
      throw new ForbiddenException('Missing authenticated user');
    }
    if (body.userId && body.userId !== authUserId) {
      throw new ForbiddenException('Cannot run KYC for another user');
    }
    const normalizedReason = body.reason.trim().toLowerCase();
    const jobId = body.jobId ?? `ssreg_${authUserId}_${normalizedReason}_${Date.now()}`;
    const session = await this.kycService.openKycSession(authUserId, jobId);
    const upload = await this.smileIdService.requestUploadUrl({
      userId: authUserId,
      jobId,
      jobType: 4,
      callbackUrl: body.callbackUrl,
      fileName: body.fileName,
      modelParameters: body.modelParameters,
      retry: body.retry,
      extraPartnerParams: { reason: normalizedReason, sandbox_result: body.sandboxResult },
    });
    return { session, jobId, reason: normalizedReason, upload };
  }

  @UseGuards(JwtAuthGuard)
  @Post('smartselfie/upload-zip')
  async smartselfieUploadZip(@Body() body: UploadZipDto) {
    return this.smileIdService.uploadZipToSmile({
      uploadUrl: body.uploadUrl,
      zipBase64: body.zipBase64,
    });
  }

  @UseGuards(JwtAuthGuard)
  @Post('document-verification')
  async documentVerification(@Req() req: AuthRequest, @Body() body: DocumentVerificationDto) {
    const authUserId = req.user?.userId;
    if (!authUserId) {
      throw new ForbiddenException('Missing authenticated user');
    }
    if (body.userId && body.userId !== authUserId) {
      throw new ForbiddenException('Cannot run KYC for another user');
    }
    const country = body.country.trim().toUpperCase();
    if (country !== 'CG') {
      throw new BadRequestException('This endpoint is configured for Congo (CG) only.');
    }
    const jobId = `doc_${authUserId}_${Date.now()}`;
    const session = await this.kycService.openKycSession(authUserId, jobId);
    const smile = await this.smileIdService.submitDocumentVerification({
      userId: authUserId,
      jobId,
      imageDetails: body.imageDetails,
      country,
      idType: body.idType.trim().toUpperCase(),
    });
    return { session, jobId, smile };
  }

  @UseGuards(JwtAuthGuard)
  @Post('document-verification/upload-url')
  async documentVerificationUploadUrl(
    @Req() req: AuthRequest,
    @Body() body: DocumentVerificationUploadUrlDto,
  ) {
    const authUserId = req.user?.userId;
    if (!authUserId) {
      throw new ForbiddenException('Missing authenticated user');
    }
    if (body.userId && body.userId !== authUserId) {
      throw new ForbiddenException('Cannot run KYC for another user');
    }
    const country = body.country.trim().toUpperCase();
    if (country !== 'CG') {
      throw new BadRequestException('This endpoint is configured for Congo (CG) only.');
    }
    const jobId = `doc_${authUserId}_${Date.now()}`;
    const session = await this.kycService.openKycSession(authUserId, jobId);
    const upload = await this.smileIdService.requestUploadUrl({
      userId: authUserId,
      jobId,
      jobType: 11,
      callbackUrl: body.callbackUrl,
      fileName: body.fileName ?? 'attachments.zip',
      modelParameters: body.modelParameters,
      retry: body.retry,
      extraPartnerParams: {
        country,
        id_type: body.idType.trim().toUpperCase(),
        sandbox_result: body.sandboxResult,
      },
    });
    return { session, jobId, upload };
  }

  @UseGuards(JwtAuthGuard)
  @Post('document-verification/upload-zip')
  async documentVerificationUploadZip(@Body() body: UploadZipDto) {
    return this.smileIdService.uploadZipToSmile({
      uploadUrl: body.uploadUrl,
      zipBase64: body.zipBase64,
    });
  }

  @UseGuards(JwtAuthGuard)
  @Post('utils/job-status')
  async jobStatus(@Req() req: AuthRequest, @Body() body: JobStatusDto) {
    const authUserId = req.user?.userId;
    if (!authUserId) {
      throw new ForbiddenException('Missing authenticated user');
    }
    const userId = body.userId ?? authUserId;
    if (userId !== authUserId) {
      throw new ForbiddenException('Cannot get status for another user');
    }
    const jobType =
      body.jobType && ['1', '2', '4', '11'].includes(body.jobType)
        ? (Number(body.jobType) as 1 | 2 | 4 | 11)
        : undefined;
    return this.smileIdService.getJobStatus({
      userId,
      jobId: body.jobId,
      jobType,
      history: body.history ?? false,
      imageLinks: body.imageLinks ?? false,
    });
  }

  // Confirme un job SmartSelfie (register/auth) en polling, et persist en DB
  // sans changer kycStatus (KYC légal).
  @UseGuards(JwtAuthGuard)
  @Post('smartselfie/confirm')
  async confirmSmartSelfie(@Req() req: AuthRequest, @Body() body: SmartSelfieConfirmDto) {
    const authUserId = req.user?.userId;
    if (!authUserId) {
      throw new ForbiddenException('Missing authenticated user');
    }

    const jobId = body.jobId.trim();
    const inferredJobType: 2 | 4 =
      jobId.startsWith('ssauth_') ? 2 : jobId.startsWith('ssreg_') ? 4 : 2;

    const status = (await this.smileIdService.getJobStatus({
      userId: authUserId,
      jobId,
      jobType: inferredJobType,
      history: body.history ?? false,
      imageLinks: body.imageLinks ?? false,
    })) as any;

    return this.kycService.confirmSmartSelfieJob({
      userId: authUserId,
      jobId,
      jobType: inferredJobType,
      smileStatus: status,
    });
  }

  @UseGuards(JwtAuthGuard)
  @Post('utils/id-number-rate-limit-reset')
  async resetIdRateLimit(@Body() body: IdNumberRateLimitResetDto) {
    this.validateSmileIdInput(body.country, body.idType, body.idNumber, body.bankCode, body.secondaryIdNumber);
    return this.smileIdService.resetIdNumberRateLimit({
      country: body.country.trim().toUpperCase(),
      idType: body.idType.trim().toUpperCase(),
      idNumber: body.idNumber.trim(),
    });
  }

  private assertBiometricIdentityConsistency(body: BiometricKycDto) {
    this.validateSmileIdInput(
      body.country,
      body.idType ?? 'NIN',
      body.idNumber,
      body.bankCode,
      body.secondaryIdNumber,
      body.dob,
    );
  }

  private validateSmileIdInput(
    country: string,
    idType: string,
    idNumber: string,
    bankCode?: string,
    secondaryIdNumber?: string,
    dob?: string,
  ) {
    validateSmileIdKycInput({
      country,
      idType,
      idNumber,
      bankCode,
      secondaryIdNumber,
      dob,
    });
  }
}


```

## `src/kyc/kyc.module.ts`

```typescript
import { Module } from '@nestjs/common';
import { KycService } from './kyc.service';
import { KycController } from './kyc.controller';
import { UsersModule } from '../users/users.module';
import { SmileIdService } from '../providers/smile-id.service';

@Module({
  imports: [UsersModule],
  providers: [KycService, SmileIdService],
  controllers: [KycController],
  exports: [KycService, SmileIdService],
})
export class KycModule {}


```

## `src/kyc/kyc.service.ts`

```typescript
import { Injectable, NotFoundException } from '@nestjs/common';
import { KycStatus } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { SmileIdService } from '../providers/smile-id.service';

@Injectable()
export class KycService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly smileId: SmileIdService,
  ) {}

  async openKycSession(userId: string, reference: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user) {
      throw new NotFoundException('User not found');
    }

    if (user.kycStatus === KycStatus.VERIFIED) {
      return {
        id: user.id,
        phoneNumber: user.phoneNumber,
        kycStatus: user.kycStatus,
        kycReference: user.kycReference,
      };
    }

    const updated = await this.prisma.user.update({
      where: { id: userId },
      data: {
        kycStatus: KycStatus.PENDING,
        kycReference: reference,
      },
    });

    return {
      id: updated.id,
      phoneNumber: updated.phoneNumber,
      kycStatus: updated.kycStatus,
      kycReference: updated.kycReference,
    };
  }

  async startKyc(userId: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
    });
  
    if (!user) {
      throw new NotFoundException('User not found');
    }
  
    // Empêcher relance inutile
    if (user.kycStatus === KycStatus.VERIFIED) {
      return {
        message: 'KYC déjà validé',
        status: user.kycStatus,
      };
    }

    // Flow correct: on ouvre une "session" KYC côté backend.
    // Le SDK Smile ID + le webhook décideront VERIFIED/REJECTED.
    const reference = `kyc_${userId}_${Date.now()}`;
    return this.openKycSession(userId, reference);
  }

  async getUserKycState(userId: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true,
        phoneNumber: true,
        kycStatus: true,
        kycReference: true,
      },
    });
    if (!user) {
      throw new NotFoundException('User not found');
    }
    return user;
  }

  async markKycVerified(userId: string, reference: string) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) {
      throw new NotFoundException('User not found');
    }

    if (user.kycStatus === KycStatus.VERIFIED) {
      return {
        id: user.id,
        phoneNumber: user.phoneNumber,
        kycStatus: user.kycStatus,
        kycReference: user.kycReference,
      };
    }

    const updated = await this.prisma.user.update({
      where: { id: userId },
      data: {
        kycStatus: KycStatus.VERIFIED,
        kycReference: reference,
      },
    });

    return {
      id: updated.id,
      phoneNumber: updated.phoneNumber,
      kycStatus: updated.kycStatus,
      kycReference: updated.kycReference,
    };
  }

  async markKycRejected(userId: string, reference?: string) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) {
      throw new NotFoundException('User not found');
    }

    if (user.kycStatus === KycStatus.REJECTED) {
      return {
        id: user.id,
        phoneNumber: user.phoneNumber,
        kycStatus: user.kycStatus,
        kycReference: user.kycReference,
      };
    }

    const updated = await this.prisma.user.update({
      where: { id: userId },
      data: {
        kycStatus: KycStatus.REJECTED,
        kycReference: reference ?? user.kycReference ?? null,
      },
    });

    return {
      id: updated.id,
      phoneNumber: updated.phoneNumber,
      kycStatus: updated.kycStatus,
      kycReference: updated.kycReference,
    };
  }

  async confirmSmartSelfieJob(input: {
    userId: string;
    jobId: string;
    jobType: 2 | 4;
    smileStatus: unknown;
  }) {
    const user = await this.prisma.user.findUnique({ where: { id: input.userId } });
    if (!user) {
      throw new NotFoundException('User not found');
    }

    const payload = input.smileStatus as any;
    const jobSuccess = payload?.job_success === true;
    const jobComplete = payload?.job_complete === true;
    const partner = payload?.result?.PartnerParams ?? payload?.result?.partner_params ?? null;

    // Sécurité: si Smile renvoie un user_id, on exige qu'il corresponde.
    const smileUserId = partner?.user_id ?? null;
    if (smileUserId && String(smileUserId) !== input.userId) {
      throw new NotFoundException('SmartSelfie job does not belong to authenticated user');
    }

    const reason = (partner?.reason ?? null) ? String(partner.reason) : null;

    const now = new Date();

    const updated = await this.prisma.user.update({
      where: { id: input.userId },
      data:
        input.jobType === 4
          ? {
              smartSelfieEnrolledAt: jobSuccess ? now : user.smartSelfieEnrolledAt,
              smartSelfieEnrollJobId: input.jobId,
              smartSelfieEnrollReason: reason,
            }
          : {
              smartSelfieLastAuthAt: jobComplete ? now : user.smartSelfieLastAuthAt,
              smartSelfieLastAuthJobId: input.jobId,
              smartSelfieLastAuthReason: reason,
              smartSelfieLastAuthSuccess: jobSuccess,
            },
    });

    return {
      user: {
        id: updated.id,
        phoneNumber: updated.phoneNumber,
        kycStatus: updated.kycStatus,
        kycReference: updated.kycReference,
        smartSelfieEnrolledAt: updated.smartSelfieEnrolledAt,
        smartSelfieEnrollJobId: updated.smartSelfieEnrollJobId,
        smartSelfieEnrollReason: updated.smartSelfieEnrollReason,
        smartSelfieLastAuthAt: updated.smartSelfieLastAuthAt,
        smartSelfieLastAuthJobId: updated.smartSelfieLastAuthJobId,
        smartSelfieLastAuthReason: updated.smartSelfieLastAuthReason,
        smartSelfieLastAuthSuccess: updated.smartSelfieLastAuthSuccess,
      },
      smile: {
        job_complete: payload?.job_complete ?? null,
        job_success: payload?.job_success ?? null,
        result: payload?.result ?? null,
      },
    };
  }
}


```

## `src/kyc/smile-id-id-rules.spec.ts`

```typescript
import { BadRequestException } from '@nestjs/common';
import { validateSmileIdKycInput } from './smile-id-id-rules';

describe('validateSmileIdKycInput', () => {
  it('accepts NG/NIN_V2 with 11 digits', () => {
    expect(() =>
      validateSmileIdKycInput({
        country: 'NG',
        idType: 'NIN_V2',
        idNumber: '00000000000',
      }),
    ).not.toThrow();
  });

  it('rejects unsupported country', () => {
    expect(() =>
      validateSmileIdKycInput({
        country: 'CM',
        idType: 'NATIONAL_ID',
        idNumber: '1234',
      }),
    ).toThrow(BadRequestException);
  });

  it('requires bankCode for ZM/BANK_ACCOUNT', () => {
    expect(() =>
      validateSmileIdKycInput({
        country: 'ZM',
        idType: 'BANK_ACCOUNT',
        idNumber: '0000000000000',
      }),
    ).toThrow(BadRequestException);
  });

  it('requires secondaryIdNumber and dob for UG/NATIONAL_ID_NO_PHOTO', () => {
    expect(() =>
      validateSmileIdKycInput({
        country: 'UG',
        idType: 'NATIONAL_ID_NO_PHOTO',
        idNumber: '00000000000000',
      }),
    ).toThrow(BadRequestException);
  });
});

```

## `src/kyc/smile-id-id-rules.ts`

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

## `src/main.ts`

```typescript
import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import helmet from 'helmet';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module';

(BigInt.prototype as any).toJSON = function () {
  return this.toString();
};

async function bootstrap() {
  const app = await NestFactory.create(AppModule, { rawBody: true });

  // Sécurité HTTP de base
  app.use(helmet());
  app.enableCors({
    origin: process.env.CORS_ORIGIN?.split(',') ?? '*',
    credentials: true,
  });

  // Validation globale des DTO
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    }),
  );

  const config = new DocumentBuilder()
    .setTitle('AfriWallet API')
    .setDescription(
      'API Fintech AfriWallet (users, wallets, cartes virtuelles, webhooks, KYC).',
    )
    .setVersion('1.0.0')
    .build();
  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('docs', app, document);

  await app.listen(process.env.PORT ?? 3000);
}

bootstrap();

```

## `src/maintenance/maintenance.module.ts`

```typescript
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ScheduleModule } from '@nestjs/schedule';
import { PrismaModule } from '../prisma/prisma.module';
import { MaintenanceService } from './maintenance.service';

@Module({
  imports: [ConfigModule, ScheduleModule.forRoot(), PrismaModule],
  providers: [MaintenanceService],
})
export class MaintenanceModule {}


```

## `src/maintenance/maintenance.service.ts`

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { ConfigService } from '@nestjs/config';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class MaintenanceService {
  private readonly logger = new Logger(MaintenanceService.name);

  constructor(
    private readonly prisma: PrismaService,
    private readonly config: ConfigService,
  ) {}

  private getRetentionDays(key: 'OTP_RETENTION_DAYS' | 'WEBHOOK_RETENTION_DAYS', fallback: number) {
    const raw = this.config.get<string>(key);
    const n = raw ? Number(raw) : fallback;
    if (!Number.isFinite(n) || n < 0) return fallback;
    return Math.floor(n);
  }

  // Nettoyage quotidien: OTP expirés + vieux webhooks traités (audit conservé).
  @Cron(CronExpression.EVERY_DAY_AT_2AM)
  async cleanup() {
    const now = new Date();

    const otpRetentionDays = this.getRetentionDays('OTP_RETENTION_DAYS', 7);
    const otpCutoff = new Date(now.getTime() - otpRetentionDays * 24 * 60 * 60 * 1000);

    // On garde une fenêtre de rétention (utile support). On purge les expirés trop anciens.
    const otpDeleted = await this.prisma.otpRequest.deleteMany({
      where: { expiresAt: { lt: now }, createdAt: { lt: otpCutoff } },
    });

    const webhookRetentionDays = this.getRetentionDays('WEBHOOK_RETENTION_DAYS', 30);
    const webhookCutoff = new Date(
      now.getTime() - webhookRetentionDays * 24 * 60 * 60 * 1000,
    );

    const webhookDeleted = await (this.prisma as any).webhookEvent.deleteMany({
      where: { createdAt: { lt: webhookCutoff }, processedAt: { not: null } },
    });

    this.logger.log(
      `cleanup done: otpDeleted=${otpDeleted.count} (retentionDays=${otpRetentionDays}) webhookDeleted=${webhookDeleted.count} (retentionDays=${webhookRetentionDays})`,
    );
  }
}


```

## `src/payments/payments.controller.ts`

```typescript
import { Body, Controller, Get, Param, Post, Req, UseGuards } from '@nestjs/common';
import { IsInt, IsPositive } from 'class-validator';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { PaymentsService } from './payments.service';
import type { Request } from 'express';

class InitiateMomoDepositDto {
  @IsInt()
  @IsPositive()
  amountFcfa!: number;
}

class InitiateMomoWithdrawDto {
  @IsInt()
  @IsPositive()
  amountFcfa!: number;
}

class InitiateBridgeDepositDto {
  @IsInt()
  @IsPositive()
  amountFcfa!: number;
}

type AuthRequest = Request & { user?: { userId?: string; phoneNumber?: string } };

@Controller('payments')
export class PaymentsController {
  constructor(private readonly paymentsService: PaymentsService) {}

  @UseGuards(JwtAuthGuard)
  @Post('deposit/momo')
  async initiateMomoDeposit(@Req() req: AuthRequest, @Body() body: InitiateMomoDepositDto) {
    const phoneNumber = req.user?.phoneNumber;
    if (!phoneNumber) {
      // Le JWT contient phoneNumber (payload), on l'utilise pour initier le débit.
      throw new Error('Missing authenticated phoneNumber');
    }

    return this.paymentsService.initiateMomoDeposit({
      phoneNumber,
      amountFcfa: body.amountFcfa,
    });
  }

  @UseGuards(JwtAuthGuard)
  @Post('withdraw/momo')
  async initiateMomoWithdraw(@Req() req: AuthRequest, @Body() body: InitiateMomoWithdrawDto) {
    const phoneNumber = req.user?.phoneNumber;
    if (!phoneNumber) {
      throw new Error('Missing authenticated phoneNumber');
    }

    return this.paymentsService.initiateMomoWithdraw({
      phoneNumber,
      amountFcfa: body.amountFcfa,
    });
  }

  @UseGuards(JwtAuthGuard)
  @Post('deposit/bridge')
  async initiateBridgeDeposit(@Req() req: AuthRequest, @Body() body: InitiateBridgeDepositDto) {
    const userId = req.user?.userId;
    const phoneNumber = req.user?.phoneNumber;
    if (!userId || !phoneNumber) {
      throw new Error('Missing authenticated user context');
    }
    return this.paymentsService.initiateBridgeDeposit({
      userId,
      phoneNumber,
      amountFcfa: body.amountFcfa,
    });
  }

  /**
   * Fallback robuste si le callback MTN n'est pas reçu.
   * Le referenceId correspond au X-Reference-Id utilisé lors de l'init.
   */
  @UseGuards(JwtAuthGuard)
  @Get('deposit/momo/:referenceId/status')
  async getMomoDepositStatus(
    @Param('referenceId') referenceId: string,
    @Req() req: AuthRequest,
  ) {
    const userId = req.user?.userId;
    if (!userId) {
      throw new Error('Missing authenticated userId');
    }
    return this.paymentsService.syncMomoDepositStatus({
      userId,
      referenceId,
    });
  }

  @UseGuards(JwtAuthGuard)
  @Get('withdraw/momo/:referenceId/status')
  async getMomoWithdrawStatus(
    @Param('referenceId') referenceId: string,
    @Req() req: AuthRequest,
  ) {
    const userId = req.user?.userId;
    if (!userId) {
      throw new Error('Missing authenticated userId');
    }
    return this.paymentsService.syncMomoWithdrawStatus({
      userId,
      referenceId,
    });
  }

  @UseGuards(JwtAuthGuard)
  @Get('deposit/bridge/:paymentRequestId/status')
  async getBridgeDepositStatus(
    @Param('paymentRequestId') paymentRequestId: string,
    @Req() req: AuthRequest,
  ) {
    const userId = req.user?.userId;
    if (!userId) {
      throw new Error('Missing authenticated userId');
    }
    return this.paymentsService.syncBridgeDepositStatus({
      userId,
      paymentRequestId,
    });
  }
}


```

## `src/payments/payments.module.ts`

```typescript
import { Module } from '@nestjs/common';
import { PaymentsController } from './payments.controller';
import { PaymentsService } from './payments.service';
import { PrismaModule } from '../prisma/prisma.module';
import { MtnService } from '../providers/mtn.service';
import { UsersModule } from '../users/users.module';
import { BridgePaymentsService } from '../providers/bridge-payments.service';

@Module({
  imports: [PrismaModule, UsersModule],
  controllers: [PaymentsController],
  providers: [PaymentsService, MtnService, BridgePaymentsService],
})
export class PaymentsModule {}


```

## `src/payments/payments.service.ts`

```typescript
import { BadRequestException, Injectable, InternalServerErrorException } from '@nestjs/common';
import {
  KycStatus,
  PaymentProvider,
  TransactionStatus,
  TransactionType,
} from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { MtnService } from '../providers/mtn.service';
import { BridgePaymentsService } from '../providers/bridge-payments.service';

interface InitiateMomoDepositInput {
  phoneNumber: string;
  amountFcfa: number;
}

interface InitiateMomoWithdrawInput {
  phoneNumber: string;
  amountFcfa: number;
}

interface SyncMomoDepositStatusInput {
  userId: string;
  referenceId: string;
}

interface SyncMomoWithdrawStatusInput {
  userId: string;
  referenceId: string;
}

interface InitiateBridgeDepositInput {
  userId: string;
  phoneNumber: string;
  amountFcfa: number;
}

interface SyncBridgeDepositStatusInput {
  userId: string;
  paymentRequestId: string;
}

export interface PollingStatusResponse {
  provider: string;
  referenceId?: string;
  paymentRequestId?: string;
  status: 'PENDING' | 'SUCCESS' | 'FAILED';
  providerStatus: string;
  isFinal: boolean;
  nextPollInMs: number | null;
  updatedAt: string;
  raw: unknown;
}

@Injectable()
export class PaymentsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly mtn: MtnService,
    private readonly bridge: BridgePaymentsService,
  ) {}

  async initiateMomoDeposit(input: InitiateMomoDepositInput) {
    const { phoneNumber, amountFcfa } = input;
    if (!phoneNumber || !amountFcfa || amountFcfa <= 0) {
      throw new BadRequestException('Invalid phoneNumber or amountFcfa');
    }

    const user = await this.prisma.user.findUnique({
      where: { phoneNumber },
      include: { wallets: true },
    });
    if (!user || user.wallets.length === 0) {
      throw new BadRequestException('User wallet not found');
    }
    if (user.kycStatus !== KycStatus.VERIFIED) {
      throw new BadRequestException('KYC verification required before MoMo deposit');
    }

    const wallet = user.wallets[0];

    // On initie chez MTN et on utilise referenceId comme providerTxId (idempotence webhook).
    const { referenceId, status } = await this.mtn.initiateDebit({
      phoneNumber,
      amountFcfa,
    });

    const currency = this.getMomoCurrency();

    try {
      await this.prisma.transaction.create({
        data: {
          walletId: wallet.id,
          amountFcfa: BigInt(amountFcfa),
          feeFcfa: BigInt(0),
          currency,
          description: 'Dépôt MoMo',
          type: TransactionType.CASH_IN_MOMO,
          status: TransactionStatus.PENDING,
          provider: PaymentProvider.MTN_MOMO,
          providerTxId: referenceId,
          metadata: {
            initiatedBy: 'api',
            phoneNumber,
          },
        },
      });
    } catch (err) {
      // Si la transaction existe déjà (même referenceId), on reste idempotent.
      if (typeof err === 'object' && err && 'code' in err && (err as { code?: string }).code === 'P2002') {
        return { status, referenceId };
      }
      throw new InternalServerErrorException('Failed to persist pending transaction');
    }

    return { status, referenceId };
  }

  async initiateMomoWithdraw(input: InitiateMomoWithdrawInput) {
    const { phoneNumber, amountFcfa } = input;
    if (!phoneNumber || !amountFcfa || amountFcfa <= 0) {
      throw new BadRequestException('Invalid phoneNumber or amountFcfa');
    }

    const user = await this.prisma.user.findUnique({
      where: { phoneNumber },
      include: { wallets: true },
    });
    if (!user || user.wallets.length === 0) {
      throw new BadRequestException('User wallet not found');
    }
    if (user.kycStatus !== KycStatus.VERIFIED) {
      throw new BadRequestException('KYC verification required before MoMo withdraw');
    }

    const wallet = user.wallets[0];
    const amountBigInt = BigInt(amountFcfa);
    if (wallet.balanceFcfa < amountBigInt) {
      throw new BadRequestException('Insufficient wallet balance');
    }

    const { referenceId, status } = await this.mtn.initiateTransfer({
      phoneNumber,
      amountFcfa,
    });

    const currency = this.getMomoCurrency();

    // On décrémente immédiatement le solde en "réservation" (PENDING).
    // En prod, on peut préférer une logique de ledger plus fine (hold/available).
    try {
      await this.prisma.$transaction([
        this.prisma.wallet.update({
          where: { id: wallet.id },
          data: { balanceFcfa: { decrement: amountBigInt } },
        }),
        this.prisma.transaction.create({
          data: {
            walletId: wallet.id,
            amountFcfa: amountBigInt,
            feeFcfa: BigInt(0),
            currency,
            description: 'Retrait MoMo',
            type: TransactionType.CASH_OUT_MOMO,
            status: TransactionStatus.PENDING,
            provider: PaymentProvider.MTN_MOMO,
            providerTxId: referenceId,
            metadata: {
              initiatedBy: 'api',
              phoneNumber,
            },
          },
        }),
      ]);
    } catch (err) {
      if (typeof err === 'object' && err && 'code' in err && (err as { code?: string }).code === 'P2002') {
        return { status, referenceId };
      }
      throw new InternalServerErrorException('Failed to persist pending cash-out transaction');
    }

    return { status, referenceId };
  }

  /**
   * Poll MTN status and (best-effort) sync DB for a given deposit.
   * NOTE: ceci ne remplace pas un vrai callback MTN, c'est un fallback.
   */
  async syncMomoDepositStatus(input: SyncMomoDepositStatusInput) {
    const referenceId = input.referenceId.trim();
    if (!referenceId) {
      throw new BadRequestException('referenceId is required');
    }

    const tx = await this.prisma.transaction.findUnique({
      where: { providerTxId: referenceId },
      include: { wallet: true },
    });
    if (!tx) {
      throw new BadRequestException('Transaction not found for referenceId');
    }
    if (tx.wallet.userId !== input.userId) {
      throw new BadRequestException('Transaction does not belong to authenticated user');
    }

    const status = await this.mtn.getRequestToPayStatus(referenceId);

    // On ne tente pas de mapper exhaustivement (les champs varient selon environnements).
    // On s'appuie sur les champs usuels: status + reason.
    const normalized = status as any;
    const providerStatus = String(normalized?.status ?? '').toUpperCase();

    if (providerStatus === 'SUCCESSFUL' || providerStatus === 'SUCCESS') {
      // Pour un dépôt: si tx est encore PENDING, on crédite et passe en SUCCESS.
      if (tx.status === TransactionStatus.PENDING) {
        await this.prisma.$transaction([
          this.prisma.wallet.update({
            where: { id: tx.walletId },
            data: { balanceFcfa: { increment: tx.amountFcfa } },
          }),
          this.prisma.transaction.update({
            where: { id: tx.id },
            data: {
              status: TransactionStatus.SUCCESS,
              metadata: normalized as any,
            } as any,
          }),
        ]);
      }
    } else if (providerStatus === 'FAILED' || providerStatus === 'REJECTED') {
      if (tx.status === TransactionStatus.PENDING) {
        await this.prisma.transaction.update({
          where: { id: tx.id },
          data: { status: TransactionStatus.FAILED, metadata: normalized as any } as any,
        });
      }
    }

    return this.buildPollingStatusResponse({
      provider: 'MTN_MOMO',
      referenceId,
      providerStatus,
      raw: normalized,
    });
  }

  async syncMomoWithdrawStatus(input: SyncMomoWithdrawStatusInput) {
    const referenceId = input.referenceId.trim();
    if (!referenceId) {
      throw new BadRequestException('referenceId is required');
    }

    const tx = await this.prisma.transaction.findUnique({
      where: { providerTxId: referenceId },
      include: { wallet: true },
    });
    if (!tx) {
      throw new BadRequestException('Transaction not found for referenceId');
    }
    if (tx.wallet.userId !== input.userId) {
      throw new BadRequestException('Transaction does not belong to authenticated user');
    }
    if (tx.type !== TransactionType.CASH_OUT_MOMO) {
      throw new BadRequestException('referenceId is not a MoMo cash-out transaction');
    }

    const status = await this.mtn.getTransferStatus(referenceId);
    const normalized = status as any;
    const providerStatus = String(normalized?.status ?? '').toUpperCase();

    if (providerStatus === 'SUCCESSFUL' || providerStatus === 'SUCCESS') {
      if (tx.status === TransactionStatus.PENDING) {
        await this.prisma.transaction.update({
          where: { id: tx.id },
          data: { status: TransactionStatus.SUCCESS, metadata: normalized as any } as any,
        });
      }
    } else if (providerStatus === 'FAILED' || providerStatus === 'REJECTED') {
      if (tx.status === TransactionStatus.PENDING) {
        // Compensation: recrédit si le retrait échoue.
        await this.prisma.$transaction([
          this.prisma.wallet.update({
            where: { id: tx.walletId },
            data: { balanceFcfa: { increment: tx.amountFcfa } },
          }),
          this.prisma.transaction.update({
            where: { id: tx.id },
            data: { status: TransactionStatus.FAILED, metadata: normalized as any } as any,
          }),
        ]);
      }
    }

    return this.buildPollingStatusResponse({
      provider: 'MTN_MOMO',
      referenceId,
      providerStatus,
      raw: normalized,
    });
  }

  async initiateBridgeDeposit(input: InitiateBridgeDepositInput) {
    const { userId, phoneNumber, amountFcfa } = input;
    if (!amountFcfa || amountFcfa <= 0) {
      throw new BadRequestException('Invalid amountFcfa');
    }

    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      include: { wallets: true },
    });
    if (!user || user.wallets.length === 0) {
      throw new BadRequestException('User wallet not found');
    }
    if (user.kycStatus !== KycStatus.VERIFIED) {
      throw new BadRequestException('KYC verification required before Bridge deposit');
    }

    const wallet = user.wallets[0];
    const bridgeResp = await this.bridge.createPaymentRequest({
      amount: amountFcfa,
      user: {
        firstName: 'AfriWallet',
        lastName: phoneNumber.slice(-4),
        externalReference: user.id,
      },
      label: 'Topup wallet AfriWallet',
      clientReference: `afw_${wallet.id}_${Date.now()}`,
    });

    const paymentRequestId = bridgeResp.id;
    const currency = this.bridge.getCurrency();

    try {
      await this.prisma.transaction.create({
        data: {
          walletId: wallet.id,
          amountFcfa: BigInt(amountFcfa),
          feeFcfa: BigInt(0),
          currency,
          description: 'Dépôt bancaire Bridge',
          type: TransactionType.ADJUSTMENT,
          status: TransactionStatus.PENDING,
          provider: PaymentProvider.BRIDGE,
          providerTxId: paymentRequestId,
          metadata: {
            initiatedBy: 'api',
            provider: 'bridge',
            phoneNumber,
            paymentRequestUrl: bridgeResp.url ?? null,
          },
        },
      });
    } catch (err) {
      if (typeof err === 'object' && err && 'code' in err && (err as { code?: string }).code === 'P2002') {
        return { status: 'PENDING', paymentRequestId, url: bridgeResp.url ?? null };
      }
      throw new InternalServerErrorException('Failed to persist pending Bridge transaction');
    }

    return { status: 'PENDING', paymentRequestId, url: bridgeResp.url ?? null };
  }

  async syncBridgeDepositStatus(input: SyncBridgeDepositStatusInput) {
    const paymentRequestId = input.paymentRequestId.trim();
    if (!paymentRequestId) {
      throw new BadRequestException('paymentRequestId is required');
    }

    const tx = await this.prisma.transaction.findUnique({
      where: { providerTxId: paymentRequestId },
      include: { wallet: true },
    });
    if (!tx) {
      throw new BadRequestException('Transaction not found for paymentRequestId');
    }
    if (tx.wallet.userId !== input.userId) {
      throw new BadRequestException('Transaction does not belong to authenticated user');
    }

    const status = await this.bridge.getPaymentRequest(paymentRequestId);
    const normalized = status as any;
    const providerStatus = String(normalized?.status ?? '').toUpperCase();

    if (providerStatus === 'ACSC') {
      if (tx.status === TransactionStatus.PENDING) {
        await this.prisma.$transaction([
          this.prisma.wallet.update({
            where: { id: tx.walletId },
            data: { balanceFcfa: { increment: tx.amountFcfa } },
          }),
          this.prisma.transaction.update({
            where: { id: tx.id },
            data: {
              status: TransactionStatus.SUCCESS,
              metadata: normalized as any,
            } as any,
          }),
        ]);
      }
    } else if (providerStatus === 'RJCT') {
      if (tx.status === TransactionStatus.PENDING) {
        await this.prisma.transaction.update({
          where: { id: tx.id },
          data: {
            status: TransactionStatus.FAILED,
            failureReason: String(normalized?.status_reason ?? 'RJCT'),
            metadata: normalized as any,
          } as any,
        });
      }
    }

    return this.buildPollingStatusResponse({
      provider: 'BRIDGE',
      paymentRequestId,
      providerStatus,
      raw: normalized,
    });
  }

  private getMomoCurrency(): string {
    const fromEnv = (process.env.MTN_MOMO_CURRENCY ?? '').trim();
    if (fromEnv) return fromEnv;
    const target = (process.env.MTN_MOMO_TARGET_ENVIRONMENT ?? 'sandbox').trim().toLowerCase();
    // MTN sandbox est souvent en EUR (d’après leurs use-cases). En prod, on laisse XAF par défaut.
    return target === 'sandbox' ? 'EUR' : 'XAF';
  }

  private buildPollingStatusResponse(input: {
    provider: string;
    referenceId?: string;
    paymentRequestId?: string;
    providerStatus: string;
    raw: unknown;
  }): PollingStatusResponse {
    const normalizedProviderStatus = input.providerStatus || 'UNKNOWN';
    const normalizedStatus = this.toNormalizedStatus(normalizedProviderStatus);
    const isFinal = normalizedStatus !== 'PENDING';

    return {
      provider: input.provider,
      referenceId: input.referenceId,
      paymentRequestId: input.paymentRequestId,
      status: normalizedStatus,
      providerStatus: normalizedProviderStatus,
      isFinal,
      nextPollInMs: isFinal ? null : this.getNextPollInMs(normalizedProviderStatus),
      updatedAt: new Date().toISOString(),
      raw: input.raw,
    };
  }

  private toNormalizedStatus(providerStatus: string): 'PENDING' | 'SUCCESS' | 'FAILED' {
    const s = providerStatus.toUpperCase();
    if (['SUCCESS', 'SUCCESSFUL', 'ACSC'].includes(s)) return 'SUCCESS';
    if (['FAILED', 'REJECTED', 'RJCT', 'CANC', 'CANCELLED', 'CANCELED'].includes(s)) {
      return 'FAILED';
    }
    return 'PENDING';
  }

  private getNextPollInMs(providerStatus: string): number {
    const s = providerStatus.toUpperCase();
    if (['CREA', 'ACTC'].includes(s)) return 2000;
    if (['PDNG', 'PENDING', 'UNKNOWN'].includes(s)) return 10000;
    return 30000;
  }
}


```

## `src/prisma/prisma.module.ts`

```typescript
import { Global, Module } from '@nestjs/common';
import { PrismaService } from './prisma.service';

@Global()
@Module({
  providers: [PrismaService],
  exports: [PrismaService],
})
export class PrismaModule {}


```

## `src/prisma/prisma.service.ts`

```typescript
import { Injectable, OnModuleInit, OnModuleDestroy, InternalServerErrorException } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import { PrismaPg } from '@prisma/adapter-pg';

@Injectable()
export class PrismaService
  extends PrismaClient
  implements OnModuleInit, OnModuleDestroy
{
  constructor() {
    const connectionString = process.env.DATABASE_URL;

    if (!connectionString) {
      // Erreur claire si la variable d’environnement manque
      throw new InternalServerErrorException(
        'DATABASE_URL is not defined in environment',
      );
    }

    const adapter = new PrismaPg({
      connectionString,
    });

    super({ adapter });
  }

  async onModuleInit(): Promise<void> {
    await this.$connect();
  }

  async onModuleDestroy(): Promise<void> {
    await this.$disconnect();
  }
}
```

## `src/providers/bridge-payments-webhook.service.ts`

```typescript
import { Injectable, InternalServerErrorException } from '@nestjs/common';
import { createHmac, timingSafeEqual } from 'crypto';

@Injectable()
export class BridgePaymentsWebhookService {
  private readonly secret: string;

  constructor() {
    this.secret = (process.env.BRIDGE_WEBHOOK_SECRET ?? '').trim();
  }

  private assertConfig() {
    if (!this.secret) {
      throw new InternalServerErrorException(
        'Bridge webhook configuration missing: BRIDGE_WEBHOOK_SECRET',
      );
    }
  }

  verifySignature(signatureHeader: string | undefined, rawBody: Buffer | string | undefined): boolean {
    this.assertConfig();
    if (!signatureHeader || !rawBody) return false;

    const payload = Buffer.isBuffer(rawBody) ? rawBody.toString('utf8') : rawBody;
    const expected = createHmac('sha256', this.secret).update(payload).digest('hex').toUpperCase();

    const candidates = signatureHeader
      .split(',')
      .map((entry) => entry.trim())
      .filter((entry) => entry.toLowerCase().startsWith('v1='))
      .map((entry) => entry.slice(3).trim().toUpperCase())
      .filter(Boolean);

    return candidates.some((candidate) => {
      const a = Buffer.from(candidate, 'utf8');
      const b = Buffer.from(expected, 'utf8');
      return a.length === b.length && timingSafeEqual(a, b);
    });
  }
}


```

## `src/providers/bridge-payments.service.ts`

```typescript
import { Injectable, InternalServerErrorException } from '@nestjs/common';

interface BridgePaymentUser {
  firstName: string;
  lastName: string;
  externalReference: string;
}

interface CreateBridgePaymentRequestInput {
  amount: number;
  user: BridgePaymentUser;
  label?: string;
  providerId?: number;
  clientReference?: string;
}

interface BridgePaymentsConfig {
  baseUrl: string;
  version: string;
  clientId: string;
  clientSecret: string;
  defaultProviderId: number;
  defaultCurrency: string;
  callbackBaseUrl?: string;
}

@Injectable()
export class BridgePaymentsService {
  private readonly config: BridgePaymentsConfig;

  constructor() {
    const callbackBaseUrl = (process.env.BRIDGE_CALLBACK_BASE_URL ?? '').trim();

    this.config = {
      baseUrl: (process.env.BRIDGE_API_BASE_URL ?? 'https://api.bridgeapi.io').trim(),
      version: (process.env.BRIDGE_API_VERSION ?? '2025-01-15').trim(),
      clientId: (process.env.BRIDGE_CLIENT_ID ?? '').trim(),
      clientSecret: (process.env.BRIDGE_CLIENT_SECRET ?? '').trim(),
      defaultProviderId: Number(process.env.BRIDGE_SANDBOX_PROVIDER_ID ?? '574'),
      defaultCurrency: (process.env.BRIDGE_PAYMENT_CURRENCY ?? 'EUR').trim() || 'EUR',
      callbackBaseUrl: callbackBaseUrl ? callbackBaseUrl.replace(/\/$/, '') : undefined,
    };
  }

  private assertConfig() {
    const missing: string[] = [];
    if (!this.config.clientId) missing.push('BRIDGE_CLIENT_ID');
    if (!this.config.clientSecret) missing.push('BRIDGE_CLIENT_SECRET');

    if (missing.length) {
      throw new InternalServerErrorException(
        `Bridge configuration missing: ${missing.join(', ')}`,
      );
    }
  }

  private headers(): Record<string, string> {
    return {
      'Bridge-Version': this.config.version,
      'Client-Id': this.config.clientId,
      'Client-Secret': this.config.clientSecret,
      'Content-Type': 'application/json',
    };
  }

  async createPaymentRequest(input: CreateBridgePaymentRequestInput): Promise<{ id: string; url?: string }> {
    this.assertConfig();

    const url = `${this.config.baseUrl}/v3/payment/payment-requests`;
    const callbackUrl = this.config.callbackBaseUrl
      ? `${this.config.callbackBaseUrl}/webhooks/bridge/payments`
      : undefined;

    const res = await fetch(url, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({
        callback_url: callbackUrl,
        provider_id: input.providerId ?? this.config.defaultProviderId,
        client_reference: input.clientReference,
        user: {
          first_name: input.user.firstName,
          last_name: input.user.lastName,
          external_reference: input.user.externalReference,
        },
        transactions: [
          {
            amount: input.amount,
            currency: this.config.defaultCurrency,
            label: input.label ?? 'Topup AfriWallet',
          },
        ],
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new InternalServerErrorException(
        `Bridge createPaymentRequest failed: ${res.status} ${text}`,
      );
    }

    const data = (await res.json()) as { id?: string; url?: string };
    if (!data.id) {
      throw new InternalServerErrorException(
        'Bridge createPaymentRequest: missing id in response',
      );
    }

    return { id: data.id, url: data.url };
  }

  async getPaymentRequest(paymentRequestId: string): Promise<unknown> {
    this.assertConfig();
    const id = paymentRequestId.trim();
    if (!id) {
      throw new InternalServerErrorException('Bridge getPaymentRequest: paymentRequestId is required');
    }

    const url = `${this.config.baseUrl}/v3/payment/payment-requests/${encodeURIComponent(id)}`;
    const res = await fetch(url, {
      method: 'GET',
      headers: this.headers(),
    });

    const text = await res.text();
    if (!res.ok) {
      throw new InternalServerErrorException(
        `Bridge getPaymentRequest failed: ${res.status} ${text}`,
      );
    }

    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  getCurrency(): string {
    return this.config.defaultCurrency;
  }
}


```

## `src/providers/mtn.service.ts`

```typescript
import { Injectable, InternalServerErrorException } from '@nestjs/common';
import { randomUUID } from 'crypto';

interface InitiateMomoDebitInput {
  phoneNumber: string;
  amountFcfa: number;
}

interface InitiateMomoTransferInput {
  phoneNumber: string;
  amountFcfa: number;
}

interface MtnConfig {
  baseUrl: string;
  subscriptionKey: string;
  apiUser: string;
  apiKey: string;
  tokenPath: string;
  requestToPayPath: string;
  requestToPayStatusPath: string;
  callbackBaseUrl?: string;
  currency: string;
  targetEnvironment: string;
  disbursementTokenPath: string;
  transferPath: string;
  transferStatusPath: string;
}

@Injectable()
export class MtnService {
  private readonly config: MtnConfig;

  constructor() {
    const {
      MTN_MOMO_BASE_URL,
      MTN_MOMO_SUBSCRIPTION_KEY,
      MTN_MOMO_API_USER,
      MTN_MOMO_API_KEY,
      MTN_MOMO_TOKEN_PATH,
      MTN_MOMO_REQUEST_TO_PAY_PATH,
      MTN_MOMO_REQUEST_TO_PAY_STATUS_PATH,
      MTN_MOMO_CURRENCY,
      MTN_MOMO_TARGET_ENVIRONMENT,
      MTN_MOMO_CALLBACK_BASE_URL,
      MTN_MOMO_DISBURSEMENT_TOKEN_PATH,
      MTN_MOMO_TRANSFER_PATH,
      MTN_MOMO_TRANSFER_STATUS_PATH,
    } = process.env;

    const targetEnvironment = MTN_MOMO_TARGET_ENVIRONMENT ?? 'sandbox';

    this.config = {
      baseUrl: MTN_MOMO_BASE_URL ?? 'https://sandbox.momodeveloper.mtn.com',
      subscriptionKey: MTN_MOMO_SUBSCRIPTION_KEY ?? '',
      apiUser: MTN_MOMO_API_USER ?? '',
      apiKey: MTN_MOMO_API_KEY ?? '',
      tokenPath: MTN_MOMO_TOKEN_PATH ?? '/collection/token/',
      requestToPayPath:
        MTN_MOMO_REQUEST_TO_PAY_PATH ?? '/collection/v1_0/requesttopay',
      requestToPayStatusPath:
        MTN_MOMO_REQUEST_TO_PAY_STATUS_PATH ??
        '/collection/v1_0/requesttopay/{referenceId}',
      callbackBaseUrl: MTN_MOMO_CALLBACK_BASE_URL?.replace(/\/$/, ''),
      currency:
        MTN_MOMO_CURRENCY ??
        (targetEnvironment.trim().toLowerCase() === 'sandbox' ? 'EUR' : 'XAF'),
      targetEnvironment,
      disbursementTokenPath:
        MTN_MOMO_DISBURSEMENT_TOKEN_PATH ?? '/disbursement/token/',
      transferPath: MTN_MOMO_TRANSFER_PATH ?? '/disbursement/v1_0/transfer',
      transferStatusPath:
        MTN_MOMO_TRANSFER_STATUS_PATH ??
        '/disbursement/v1_0/transfer/{referenceId}',
    };
  }

  private assertConfig() {
    const missing: string[] = [];
    if (!this.config.subscriptionKey) missing.push('MTN_MOMO_SUBSCRIPTION_KEY');
    if (!this.config.apiUser) missing.push('MTN_MOMO_API_USER');
    if (!this.config.apiKey) missing.push('MTN_MOMO_API_KEY');
    if (!this.config.targetEnvironment) missing.push('MTN_MOMO_TARGET_ENVIRONMENT');
    if (missing.length) {
      throw new InternalServerErrorException(
        `MTN MoMo configuration missing: ${missing.join(', ')}`,
      );
    }
  }

  private async getAccessToken(tokenPath: string): Promise<string> {
    this.assertConfig();

    const url = `${this.config.baseUrl}${tokenPath}`;
    const auth = Buffer.from(
      `${this.config.apiUser}:${this.config.apiKey}`,
    ).toString('base64');

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Basic ${auth}`,
        'Ocp-Apim-Subscription-Key': this.config.subscriptionKey,
      },
    });

    if (!res.ok) {
      const text = await res.text();
      throw new InternalServerErrorException(
        `MTN getAccessToken failed: ${res.status} ${text}`,
      );
    }

    const data = (await res.json()) as { access_token: string };
    if (!data.access_token) {
      throw new InternalServerErrorException(
        'MTN getAccessToken: missing access_token in response',
      );
    }
    return data.access_token;
  }

  /**
   * Collections: RequestToPay (cash-in).
   * Important: MTN est async. On récupère le statut via callback (si configuré) et/ou polling.
   */
  async initiateDebit(
    input: InitiateMomoDebitInput,
  ): Promise<{ status: 'PENDING'; referenceId: string }> {
    const { phoneNumber, amountFcfa } = input;
    const accessToken = await this.getAccessToken(this.config.tokenPath);

    const referenceId = randomUUID();
    const url = `${this.config.baseUrl}${this.config.requestToPayPath}`;

    const body = {
      amount: amountFcfa.toString(),
      currency: this.config.currency,
      externalId: referenceId,
      payer: {
        partyIdType: 'MSISDN',
        partyId: phoneNumber,
      },
      payerMessage: 'AfriWallet wallet top-up',
      payeeNote: 'AfriWallet wallet top-up',
    };

    const callbackUrl =
      this.config.callbackBaseUrl
        ? `${this.config.callbackBaseUrl}/webhooks/mtn/requesttopay/${referenceId}`
        : undefined;

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'X-Reference-Id': referenceId,
        'X-Target-Environment': this.config.targetEnvironment,
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': this.config.subscriptionKey,
        ...(callbackUrl ? { 'X-Callback-Url': callbackUrl } : {}),
      },
      body: JSON.stringify(body),
    });

    if (!res.ok && res.status !== 202) {
      const text = await res.text();
      throw new InternalServerErrorException(
        `MTN initiateDebit failed: ${res.status} ${text}`,
      );
    }

    return { status: 'PENDING', referenceId };
  }

  /**
   * Collections: get RequestToPay status (polling fallback).
   */
  async getRequestToPayStatus(referenceId: string): Promise<unknown> {
    this.assertConfig();
    const id = referenceId.trim();
    if (!id) {
      throw new InternalServerErrorException('MTN getRequestToPayStatus: referenceId is required');
    }

    const accessToken = await this.getAccessToken(this.config.tokenPath);
    const path = this.config.requestToPayStatusPath.replace('{referenceId}', encodeURIComponent(id));
    const url = `${this.config.baseUrl}${path}`;

    const res = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'X-Target-Environment': this.config.targetEnvironment,
        'Ocp-Apim-Subscription-Key': this.config.subscriptionKey,
      },
    });

    const text = await res.text();
    if (!res.ok) {
      throw new InternalServerErrorException(
        `MTN getRequestToPayStatus failed: ${res.status} ${text}`,
      );
    }
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  /**
   * Disbursements: transfer (cash-out).
   */
  async initiateTransfer(
    input: InitiateMomoTransferInput,
  ): Promise<{ status: 'PENDING'; referenceId: string }> {
    const { phoneNumber, amountFcfa } = input;
    const accessToken = await this.getAccessToken(this.config.disbursementTokenPath);

    const referenceId = randomUUID();
    const url = `${this.config.baseUrl}${this.config.transferPath}`;

    const body = {
      amount: amountFcfa.toString(),
      currency: this.config.currency,
      externalId: referenceId,
      payee: {
        partyIdType: 'MSISDN',
        partyId: phoneNumber,
      },
      payerMessage: 'AfriWallet wallet cash-out',
      payeeNote: 'AfriWallet wallet cash-out',
    };

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'X-Reference-Id': referenceId,
        'X-Target-Environment': this.config.targetEnvironment,
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': this.config.subscriptionKey,
      },
      body: JSON.stringify(body),
    });

    if (!res.ok && res.status !== 202) {
      const text = await res.text();
      throw new InternalServerErrorException(
        `MTN initiateTransfer failed: ${res.status} ${text}`,
      );
    }

    return { status: 'PENDING', referenceId };
  }

  async getTransferStatus(referenceId: string): Promise<unknown> {
    this.assertConfig();
    const id = referenceId.trim();
    if (!id) {
      throw new InternalServerErrorException('MTN getTransferStatus: referenceId is required');
    }

    const accessToken = await this.getAccessToken(this.config.disbursementTokenPath);
    const path = this.config.transferStatusPath.replace('{referenceId}', encodeURIComponent(id));
    const url = `${this.config.baseUrl}${path}`;

    const res = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'X-Target-Environment': this.config.targetEnvironment,
        'Ocp-Apim-Subscription-Key': this.config.subscriptionKey,
      },
    });

    const text = await res.text();
    if (!res.ok) {
      throw new InternalServerErrorException(
        `MTN getTransferStatus failed: ${res.status} ${text}`,
      );
    }
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }
}


```

## `src/providers/onafriq-webhook.service.ts`

```typescript
import { Injectable, InternalServerErrorException } from '@nestjs/common';

// Librairie AES256 utilisée pour valider la signature.
// eslint-disable-next-line @typescript-eslint/no-var-requires
const AES256 = require('aes-everywhere') as {
  decrypt(cipherText: string, secret: string): string;
};

@Injectable()
export class OnafriqWebhookService {
  private readonly secretKey: string;
  private readonly webhookSecret: string;

  constructor() {
    this.secretKey = process.env.ONAFRIQ_SECRET_KEY ?? '';
    this.webhookSecret = process.env.ONAFRIQ_WEBHOOK_SECRET ?? '';
  }

  private assertConfig() {
    const missing: string[] = [];
    if (!this.secretKey) missing.push('ONAFRIQ_SECRET_KEY');
    if (!this.webhookSecret) missing.push('ONAFRIQ_WEBHOOK_SECRET');
    if (missing.length) {
      throw new InternalServerErrorException(
        `Onafriq webhook configuration missing: ${missing.join(', ')}`,
      );
    }
  }

  verifySignature(xWebhookSignature: string): boolean {
    this.assertConfig();

    try {
      const decrypted = AES256.decrypt(xWebhookSignature, this.secretKey);
      return decrypted === this.webhookSecret;
    } catch {
      return false;
    }
  }
}

```

## `src/providers/onafriq.service.spec.ts`

```typescript
import { InternalServerErrorException } from '@nestjs/common';
import { OnafriqService } from './onafriq.service';

describe('OnafriqService', () => {
  const originalEnv = process.env;
  const originalFetch = global.fetch;

  beforeEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
    process.env = {
      ...originalEnv,
      ONAFRIQ_CLIENT_USERNAME: 'user',
      ONAFRIQ_CLIENT_PASSWORD: 'pass',
      ONAFRIQ_PROGRAM_ID: '123',
      ONAFRIQ_SUB_COMPANY: '111',
      ONAFRIQ_REFERRED_BY: '111',
      ONAFRIQ_IDP_BASE_URL: 'https://cards-sbx.onafriqservices.com',
      ONAFRIQ_API_BASE_URL: 'https://cards-sbx.onafriqservices.com',
      ONAFRIQ_TOKEN_PATH: '/idp/connect/token',
      ONAFRIQ_REGISTER_PERSONALIZED_PATH: '/rest/api/v1/accounts/personalized',
      ONAFRIQ_HTTP_TIMEOUT_MS: '10000',
      ONAFRIQ_HTTP_RETRY_COUNT: '1',
      ONAFRIQ_HTTP_RETRY_BACKOFF_MS: '1',
    };
  });

  afterEach(() => {
    global.fetch = originalFetch;
    process.env = originalEnv;
  });

  it('creates virtual card with OAuth token flow', async () => {
    const fetchMock = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: 'token_1', expires_in: 3600 }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          registrationAccountId: 999001,
          registrationLast4Digits: '1234',
          registrationPassCode: 'CODE7',
        }),
      } as Response);
    global.fetch = fetchMock as unknown as typeof global.fetch;

    const service = new OnafriqService();
    const result = await service.createCard({
      userId: 'usr_abc_123',
      phoneNumber: '237699887766',
      amountFcfa: 5000,
    });

    expect(result.token).toBe('999001');
    expect(result.lastFour).toBe('1234');
    expect(result.passCode).toBe('CODE7');
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('retries once on transient token error', async () => {
    const fetchMock = jest.fn()
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => 'server down',
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: 'token_2', expires_in: 3600 }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          registrationAccountId: 321,
          registrationLast4Digits: '6789',
          registrationPassCode: null,
        }),
      } as Response);
    global.fetch = fetchMock as unknown as typeof global.fetch;

    const service = new OnafriqService();
    const result = await service.createCard({
      userId: 'usr_retry',
      phoneNumber: '237612345678',
      amountFcfa: 1000,
    });

    expect(result.token).toBe('321');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('throws when Onafriq response misses identifiers', async () => {
    const fetchMock = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: 'token_3', expires_in: 3600 }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ registrationPassCode: 'X' }),
      } as Response);
    global.fetch = fetchMock as unknown as typeof global.fetch;

    const service = new OnafriqService();

    await expect(
      service.createCard({
        userId: 'usr_bad',
        phoneNumber: '237612345678',
        amountFcfa: 1000,
      }),
    ).rejects.toBeInstanceOf(InternalServerErrorException);
  });
});

```

## `src/providers/onafriq.service.ts`

```typescript
import { Injectable, InternalServerErrorException, Logger } from '@nestjs/common';

interface CreateRemoteCardInput {
  userId: string;
  phoneNumber: string;
  amountFcfa: number;
}

interface RemoteCard {
  token: string;
  lastFour: string;
  passCode: string | null;
  raw: unknown;
}

interface OnafriqConfig {
  idpBaseUrl: string;
  apiBaseUrl: string;
  tokenPath: string;
  registerPersonalizedPath: string;
  username: string;
  password: string;
  programId: string;
  countryCode: string;
  phoneCountryCode: string;
  stateRegion: string;
  city: string;
  addressLine1: string;
  idType: number;
  idValuePrefix: string;
  subCompany: number;
  referredBy: number;
  cardCurrency: string;
}

@Injectable()
export class OnafriqService {
  private readonly logger = new Logger(OnafriqService.name);
  private readonly config: OnafriqConfig;
  private accessToken: string | null = null;
  private accessTokenExpiresAtMs = 0;

  constructor() {
    const idpBaseUrl = process.env.ONAFRIQ_IDP_BASE_URL ?? 'https://cards-sbx.onafriqservices.com';
    const apiBaseUrl = process.env.ONAFRIQ_API_BASE_URL ?? 'https://cards-sbx.onafriqservices.com';
    const subCompany = Number(process.env.ONAFRIQ_SUB_COMPANY ?? '0');
    const referredBy = Number(process.env.ONAFRIQ_REFERRED_BY ?? String(subCompany || 0));
    const idType = Number(process.env.ONAFRIQ_DEFAULT_ID_TYPE ?? '4');

    this.config = {
      idpBaseUrl,
      apiBaseUrl,
      tokenPath: process.env.ONAFRIQ_TOKEN_PATH ?? '/idp/connect/token',
      registerPersonalizedPath:
        process.env.ONAFRIQ_REGISTER_PERSONALIZED_PATH ?? '/rest/api/v1/accounts/personalized',
      username: process.env.ONAFRIQ_CLIENT_USERNAME ?? '',
      password: process.env.ONAFRIQ_CLIENT_PASSWORD ?? '',
      programId: process.env.ONAFRIQ_PROGRAM_ID ?? '',
      countryCode: process.env.ONAFRIQ_DEFAULT_COUNTRY_CODE ?? 'CM',
      phoneCountryCode: process.env.ONAFRIQ_DEFAULT_PHONE_COUNTRY_CODE ?? '237',
      stateRegion: process.env.ONAFRIQ_DEFAULT_STATE_REGION ?? 'CM',
      city: process.env.ONAFRIQ_DEFAULT_CITY ?? 'Douala',
      addressLine1: process.env.ONAFRIQ_DEFAULT_ADDRESS_LINE1 ?? 'AfriWallet user',
      idType,
      idValuePrefix: process.env.ONAFRIQ_DEFAULT_ID_VALUE_PREFIX ?? 'AfriWallet',
      subCompany,
      referredBy,
      cardCurrency: process.env.ONAFRIQ_CARD_CURRENCY ?? 'XAF',
    };
  }

  private getTimeoutMs(): number {
    return Number(process.env.ONAFRIQ_HTTP_TIMEOUT_MS ?? '10000');
  }

  private getRetryCount(): number {
    return Number(process.env.ONAFRIQ_HTTP_RETRY_COUNT ?? '2');
  }

  private getRetryBackoffMs(): number {
    return Number(process.env.ONAFRIQ_HTTP_RETRY_BACKOFF_MS ?? '400');
  }

  private assertConfig() {
    const missing: string[] = [];

    if (!this.config.username) missing.push('ONAFRIQ_CLIENT_USERNAME');
    if (!this.config.password) missing.push('ONAFRIQ_CLIENT_PASSWORD');
    if (!this.config.programId) missing.push('ONAFRIQ_PROGRAM_ID');
    if (!this.config.subCompany) missing.push('ONAFRIQ_SUB_COMPANY');
    if (!this.config.referredBy) missing.push('ONAFRIQ_REFERRED_BY');

    if (missing.length) {
      throw new InternalServerErrorException(
        `Onafriq configuration missing: ${missing.join(', ')}`,
      );
    }
  }

  private getRequestId(prefix = 'zeno'): string {
    return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 1_000_000)}`;
  }

  private async sleep(ms: number): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, ms));
  }

  private isRetriableStatus(status: number): boolean {
    return status === 408 || status === 429 || status >= 500;
  }

  private async requestWithRetry(
    correlationId: string,
    url: string,
    init: RequestInit,
  ): Promise<Response> {
    const attempts = Math.max(1, this.getRetryCount() + 1);
    const timeoutMs = Math.max(1000, this.getTimeoutMs());
    let lastError: unknown = null;

    for (let attempt = 1; attempt <= attempts; attempt++) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const res = await fetch(url, {
          ...init,
          signal: controller.signal,
        });

        if (res.ok) {
          clearTimeout(timer);
          if (attempt > 1) {
            this.logger.log(
              `[${correlationId}] Onafriq request recovered on attempt ${attempt}/${attempts}`,
            );
          }
          return res;
        }

        if (!this.isRetriableStatus(res.status) || attempt === attempts) {
          clearTimeout(timer);
          return res;
        }

        this.logger.warn(
          `[${correlationId}] Onafriq request attempt ${attempt}/${attempts} failed with status ${res.status}, retrying`,
        );
      } catch (err) {
        lastError = err;
        if (attempt === attempts) {
          clearTimeout(timer);
          break;
        }
        this.logger.warn(
          `[${correlationId}] Onafriq request attempt ${attempt}/${attempts} errored (${err instanceof Error ? err.message : 'unknown error'}), retrying`,
        );
      } finally {
        clearTimeout(timer);
      }

      const delay = this.getRetryBackoffMs() * attempt;
      await this.sleep(delay);
    }

    throw new InternalServerErrorException(
      `Onafriq request failed after retries (${correlationId}): ${lastError instanceof Error ? lastError.message : 'unknown error'}`,
    );
  }

  private parsePhone(rawPhoneNumber: string): { countryCode: string; number: string; full: string } {
    const digits = rawPhoneNumber.replace(/\D/g, '');
    if (digits.length < 10) {
      throw new InternalServerErrorException('Invalid phone number for Onafriq card registration');
    }
    const configuredCc = this.config.phoneCountryCode;
    let countryCode = configuredCc;
    let number = digits;

    if (digits.startsWith(configuredCc) && digits.length > configuredCc.length + 7) {
      number = digits.slice(configuredCc.length);
    } else if (digits.length > 10) {
      countryCode = digits.slice(0, digits.length - 9);
      number = digits.slice(countryCode.length);
    }

    return { countryCode, number, full: `${countryCode}${number}` };
  }

  private formatBirthDateFromUserId(_userId: string): string {
    return process.env.ONAFRIQ_DEFAULT_BIRTH_DATE ?? '01-JAN-1990';
  }

  private buildBasicAuthHeader(): string {
    const encoded = Buffer.from(`${this.config.username}:${this.config.password}`).toString('base64');
    return `Basic ${encoded}`;
  }

  private async getAccessToken(): Promise<string> {
    const now = Date.now();
    if (this.accessToken && now < this.accessTokenExpiresAtMs - 30_000) {
      return this.accessToken;
    }

    const requestId = this.getRequestId('onafriq-token');
    const correlationId = requestId;
    const tokenUrl = `${this.config.idpBaseUrl}${this.config.tokenPath}`;
    const body = new URLSearchParams({ grant_type: 'client_credentials' });

    const res = await this.requestWithRetry(correlationId, tokenUrl, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        Authorization: this.buildBasicAuthHeader(),
        'Content-Type': 'application/x-www-form-urlencoded',
        programId: this.config.programId,
        requestId,
      },
      body: body.toString(),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new InternalServerErrorException(
        `Onafriq token request failed (${correlationId}): ${res.status} ${text}`,
      );
    }

    const data = (await res.json()) as {
      access_token?: string;
      expires_in?: number;
    };
    if (!data.access_token) {
      throw new InternalServerErrorException('Onafriq token response missing access_token');
    }

    const expiresInSeconds = Number(data.expires_in ?? 300);
    this.accessToken = data.access_token;
    this.accessTokenExpiresAtMs = Date.now() + Math.max(60, expiresInSeconds) * 1000;
    return this.accessToken;
  }

  private buildCardRegistrationPayload(input: CreateRemoteCardInput) {
    const phone = this.parsePhone(input.phoneNumber);
    const shortUser = input.userId.slice(-8).toUpperCase();
    const firstName = 'AfriWallet';
    const lastName = `U${shortUser}`;
    const preferredName = `${firstName} ${lastName}`.slice(0, 19);

    return {
      firstName,
      middleName: '',
      lastName,
      preferredName,
      otherAccountId: input.userId,
      otherCompanyName: 'AfriWallet',
      address1: this.config.addressLine1,
      address2: '',
      address3: '',
      city: this.config.city,
      country: this.config.countryCode,
      stateRegion: this.config.stateRegion,
      postalCode: '',
      birthDate: this.formatBirthDateFromUserId(input.userId),
      idType: this.config.idType,
      idValue: `${this.config.idValuePrefix}-${shortUser}`,
      mobilePhoneNumber: {
        countryCode: phone.countryCode,
        number: phone.number,
      },
      emailAddress: `${input.userId.slice(-12)}@afriwallet.local`,
      accountSource: 'OTHER',
      referredBy: this.config.referredBy,
      subCompany: this.config.subCompany,
      return: null,
      solId: null,
      bvn: null,
    };
  }

  async createCard(input: CreateRemoteCardInput): Promise<RemoteCard> {
    this.assertConfig();
    const requestId = this.getRequestId('onafriq-create-card');
    const correlationId = requestId;
    const token = await this.getAccessToken();
    const url = `${this.config.apiBaseUrl}${this.config.registerPersonalizedPath}`;
    const payload = this.buildCardRegistrationPayload(input);

    const res = await this.requestWithRetry(correlationId, url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        programId: this.config.programId,
        requestId,
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new InternalServerErrorException(
        `Onafriq create card failed (${correlationId}): ${res.status} ${text}`,
      );
    }

    const data = (await res.json()) as {
      registrationAccountId?: number | string;
      registrationLast4Digits?: string;
      registrationPassCode?: string | null;
    };

    const accountId = data.registrationAccountId != null ? String(data.registrationAccountId) : '';
    const lastFour = String(data.registrationLast4Digits ?? '').trim();

    if (!accountId || !lastFour) {
      throw new InternalServerErrorException(
        'Onafriq create card response missing registration identifiers',
      );
    }

    return {
      token: accountId,
      lastFour,
      passCode: data.registrationPassCode ?? null,
      raw: data,
    };
  }
}

```

## `src/providers/smile-id.service.ts`

```typescript
import { BadRequestException, Injectable, InternalServerErrorException } from '@nestjs/common';
import { Signature, WebApi } from 'smile-identity-core';

interface SmileConfig {
  baseUrl: string;
  partnerId: string;
  apiKey: string;
  signatureApiKey: string;
  callbackUrl: string;
  sidServer: number;
}

interface SmileImageDetail {
  image_type_id: number;
  image: string;
}

interface SmileJobOptions {
  return_job_status: boolean;
  return_history: boolean;
  return_image_links: boolean;
}

interface DocumentVerificationInput {
  userId: string;
  jobId?: string;
  imageDetails: SmileImageDetail[];
  country: string;
  idType: string;
  options?: Partial<SmileJobOptions>;
}

interface BiometricKycInput {
  userId: string;
  jobId?: string;
  imageDetails: SmileImageDetail[];
  firstName: string;
  lastName: string;
  country: string;
  idType: string;
  idNumber: string;
  dob: string; // yyyy-mm-dd
  bankCode?: string;
  secondaryIdNumber?: string;
  options?: Partial<SmileJobOptions>;
}

interface SmartSelfieAuthInput {
  userId: string;
  jobId?: string;
  imageDetails: SmileImageDetail[];
  options?: Partial<SmileJobOptions>;
}

interface JobStatusInput {
  userId: string;
  jobId: string;
  jobType?: 1 | 2 | 4 | 11;
  history?: boolean;
  imageLinks?: boolean;
}

interface IdNumberRateLimitResetInput {
  country: string;
  idType: string;
  idNumber: string;
}

interface RequestUploadUrlInput {
  userId: string;
  jobId: string;
  jobType: 1 | 2 | 4 | 11;
  callbackUrl?: string;
  modelParameters?: Record<string, unknown>;
  sourceSdkVersion?: string;
  fileName?: string;
  retry?: boolean;
  extraPartnerParams?: Record<string, unknown>;
}

@Injectable()
export class SmileIdService {
  private readonly config: SmileConfig;
  private readonly webApi: WebApi;

  constructor() {
    const {
      SMILE_ID_BASE_URL,
      SMILE_ID_PARTNER_ID,
      SMILE_ID_API_KEY,
      SMILE_ID_SIGNATURE_API_KEY,
      SMILE_ID_CALLBACK_URL,
      SMILE_ID_SERVER,
    } = process.env;

    this.config = {
      baseUrl: (SMILE_ID_BASE_URL ?? '').replace(/\/$/, ''),
      partnerId: SMILE_ID_PARTNER_ID ?? '',
      apiKey: SMILE_ID_API_KEY ?? '',
      signatureApiKey: SMILE_ID_SIGNATURE_API_KEY ?? '',
      callbackUrl: SMILE_ID_CALLBACK_URL ?? '',
      sidServer: Number(SMILE_ID_SERVER ?? '0'),
    };

    this.webApi = new WebApi(
      this.config.partnerId,
      this.config.callbackUrl,
      this.config.apiKey,
      this.config.sidServer,
    );
  }

  private assertConfig() {
    const missing: string[] = [];
    if (!this.config.partnerId) missing.push('SMILE_ID_PARTNER_ID');
    if (!this.config.apiKey) missing.push('SMILE_ID_API_KEY');
    if (!this.config.signatureApiKey) missing.push('SMILE_ID_SIGNATURE_API_KEY');
    if (!this.config.callbackUrl) missing.push('SMILE_ID_CALLBACK_URL');
    if (!this.config.baseUrl) missing.push('SMILE_ID_BASE_URL');
    if (missing.length) {
      throw new InternalServerErrorException(
        `Smile ID configuration missing: ${missing.join(', ')}`,
      );
    }
  }

  /**
   * Génère la signature que le frontend doit utiliser avec le SDK Smile ID.
   * Retourne timestamp ISO8601, signature, partnerId et callbackUrl.
   */
  generateSignatureForClient(): {
    timestamp: string;
    signature: string;
    partnerId: string;
    callbackUrl: string;
  } {
    this.assertConfig();

    const connection = new Signature(this.config.partnerId, this.config.signatureApiKey);
    const { timestamp: rawTimestamp, signature } = connection.generate_signature();
    const timestamp = String(rawTimestamp);

    return {
      timestamp,
      signature,
      partnerId: this.config.partnerId,
      callbackUrl: this.config.callbackUrl,
    };
  }

  /**
   * Vérifie la signature reçue depuis le webhook Smile ID.
   */
  verifyCallbackSignature(receivedSignature: string, receivedTimestamp: string): boolean {
    this.assertConfig();

    const connection = new Signature(this.config.partnerId, this.config.signatureApiKey);
    return connection.confirm_signature(receivedTimestamp, receivedSignature);
  }

  private throwFriendlyUploadError(status: number, body: any): never {
    // Smile ID renvoie souvent { code: "2215", error: "..." } quand un job existe déjà.
    if (body && String(body.code) === '2215') {
      throw new BadRequestException({
        message:
          "Smile ID: ce job_id existe déjà. Utilise un nouveau jobId, ou relance avec 'retry: true' sur l’endpoint upload-url.",
        provider: 'SMILE_ID',
        code: String(body.code),
        error: body.error ?? body.message ?? 'Job already exists',
      });
    }
    // Smile ID peut renvoyer 2209 quand un user est deja enroll et le job_type n'est pas adapte.
    if (body && String(body.code) === '2209') {
      throw new BadRequestException({
        message:
          "Smile ID: job type incompatible pour cet utilisateur (deja enrolled). Utilise un nouvel utilisateur pour Biometric KYC (job_type 1), ou bascule vers SmartSelfie (job_type 2/4) selon ton use-case.",
        provider: 'SMILE_ID',
        code: String(body.code),
        error: body.error ?? body.message ?? 'Wrong job type for enrolled user',
      });
    }
    throw new InternalServerErrorException({
      message: 'Smile ID upload URL request failed',
      status,
      body,
    });
  }

  private throwFriendlyJobStatusError(status: number, body: any): never {
    if (body && String(body.code) === '2304') {
      throw new BadRequestException({
        message:
          "Smile ID: job introuvable. Verifie le jobId, le user lie au token, et que le job a bien ete cree dans le meme environnement (test/prod).",
        provider: 'SMILE_ID',
        code: String(body.code),
        error: body.error ?? body.message ?? 'Job not found',
      });
    }
    throw new InternalServerErrorException({
      message: 'Smile ID job status request failed',
      status,
      body,
    });
  }

  /**
   * Soumet un job Enhanced Document Verification (job_type 11) via WebApi.
   * Les images doivent suivre le format officiel Smile ID (image_type_id, image).
   */
  async submitDocumentVerification(
    input: DocumentVerificationInput,
  ): Promise<unknown> {
    this.assertConfig();

    const partner_params = {
      job_id: input.jobId ?? `doc_${Date.now()}`,
      user_id: input.userId,
      job_type: 11,
    };

    const id_info = {
      country: input.country,
      id_type: input.idType,
    };

    const options: SmileJobOptions = {
      return_job_status: input.options?.return_job_status ?? true,
      return_history: input.options?.return_history ?? false,
      return_image_links: input.options?.return_image_links ?? false,
    };

    return this.webApi.submit_job(
      partner_params,
      input.imageDetails,
      id_info,
      options,
    );
  }

  /**
   * Soumet un job Biometric KYC (job_type 1) via WebApi.
   */
  async submitBiometricKyc(input: BiometricKycInput): Promise<unknown> {
    this.assertConfig();

    const partner_params = {
      job_id: input.jobId ?? `kyc_${Date.now()}`,
      user_id: input.userId,
      job_type: 1,
    };

    const id_info = {
      first_name: input.firstName,
      last_name: input.lastName,
      country: input.country,
      id_type: input.idType,
      id_number: input.idNumber,
      dob: input.dob,
      bank_code: input.bankCode,
      secondary_id_number: input.secondaryIdNumber,
      entered: 'true',
    };

    const options: SmileJobOptions = {
      return_job_status: input.options?.return_job_status ?? true,
      return_history: input.options?.return_history ?? false,
      return_image_links: input.options?.return_image_links ?? false,
    };

    return this.webApi.submit_job(
      partner_params,
      input.imageDetails,
      id_info,
      options,
    );
  }

  /**
   * Soumet un job SmartSelfie Authentication (job_type 2) via WebApi.
   */
  async submitSmartSelfieAuth(
    input: SmartSelfieAuthInput,
  ): Promise<unknown> {
    this.assertConfig();

    const partner_params = {
      job_id: input.jobId ?? `ssauth_${Date.now()}`,
      user_id: input.userId,
      job_type: 2,
    };

    const options: SmileJobOptions = {
      return_job_status: input.options?.return_job_status ?? true,
      return_history: input.options?.return_history ?? false,
      return_image_links: input.options?.return_image_links ?? false,
    };

    // SmartSelfie Auth n'a pas d'id_info spécifique, on passe un objet vide.
    return this.webApi.submit_job(
      partner_params,
      input.imageDetails,
      {},
      options,
    );
  }

  async getJobStatus(input: JobStatusInput): Promise<unknown> {
    this.assertConfig();
    const sdk = this.webApi as unknown as {
      get_job_status?: (
        partnerParams: Record<string, unknown>,
        options: Record<string, unknown>,
      ) => Promise<unknown>;
    };
    if (typeof sdk.get_job_status !== 'function') {
      throw new InternalServerErrorException('Smile ID SDK does not expose get_job_status');
    }

    const partnerParams = {
      user_id: input.userId,
      job_id: input.jobId,
      job_type: input.jobType ?? 1,
    };
    const options = {
      history: input.history ?? false,
      return_history: input.history ?? false,
      return_images: input.imageLinks ?? false,
    };
    try {
      return await sdk.get_job_status(partnerParams, options);
    } catch (error: any) {
      const status = Number(error?.response?.status ?? 500);
      const body = error?.response?.data ?? {
        message: error instanceof Error ? error.message : 'Unknown Smile ID error',
      };
      this.throwFriendlyJobStatusError(status, body);
    }
  }

  async resetIdNumberRateLimit(input: IdNumberRateLimitResetInput): Promise<unknown> {
    this.assertConfig();
    const connection = new Signature(this.config.partnerId, this.config.signatureApiKey);
    const { timestamp: rawTimestamp, signature } = connection.generate_signature();
    const timestamp = String(rawTimestamp);

    const response = await fetch(`${this.config.baseUrl}/v1/id_number_rate_limit_reset`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        signature,
        timestamp,
        partner_id: this.config.partnerId,
        country: input.country,
        id_type: input.idType,
        id_number: input.idNumber,
      }),
    });

    const payload = await response.json().catch(() => ({ success: false }));
    if (!response.ok) {
      throw new InternalServerErrorException({
        message: 'Smile ID rate limit reset failed',
        status: response.status,
        payload,
      });
    }
    return payload;
  }

  async requestUploadUrl(input: RequestUploadUrlInput): Promise<unknown> {
    this.assertConfig();
    const connection = new Signature(this.config.partnerId, this.config.signatureApiKey);
    const { timestamp: rawTimestamp, signature } = connection.generate_signature();
    const timestamp = String(rawTimestamp);

    const callbackUrl = input.callbackUrl ?? this.config.callbackUrl;
    const partnerParams = {
      job_id: input.jobId,
      user_id: input.userId,
      job_type: input.jobType,
      ...(input.extraPartnerParams ?? {}),
    };

    const payload = {
      callback_url: callbackUrl,
      model_parameters: input.modelParameters ?? {},
      partner_params: partnerParams,
      signature,
      smile_client_id: this.config.partnerId,
      source_sdk: 'rest_api',
      source_sdk_version: input.sourceSdkVersion ?? '1.0.0',
      timestamp,
      file_name: input.fileName ?? undefined,
      retry: input.retry === true ? true : undefined,
    };

    const response = await fetch(`${this.config.baseUrl}/v1/upload`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const body = await response.json().catch(() => ({ success: false }));
    if (!response.ok) {
      this.throwFriendlyUploadError(response.status, body);
    }
    return body;
  }

  async uploadZipToSmile(input: { uploadUrl: string; zipBase64: string }): Promise<{ uploaded: true }> {
    this.assertConfig();
    const uploadUrl = input.uploadUrl.trim();
    if (!uploadUrl) {
      throw new BadRequestException('uploadUrl is required');
    }
    try {
      const parsed = new URL(uploadUrl);
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        throw new BadRequestException('uploadUrl must be a valid http(s) URL');
      }
    } catch {
      throw new BadRequestException('uploadUrl must be a valid URL from the previous upload-url step');
    }

    const cleaned = input.zipBase64.replace(/\s+/g, '');
    if (!/^[A-Za-z0-9+/=]+$/.test(cleaned)) {
      throw new BadRequestException('zipBase64 must be a valid base64 string');
    }
    const binary = Buffer.from(cleaned, 'base64');
    if (!binary.length) {
      throw new BadRequestException('zipBase64 payload is empty or invalid');
    }

    const response = await fetch(uploadUrl, {
      method: 'PUT',
      headers: { 'content-type': 'application/zip' },
      body: binary,
    });

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new InternalServerErrorException({
        message: 'Smile ID ZIP upload failed',
        status: response.status,
        body,
      });
    }
    return { uploaded: true };
  }
}


```

## `src/providers/sms.service.ts`

```typescript
import { Injectable, InternalServerErrorException, Logger } from '@nestjs/common';
import Twilio from 'twilio';

interface SendSmsInput {
  to: string;
  body: string;
}

@Injectable()
export class SmsService {
  private readonly client: ReturnType<typeof Twilio> | null;
  private readonly from: string | null;
  private readonly enabled: boolean;
  private readonly logger = new Logger(SmsService.name); // Ajout d'un logger pour voir les erreurs

  constructor() {
    const sid = process.env.TWILIO_ACCOUNT_SID ?? '';
    const token = process.env.TWILIO_AUTH_TOKEN ?? '';
    const from = process.env.TWILIO_FROM ?? '';

    this.enabled = Boolean(sid && token && from);
    this.client = this.enabled ? Twilio(sid, token) : null;
    this.from = this.enabled ? from : null;
  }

  async sendSms(input: SendSmsInput): Promise<{ sent: boolean }> {
    if (!this.client || !this.from) {
      throw new InternalServerErrorException(
        'SMS provider not configured (TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_FROM)',
      );
    }

    try {
      await this.client.messages.create({
        from: this.from,
        to: input.to,
        body: input.body,
      });

      return { sent: true };
    } catch (error: any) {
      // On affiche l'erreur réelle dans la console du serveur
      this.logger.error(`Erreur Twilio (${error.code}): ${error.message}`);

      // Si on n'est pas en production, on ne bloque pas le reste de l'app
      if (process.env.NODE_ENV !== 'production') {
        this.logger.warn('⚠️ Mode DEV : Le flux continue malgré l\'échec de l\'envoi SMS.');
        return { sent: false }; 
      }

      // En production, on veut que l'erreur remonte pour avertir l'utilisateur
      throw new InternalServerErrorException(`Échec de l'envoi du SMS : ${error.message}`);
    }
  }

  isConfigured(): boolean {
    return this.enabled;
  }
}
```

## `src/users/users.controller.ts`

```typescript
import { Body, Controller, Get, Post } from '@nestjs/common';
import { IsNotEmpty, IsString } from 'class-validator';
import { UsersService } from './users.service';
import * as bcrypt from 'bcryptjs';

class RegisterUserDto {
  @IsString()
  @IsNotEmpty()
  phoneNumber!: string;

  @IsString()
  @IsNotEmpty()
  pin!: string;
}

@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Post('register')
  async register(@Body() body: RegisterUserDto) {
    const { phoneNumber, pin } = body;

    const salt = await bcrypt.genSalt(10);
    const pinHash = await bcrypt.hash(pin, salt);

    const user = await this.usersService.createUser(phoneNumber, pinHash);
    return {
      id: user.id,
      phoneNumber: user.phoneNumber,
      kycStatus: user.kycStatus,
      wallets: user.wallets.map((w) => ({
        id: w.id,
        balanceFcfa: Number(w.balanceFcfa),
      })),
    };
  }

  @Post('lookup')
  async lookup(@Body('phoneNumber') phoneNumber: string) {
    const user = await this.usersService.findByPhoneNumber(phoneNumber);
    if (!user) {
      return null;
    }

    return {
      id: user.id,
      phoneNumber: user.phoneNumber,
      kycStatus: user.kycStatus,
      wallets: user.wallets.map((w) => ({
        id: w.id,
        balanceFcfa: Number(w.balanceFcfa),
      })),
    };
  }

  @Get('health')
  health() {
    return { status: 'ok' };
  }
}


```

## `src/users/users.module.ts`

```typescript
import { Module } from '@nestjs/common';
import { UsersService } from './users.service';
import { UsersController } from './users.controller';

@Module({
  providers: [UsersService],
  controllers: [UsersController],
  exports: [UsersService],
})
export class UsersModule {}


```

## `src/users/users.service.ts`

```typescript
import { ConflictException, Injectable } from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class UsersService {
  constructor(private readonly prisma: PrismaService) {}

  findByPhoneNumber(phoneNumber: string) {
    return this.prisma.user.findUnique({
      where: { phoneNumber },
      include: { wallets: true },
    });
  }

  async createUser(phoneNumber: string, pinHash: string) {
    // UX: on renvoie un feedback clair plutôt qu'une erreur Prisma "brute".
    const existing = await this.prisma.user.findUnique({
      where: { phoneNumber },
      select: { id: true },
    });
    if (existing) {
      throw new ConflictException('Un compte existe déjà, connectez-vous.');
    }

    try {
      return await this.prisma.user.create({
        data: {
          phoneNumber,
          pinHash,
          // valeur littérale, compatible avec le type enum généré
          kycStatus: 'PENDING',
          wallets: {
            create: {
              balanceFcfa: BigInt(0),
            },
          },
        },
        include: { wallets: true },
      });
    } catch (err) {
      // Garde-fou contre les courses (2 requêtes register simultanées).
      if (err instanceof Prisma.PrismaClientKnownRequestError) {
        if (err.code === 'P2002') {
          throw new ConflictException('Un compte existe déjà, connectez-vous.');
        }
      }
      throw err;
    }
  }
}


```

## `src/virtual-cards/virtual-cards.controller.ts`

```typescript
import { Body, Controller, Post, Req, UseGuards } from '@nestjs/common';
import { IsNotEmpty, IsNumber, IsPositive, IsString } from 'class-validator';
import { VirtualCardsService } from './virtual-cards.service';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';

class CreateVirtualCardDto {
  @IsString()
  @IsNotEmpty()
  walletId!: string;

  @IsNumber()
  @IsPositive()
  amountFcfa!: number;
}

interface AuthenticatedRequest {
  user?: { userId: string };
}

@Controller('virtual-cards')
export class VirtualCardsController {
  constructor(private readonly virtualCardsService: VirtualCardsService) {}

  @UseGuards(JwtAuthGuard)
  @Post()
  async create(@Body() body: CreateVirtualCardDto, @Req() req: AuthenticatedRequest) {
    const user = req.user as { userId: string };
    return this.virtualCardsService.createVirtualCard({
      ...body,
      userId: user.userId,
      requireVerifiedKyc: true,
    });
  }
}


```

## `src/virtual-cards/virtual-cards.module.ts`

```typescript
import { Module } from '@nestjs/common';
import { VirtualCardsService } from './virtual-cards.service';
import { VirtualCardsController } from './virtual-cards.controller';
import { OnafriqService } from '../providers/onafriq.service';

@Module({
  controllers: [VirtualCardsController],
  providers: [VirtualCardsService, OnafriqService],
})
export class VirtualCardsModule {}


```

## `src/virtual-cards/virtual-cards.service.ts`

```typescript
import { BadRequestException, Injectable, NotFoundException, ForbiddenException } from '@nestjs/common';
import { CardProvider, PaymentProvider, Prisma, TransactionStatus, TransactionType } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { OnafriqService } from '../providers/onafriq.service';

interface CreateVirtualCardInput {
  walletId: string;
  amountFcfa: number;
  userId: string;
  requireVerifiedKyc?: boolean;
}

@Injectable()
export class VirtualCardsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly onafriq: OnafriqService,
  ) {}

  async createVirtualCard(input: CreateVirtualCardInput) {
    const { walletId, amountFcfa, userId, requireVerifiedKyc = true } = input;

    if (!walletId || !amountFcfa) {
      throw new BadRequestException('Missing required fields');
    }

    const wallet = await this.prisma.wallet.findFirst({
      where: { id: walletId, userId },
      include: { user: true },
    });

    if (!wallet) {
      throw new NotFoundException('Wallet not found');
    }

    if (requireVerifiedKyc && wallet.user.kycStatus !== 'VERIFIED') {
      throw new ForbiddenException('KYC must be VERIFIED to create a virtual card');
    }

    const amountBigInt = BigInt(amountFcfa);

    if (wallet.balanceFcfa < amountBigInt) {
      throw new BadRequestException('Insufficient wallet balance');
    }

    const remoteCard = await this.onafriq.createCard({
      userId: wallet.user.id,
      phoneNumber: wallet.user.phoneNumber,
      amountFcfa,
    });
    const lastFour = remoteCard.lastFour;
    const cardToken = remoteCard.token;

    const [updatedWallet, virtualCard, transaction] = await this.prisma.$transaction([
      this.prisma.wallet.update({
        where: { id: wallet.id },
        data: {
          balanceFcfa: {
            decrement: amountBigInt,
          },
        },
      }),
      this.prisma.virtualCard.create({
        data: {
          walletId: wallet.id,
          provider: CardProvider.ONAFRIQ,
          lastFour,
          cardToken,
        },
      }),
      this.prisma.transaction.create({
        data: {
          walletId: wallet.id,
          amountFcfa: amountBigInt,
          type: TransactionType.CARD_ISSUANCE_FEE,
          status: TransactionStatus.SUCCESS,
          provider: PaymentProvider.ONAFRIQ,
          providerTxId: cardToken,
          metadata: {
            onafriq: remoteCard.raw as Prisma.InputJsonValue,
            registrationPassCode: remoteCard.passCode,
          } as Prisma.InputJsonValue,
        },
      }),
    ]);

    return {
      wallet: {
        id: updatedWallet.id,
        balanceFcfa: Number(updatedWallet.balanceFcfa),
      },
      virtualCard: {
        id: virtualCard.id,
        walletId: virtualCard.walletId,
        provider: virtualCard.provider,
        lastFour: virtualCard.lastFour,
        isFrozen: virtualCard.isFrozen,
      },
      transaction: {
        id: transaction.id,
        walletId: transaction.walletId,
        amountFcfa: Number(transaction.amountFcfa),
        type: transaction.type,
        status: transaction.status,
        provider: transaction.provider,
        createdAt: transaction.createdAt,
      },
    };
  }
}


```

## `src/wallets/wallets.controller.ts`

```typescript
import { Controller, Get, Param, Req, UseGuards } from '@nestjs/common';
import { WalletsService } from './wallets.service';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';

interface AuthenticatedRequest {
  user?: { userId: string };
}

@Controller('wallets')
export class WalletsController {
  constructor(private readonly walletsService: WalletsService) {}

  @UseGuards(JwtAuthGuard)
  @Get()
  async listUserWallets(@Req() req: AuthenticatedRequest) {
    const user = req.user as { userId: string };
    return this.walletsService.listUserWallets(user.userId);
  }

  @UseGuards(JwtAuthGuard)
  @Get(':walletId')
  async getWallet(@Param('walletId') walletId: string, @Req() req: AuthenticatedRequest) {
    const user = req.user as { userId: string };
    return this.walletsService.getWalletForUser(user.userId, walletId);
  }

  @UseGuards(JwtAuthGuard)
  @Get(':walletId/transactions')
  async listTransactions(
    @Param('walletId') walletId: string,
    @Req() req: AuthenticatedRequest,
  ) {
    const user = req.user as { userId: string };
    return this.walletsService.listTransactionsForUser(user.userId, walletId);
  }
}


```

## `src/wallets/wallets.module.ts`

```typescript
import { Module } from '@nestjs/common';
import { WalletsService } from './wallets.service';
import { WalletsController } from './wallets.controller';

@Module({
  controllers: [WalletsController],
  providers: [WalletsService],
})
export class WalletsModule {}


```

## `src/wallets/wallets.service.ts`

```typescript
import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class WalletsService {
  constructor(private readonly prisma: PrismaService) {}

  async listUserWallets(userId: string) {
    const wallets = await this.prisma.wallet.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
    });

    return wallets.map((w) => ({
      id: w.id,
      balanceFcfa: Number(w.balanceFcfa),
      createdAt: w.createdAt,
    }));
  }

  async getWalletForUser(userId: string, walletId: string) {
    const wallet = await this.prisma.wallet.findFirst({
      where: { id: walletId, userId },
    });

    if (!wallet) {
      throw new NotFoundException('Wallet not found');
    }

    return {
      id: wallet.id,
      balanceFcfa: Number(wallet.balanceFcfa),
      createdAt: wallet.createdAt,
      updatedAt: wallet.updatedAt,
    };
  }

  async listTransactionsForUser(userId: string, walletId: string) {
    const wallet = await this.prisma.wallet.findFirst({
      where: { id: walletId, userId },
    });

    if (!wallet) {
      throw new NotFoundException('Wallet not found');
    }

    const transactions = await this.prisma.transaction.findMany({
      where: { walletId },
      orderBy: { createdAt: 'desc' },
    });

    return transactions.map((tx) => ({
      id: tx.id,
      walletId: tx.walletId,
      amountFcfa: Number(tx.amountFcfa),
      type: tx.type,
      status: tx.status,
      provider: tx.provider,
      providerTxId: tx.providerTxId,
      createdAt: tx.createdAt,
    }));
  }
}


```

## `src/webhooks/webhooks.controller.ts`

```typescript
import { Body, Controller, ForbiddenException, Headers, Param, Post, Put, Req } from '@nestjs/common';
import { Throttle } from '@nestjs/throttler';
import { WebhooksService } from './webhooks.service';
import { SmileIdService } from '../providers/smile-id.service';
import { OnafriqWebhookService } from '../providers/onafriq-webhook.service';
import { BridgePaymentsWebhookService } from '../providers/bridge-payments-webhook.service';
import type { Request } from 'express';

interface SmileWebhookBody {
  signature?: string;
  timestamp?: string;
  job_success?: boolean;
  result?: {
    PartnerParams?: {
      user_id?: string;
      job_id?: string;
    };
  };
}

@Controller('webhooks')
export class WebhooksController {
  constructor(
    private readonly webhooksService: WebhooksService,
    private readonly smileIdService: SmileIdService,
    private readonly onafriqWebhookService: OnafriqWebhookService,
    private readonly bridgePaymentsWebhookService: BridgePaymentsWebhookService,
  ) {}

  /**
   * Webhook MTN MoMo (Collections requesttopay callback).
   * On configure le callback URL sous la forme:
   *   {MTN_MOMO_CALLBACK_BASE_URL}/webhooks/mtn/requesttopay/{referenceId}
   * afin de pouvoir corréler de façon fiable au X-Reference-Id.
   *
   * MTN peut appeler en POST ou PUT selon l'implémentation / produit.
   */
  @Post('mtn/requesttopay/:referenceId')
  @Throttle({ default: { ttl: 60_000, limit: 300 } })
  async mtnRequestToPayCallbackPost(
    @Param('referenceId') referenceId: string,
    @Body() body: unknown,
    @Headers('x-reference-id') xReferenceId: string | undefined,
    @Req() req: Request,
  ) {
    // Durcissement optionnel: allowlist IP si configurée.
    // Le contrôle fin (proxy trust, ranges, etc.) dépendra du déploiement.
    const ip = this.getRequestIp(req);
    return this.webhooksService.handleMtnRequestToPayCallback({
      referenceId: xReferenceId ?? referenceId,
      payload: body,
      requestIp: ip,
    });
  }

  @Put('mtn/requesttopay/:referenceId')
  @Throttle({ default: { ttl: 60_000, limit: 300 } })
  async mtnRequestToPayCallbackPut(
    @Param('referenceId') referenceId: string,
    @Body() body: unknown,
    @Headers('x-reference-id') xReferenceId: string | undefined,
    @Req() req: Request,
  ) {
    const ip = this.getRequestIp(req);
    return this.webhooksService.handleMtnRequestToPayCallback({
      referenceId: xReferenceId ?? referenceId,
      payload: body,
      requestIp: ip,
    });
  }

  // Callback Smile ID -> ton backend (validation KYC).
  @Post('smile-id')
  async smileIdCallback(@Body() body: SmileWebhookBody) {
    const { signature, timestamp } = body;
    if (!signature || !timestamp) {
      throw new ForbiddenException('Missing Smile ID signature or timestamp');
    }

    // Anti-replay: on refuse les signatures trop anciennes (± 5 minutes).
    const now = Date.now();
    const ts = new Date(timestamp).getTime();
    if (!Number.isFinite(ts)) {
      throw new ForbiddenException('Invalid timestamp');
    }
    if (Math.abs(now - ts) > 5 * 60 * 1000) {
      throw new ForbiddenException('Expired signature');
    }

    const valid = this.smileIdService.verifyCallbackSignature(
      signature,
      timestamp,
    );
    if (!valid) {
      throw new ForbiddenException('Invalid Smile ID signature');
    }

    // Le service gère idempotence + audit + transitions KYC.
    return this.webhooksService.handleSmileIdWebhook(body);
  }

  // Webhook Onafriq Cards -> ton backend (événements cartes).
  @Throttle({ default: { ttl: 60_000, limit: 120 } })
  @Post('onafriq/cards')
  async onafriqCardsCallback(
    @Headers('x-webhook-signature') signature: string | undefined,
    @Body() body: unknown,
  ) {
    if (!signature) {
      throw new ForbiddenException('Missing Onafriq webhook signature');
    }

    const valid = this.onafriqWebhookService.verifySignature(signature);
    if (!valid) {
      throw new ForbiddenException('Invalid Onafriq webhook signature');
    }

    await this.webhooksService.handleOnafriqWebhook(body);
    return { received: true };
  }

  @Throttle({ default: { ttl: 60_000, limit: 180 } })
  @Post('bridge/payments')
  async bridgePaymentsCallback(
    @Headers('bridgeapi-signature') signature: string | undefined,
    @Body() body: unknown,
    @Req() req: Request & { rawBody?: Buffer },
  ) {
    const raw = req.rawBody;
    const valid = this.bridgePaymentsWebhookService.verifySignature(signature, raw);
    if (!valid) {
      throw new ForbiddenException('Invalid Bridge payments webhook signature');
    }
    return this.webhooksService.handleBridgePaymentsWebhook(body);
  }

  private getRequestIp(req: Request): string | null {
    const xff = req.headers['x-forwarded-for'];
    const firstForwarded =
      typeof xff === 'string' ? xff.split(',')[0]?.trim() : Array.isArray(xff) ? xff[0] : null;
    return firstForwarded || req.ip || (req.socket && req.socket.remoteAddress) || null;
  }
}


```

## `src/webhooks/webhooks.module.ts`

```typescript
import { Module } from '@nestjs/common';
import { WebhooksController } from './webhooks.controller';
import { WebhooksService } from './webhooks.service';
import { UsersModule } from '../users/users.module';
import { KycModule } from '../kyc/kyc.module';
import { OnafriqWebhookService } from '../providers/onafriq-webhook.service';
import { BridgePaymentsWebhookService } from '../providers/bridge-payments-webhook.service';

@Module({
  imports: [UsersModule, KycModule],
  controllers: [WebhooksController],
  providers: [WebhooksService, OnafriqWebhookService, BridgePaymentsWebhookService],
})
export class WebhooksModule {}


```

## `src/webhooks/webhooks.service.spec.ts`

```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { WebhooksService } from './webhooks.service';
import { PrismaService } from '../prisma/prisma.service';
import { UsersService } from '../users/users.service';
import { KycService } from '../kyc/kyc.service';

describe('WebhooksService (Smile ID)', () => {
  let service: WebhooksService;

  const prismaMock = {
    webhookEvent: {
      create: jest.fn(),
      update: jest.fn(),
    },
  };

  const usersServiceMock = {};

  const kycServiceMock = {
    getUserKycState: jest.fn(),
    markKycVerified: jest.fn(),
    markKycRejected: jest.fn(),
  };

  beforeEach(async () => {
    jest.clearAllMocks();
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        WebhooksService,
        { provide: PrismaService, useValue: prismaMock },
        { provide: UsersService, useValue: usersServiceMock },
        { provide: KycService, useValue: kycServiceMock },
      ],
    }).compile();

    service = module.get(WebhooksService);
  });

  it('marks user as VERIFIED when job_success is true', async () => {
    prismaMock.webhookEvent.create.mockResolvedValue({});
    prismaMock.webhookEvent.update.mockResolvedValue({});
    kycServiceMock.getUserKycState.mockResolvedValue({
      id: 'user_1',
      phoneNumber: '+234000',
      kycStatus: 'PENDING',
      kycReference: 'kyc_user_1_123',
    });
    kycServiceMock.markKycVerified.mockResolvedValue({});

    const res = await service.handleSmileIdWebhook({
      signature: 'sig',
      timestamp: new Date().toISOString(),
      job_success: true,
      result: {
        PartnerParams: { user_id: 'user_1', job_id: 'job_1' },
      },
    });

    expect(res).toEqual({ received: true });
    expect(kycServiceMock.markKycVerified).toHaveBeenCalledWith('user_1', 'kyc_user_1_123');
    expect(kycServiceMock.markKycRejected).not.toHaveBeenCalled();
  });

  it('marks user as REJECTED when job_success is false', async () => {
    prismaMock.webhookEvent.create.mockResolvedValue({});
    prismaMock.webhookEvent.update.mockResolvedValue({});
    kycServiceMock.getUserKycState.mockResolvedValue({
      id: 'user_2',
      phoneNumber: '+234111',
      kycStatus: 'PENDING',
      kycReference: 'kyc_user_2_123',
    });
    kycServiceMock.markKycRejected.mockResolvedValue({});

    const res = await service.handleSmileIdWebhook({
      signature: 'sig',
      timestamp: new Date().toISOString(),
      job_success: false,
      result: {
        PartnerParams: { user_id: 'user_2', job_id: 'job_2' },
      },
    });

    expect(res).toEqual({ received: true });
    expect(kycServiceMock.markKycRejected).toHaveBeenCalledWith('user_2', 'kyc_user_2_123');
    expect(kycServiceMock.markKycVerified).not.toHaveBeenCalled();
  });
});

```

## `src/webhooks/webhooks.service.ts`

```typescript
import {
  BadRequestException,
  ForbiddenException,
  Injectable,
  Logger,
} from '@nestjs/common';
import { PaymentProvider, Prisma, TransactionStatus, TransactionType } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { KycService } from '../kyc/kyc.service';

interface SmileWebhookBody {
  signature?: string;
  timestamp?: string;
  job_success?: boolean;
  result?: {
    PartnerParams?: {
      user_id?: string;
      job_id?: string;
    };
  };
}

@Injectable()
export class WebhooksService {
  private readonly logger = new Logger(WebhooksService.name);

  constructor(
    private readonly prisma: PrismaService,
    private readonly kycService: KycService,
  ) {}

  /**
   * Webhook MTN MoMo (Collections RequestToPay) – prod-ready path.
   * Le callback URL inclut le referenceId (X-Reference-Id) => on peut corréler en DB via providerTxId.
   *
   * Le payload exact MTN peut varier; on traite de manière tolérante en lisant `status`/`reason`.
   */
  async handleMtnRequestToPayCallback(input: { referenceId: string; payload: unknown; requestIp?: string | null }) {
    const referenceId = input.referenceId?.trim();
    if (!referenceId) {
      throw new BadRequestException('Missing referenceId');
    }

    const payload = input.payload as any;
    const providerStatus = String(payload?.status ?? '').toUpperCase();
    const reason = payload?.reason ? String(payload.reason) : null;

    // Allowlist IP optionnelle (durcissement). Format: "1.2.3.4,5.6.7.8"
    const allowlistRaw = (process.env.MTN_MOMO_WEBHOOK_IP_ALLOWLIST ?? '').trim();
    if (allowlistRaw) {
      const allowed = allowlistRaw
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const requestIp = (input.requestIp ?? '').trim();
      if (!requestIp || !allowed.includes(requestIp)) {
        this.logger.warn(`MTN callback blocked by allowlist ip=${requestIp || 'unknown'} referenceId=${referenceId}`);
        throw new ForbiddenException('MTN callback rejected');
      }
    }

    const tx = await this.prisma.transaction.findUnique({
      where: { providerTxId: referenceId },
      include: { wallet: true },
    });
    if (!tx) {
      // On renvoie 200 pour éviter les retries côté provider, mais on log l'anomalie.
      this.logger.warn(`MTN callback received for unknown referenceId=${referenceId}`);
      return { received: true };
    }

    // Audit + idempotence en base, comme Smile ID.
    const eventKey = `mtn:r2p:${referenceId}`;
    try {
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.create({
        data: {
          provider: PaymentProvider.MTN_MOMO,
          eventKey,
          userId: tx.wallet.userId,
          kycReference: null,
          payload: payload as unknown as Prisma.InputJsonValue,
        },
      });
    } catch (err) {
      if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === 'P2002') {
        this.logger.warn(`Duplicate MTN webhook ignored for eventKey=${eventKey}`);
        return { received: true };
      }
      throw err;
    }

    // Si déjà finalisée, idempotent.
    if (tx.status === TransactionStatus.SUCCESS || tx.status === TransactionStatus.FAILED) {
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { processedAt: new Date() },
      });
      return { received: true };
    }

    try {
      if (providerStatus === 'SUCCESSFUL' || providerStatus === 'SUCCESS') {
        if (tx.type === TransactionType.CASH_IN_MOMO) {
          // Dépôt: créditer le wallet et finaliser.
          await this.prisma.$transaction([
            this.prisma.wallet.update({
              where: { id: tx.walletId },
              data: { balanceFcfa: { increment: tx.amountFcfa } },
            }),
            this.prisma.transaction.update({
              where: { id: tx.id },
              data: ({
                status: TransactionStatus.SUCCESS,
                metadata: payload as unknown as Prisma.InputJsonValue,
              } as any),
            }),
          ]);
        } else if (tx.type === TransactionType.CASH_OUT_MOMO) {
          // Retrait: rien à créditer (déjà décrémenté), juste finaliser.
          await this.prisma.transaction.update({
            where: { id: tx.id },
            data: ({
              status: TransactionStatus.SUCCESS,
              metadata: payload as unknown as Prisma.InputJsonValue,
            } as any),
          });
        } else {
          await this.prisma.transaction.update({
            where: { id: tx.id },
            data: ({
              status: TransactionStatus.SUCCESS,
              metadata: payload as unknown as Prisma.InputJsonValue,
            } as any),
          });
        }

        await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
          where: { eventKey },
          data: { processedAt: new Date() },
        });
        return { received: true };
      }

      if (providerStatus === 'FAILED' || providerStatus === 'REJECTED') {
        if (tx.type === TransactionType.CASH_OUT_MOMO) {
          // Compensation: on recrédite le solde si un cash-out échoue.
          await this.prisma.$transaction([
            this.prisma.wallet.update({
              where: { id: tx.walletId },
              data: { balanceFcfa: { increment: tx.amountFcfa } },
            }),
            this.prisma.transaction.update({
              where: { id: tx.id },
              data: ({
                status: TransactionStatus.FAILED,
                failureReason: reason,
                metadata: payload as unknown as Prisma.InputJsonValue,
              } as any),
            }),
          ]);
        } else {
          await this.prisma.transaction.update({
            where: { id: tx.id },
            data: ({
              status: TransactionStatus.FAILED,
              failureReason: reason,
              metadata: payload as unknown as Prisma.InputJsonValue,
            } as any),
          });
        }

        await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
          where: { eventKey },
          data: { processedAt: new Date() },
        });
        return { received: true };
      }

      // Statut non-final => on enregistre le payload en metadata pour debug.
      await this.prisma.transaction.update({
        where: { id: tx.id },
        data: ({ metadata: payload as unknown as Prisma.InputJsonValue } as any),
      });
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { processedAt: new Date() },
      });
      return { received: true };
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown MTN webhook processing error';
      this.logger.error(`MTN webhook processing failed eventKey=${eventKey}: ${msg}`);
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { error: msg },
      });
      throw err;
    }
  }

  async handleOnafriqWebhook(payload: unknown): Promise<void> {
    const body = payload as Record<string, unknown>;
    const requestId = body.requestId != null ? String(body.requestId) : null;
    const customerId =
      body.customerId != null
        ? String(body.customerId)
        : body.accountId != null
          ? String(body.accountId)
          : null;
    const transactionId = body.transactionId != null ? String(body.transactionId) : null;
    const notificationType = body.notificationType != null ? String(body.notificationType) : 'unknown';
    const eventKey = `onafriq:${notificationType}:${requestId ?? 'no-request-id'}:${transactionId ?? customerId ?? 'unknown'}`;

    try {
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.create({
        data: {
          provider: PaymentProvider.ONAFRIQ,
          eventKey,
          userId: null,
          kycReference: null,
          payload: body as unknown as Prisma.InputJsonValue,
        },
      });
    } catch (err) {
      if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === 'P2002') {
        return;
      }
      throw err;
    }

    try {
      const lastFour =
        body.lastFourDigits != null
          ? String(body.lastFourDigits)
          : body.registrationLast4Digits != null
            ? String(body.registrationLast4Digits)
            : null;
      const cardStatus = body.cardStatus != null ? String(body.cardStatus).toUpperCase() : null;
      const shouldFreeze = cardStatus
        ? ['IA', 'LC', 'SC', 'DEACTIVATED', 'EX', 'INACTIVE', 'LOSTORSTOLEN'].includes(cardStatus)
        : null;

      if (customerId) {
        await this.prisma.virtualCard.updateMany({
          where: { cardToken: customerId },
          data: shouldFreeze == null ? {} : { isFrozen: shouldFreeze },
        });
      } else if (lastFour && shouldFreeze != null) {
        await this.prisma.virtualCard.updateMany({
          where: { lastFour },
          data: { isFrozen: shouldFreeze },
        });
      }

      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { processedAt: new Date() },
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown Onafriq webhook processing error';
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { error: msg },
      });
      throw err;
    }
  }

  async handleBridgePaymentsWebhook(payload: unknown): Promise<{ received: true }> {
    const body = payload as any;
    const type = String(body?.type ?? '');
    const content = body?.content ?? {};

    const paymentRequestId = String(content?.payment_request_id ?? '').trim();
    if (!paymentRequestId) {
      return { received: true };
    }

    const eventKey = `bridge:payments:${type}:${paymentRequestId}:${String(content?.status ?? '')}`;
    try {
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.create({
        data: {
          provider: PaymentProvider.BRIDGE,
          eventKey,
          userId: null,
          kycReference: null,
          payload: body as unknown as Prisma.InputJsonValue,
        },
      });
    } catch (err) {
      if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === 'P2002') {
        return { received: true };
      }
      throw err;
    }

    const tx = await this.prisma.transaction.findUnique({
      where: { providerTxId: paymentRequestId },
      include: { wallet: true },
    });
    if (!tx) {
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { processedAt: new Date() },
      });
      return { received: true };
    }

    const providerStatus = String(content?.status ?? '').toUpperCase();
    if (providerStatus === 'ACSC' && tx.status === TransactionStatus.PENDING) {
      await this.prisma.$transaction([
        this.prisma.wallet.update({
          where: { id: tx.walletId },
          data: { balanceFcfa: { increment: tx.amountFcfa } },
        }),
        this.prisma.transaction.update({
          where: { id: tx.id },
          data: { status: TransactionStatus.SUCCESS, metadata: body as any } as any,
        }),
      ]);
    } else if (providerStatus === 'RJCT' && tx.status === TransactionStatus.PENDING) {
      await this.prisma.transaction.update({
        where: { id: tx.id },
        data: {
          status: TransactionStatus.FAILED,
          failureReason: String(content?.status_reason ?? 'RJCT'),
          metadata: body as any,
        } as any,
      });
    } else {
      await this.prisma.transaction.update({
        where: { id: tx.id },
        data: { metadata: body as any } as any,
      });
    }

    await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
      where: { eventKey },
      data: { processedAt: new Date() },
    });
    return { received: true };
  }

  async handleSmileIdWebhook(body: SmileWebhookBody): Promise<{ received: true }> {
    const userId = body.result?.PartnerParams?.user_id ?? null;
    const jobId = body.result?.PartnerParams?.job_id ?? null;
    const signature = body.signature ?? '';
    const timestamp = body.timestamp ?? '';

    // Idempotence: job_id si présent, sinon fallback signature+timestamp+userId.
    const eventKey =
      jobId?.trim() ||
      `smile:${userId ?? 'unknown'}:${timestamp.trim()}:${signature.trim()}`;

    // Audit + idempotence en base
    try {
      const user = userId ? await this.kycService.getUserKycState(userId) : null;

      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.create({
        data: {
          provider: PaymentProvider.SMILE_ID,
          eventKey,
          userId,
          kycReference: user?.kycReference ?? null,
          payload: body as unknown as Prisma.InputJsonValue,
        },
      });
    } catch (err) {
      // Si eventKey existe déjà => on considère reçu (idempotent)
      // Prisma P2002: unique constraint failed
      if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === 'P2002') {
        this.logger.warn(`Duplicate Smile webhook ignored for eventKey=${eventKey}`);
        return { received: true };
      }
      throw err;
    }

    try {
      // Si on n'a pas de user_id, on s'arrête là (audit only).
      if (!userId) {
        await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
          where: { eventKey },
          data: { processedAt: new Date() },
        });
        this.logger.warn(`Smile webhook received without user_id eventKey=${eventKey}`);
        return { received: true };
      }

      const user = await this.kycService.getUserKycState(userId);
      if (!user.kycReference) {
        // Pas de session KYC => on garde l'event en audit mais on ne touche pas le user.
        await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
          where: { eventKey },
          data: { processedAt: new Date() },
        });
        this.logger.warn(`Smile webhook user without kycReference userId=${userId}`);
        return { received: true };
      }

      // États finaux => idempotent.
      if (user.kycStatus === 'VERIFIED' || user.kycStatus === 'REJECTED') {
        await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
          where: { eventKey },
          data: { processedAt: new Date() },
        });
        return { received: true };
      }

      if (body.job_success === true) {
        await this.kycService.markKycVerified(userId, user.kycReference);
      } else {
        await this.kycService.markKycRejected(userId, user.kycReference);
      }

      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { processedAt: new Date() },
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown webhook processing error';
      this.logger.error(`Smile webhook processing failed eventKey=${eventKey}: ${errorMessage}`);
      await (this.prisma as unknown as { webhookEvent: any }).webhookEvent.update({
        where: { eventKey },
        data: { error: errorMessage },
      });
      throw err;
    }

    return { received: true };
  }

  private toWalletResponse(wallet: { id: string; balanceFcfa: bigint }) {
    return {
      id: wallet.id,
      balanceFcfa: Number(wallet.balanceFcfa),
    };
  }

  private toTransactionResponse(tx: {
    id: string;
    walletId: string;
    amountFcfa: bigint;
    type: TransactionType;
    status: TransactionStatus;
    provider: PaymentProvider | null;
    providerTxId: string | null;
    createdAt: Date;
  }) {
    return {
      id: tx.id,
      walletId: tx.walletId,
      amountFcfa: Number(tx.amountFcfa),
      type: tx.type,
      status: tx.status,
      provider: tx.provider,
      providerTxId: tx.providerTxId,
      createdAt: tx.createdAt,
    };
  }
}


```

