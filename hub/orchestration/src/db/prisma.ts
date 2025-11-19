import { PrismaClient } from '@prisma/client';
import logger from '../utils/logger';

// Singleton pattern for Prisma client
const globalForPrisma = global as unknown as { prisma: PrismaClient };

export const prisma =
  globalForPrisma.prisma ||
  new PrismaClient({
    log: ['error', 'warn'],
  });

// Query logging disabled to avoid type issues
// Can be enabled with proper Prisma event types if needed

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

export default prisma;
