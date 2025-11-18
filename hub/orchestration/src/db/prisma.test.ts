import { describe, it, expect } from 'vitest';
import prisma from './prisma';

describe('prisma', () => {
  it('should export Prisma client instance', () => {
    expect(prisma).toBeDefined();
    expect(prisma.$connect).toBeDefined();
  });
});
