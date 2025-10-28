import { describe, it, expect } from 'vitest';

// Validation utilities
const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const validateURL = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

const validateRequired = (value: string | null | undefined): boolean => {
  return value !== null && value !== undefined && value.trim().length > 0;
};

const validateMinLength = (value: string, minLength: number): boolean => {
  return value.length >= minLength;
};

const validateMaxLength = (value: string, maxLength: number): boolean => {
  return value.length <= maxLength;
};

const validateRange = (value: number, min: number, max: number): boolean => {
  return value >= min && value <= max;
};

const validateGitHubRepo = (fullName: string): boolean => {
  const repoRegex = /^[a-zA-Z0-9_-]+\/[a-zA-Z0-9_-]+$/;
  return repoRegex.test(fullName);
};

const sanitizeInput = (input: string): string => {
  return input.replace(/[<>]/g, '');
};

describe('Validation Utilities', () => {
  describe('validateEmail', () => {
    it('validates correct email addresses', () => {
      expect(validateEmail('test@example.com')).toBe(true);
      expect(validateEmail('user.name@domain.co.uk')).toBe(true);
      expect(validateEmail('valid+email@test.org')).toBe(true);
    });

    it('rejects invalid email addresses', () => {
      expect(validateEmail('invalid')).toBe(false);
      expect(validateEmail('missing@domain')).toBe(false);
      expect(validateEmail('@example.com')).toBe(false);
      expect(validateEmail('user@')).toBe(false);
      expect(validateEmail('user name@domain.com')).toBe(false);
    });

    it('rejects empty string', () => {
      expect(validateEmail('')).toBe(false);
    });
  });

  describe('validateURL', () => {
    it('validates correct URLs', () => {
      expect(validateURL('https://example.com')).toBe(true);
      expect(validateURL('http://localhost:3000')).toBe(true);
      expect(validateURL('https://github.com/user/repo')).toBe(true);
    });

    it('rejects invalid URLs', () => {
      expect(validateURL('not-a-url')).toBe(false);
      expect(validateURL('//missing-protocol.com')).toBe(false);
    });

    it('rejects empty string', () => {
      expect(validateURL('')).toBe(false);
    });
  });

  describe('validateRequired', () => {
    it('validates non-empty strings', () => {
      expect(validateRequired('value')).toBe(true);
      expect(validateRequired('  text  ')).toBe(true);
    });

    it('rejects empty or whitespace strings', () => {
      expect(validateRequired('')).toBe(false);
      expect(validateRequired('   ')).toBe(false);
    });

    it('rejects null and undefined', () => {
      expect(validateRequired(null)).toBe(false);
      expect(validateRequired(undefined)).toBe(false);
    });
  });

  describe('validateMinLength', () => {
    it('validates strings meeting minimum length', () => {
      expect(validateMinLength('hello', 3)).toBe(true);
      expect(validateMinLength('hello', 5)).toBe(true);
    });

    it('rejects strings shorter than minimum', () => {
      expect(validateMinLength('hi', 3)).toBe(false);
      expect(validateMinLength('', 1)).toBe(false);
    });
  });

  describe('validateMaxLength', () => {
    it('validates strings within maximum length', () => {
      expect(validateMaxLength('hello', 10)).toBe(true);
      expect(validateMaxLength('hello', 5)).toBe(true);
    });

    it('rejects strings longer than maximum', () => {
      expect(validateMaxLength('hello world', 5)).toBe(false);
      expect(validateMaxLength('too long', 3)).toBe(false);
    });
  });

  describe('validateRange', () => {
    it('validates numbers within range', () => {
      expect(validateRange(5, 0, 10)).toBe(true);
      expect(validateRange(0, 0, 10)).toBe(true);
      expect(validateRange(10, 0, 10)).toBe(true);
    });

    it('rejects numbers outside range', () => {
      expect(validateRange(-1, 0, 10)).toBe(false);
      expect(validateRange(11, 0, 10)).toBe(false);
    });
  });

  describe('validateGitHubRepo', () => {
    it('validates correct GitHub repository names', () => {
      expect(validateGitHubRepo('user/repo')).toBe(true);
      expect(validateGitHubRepo('organization/project-name')).toBe(true);
      expect(validateGitHubRepo('User_123/Repo_456')).toBe(true);
    });

    it('rejects invalid repository names', () => {
      expect(validateGitHubRepo('invalid')).toBe(false);
      expect(validateGitHubRepo('user/repo/extra')).toBe(false);
      expect(validateGitHubRepo('/repo')).toBe(false);
      expect(validateGitHubRepo('user/')).toBe(false);
      expect(validateGitHubRepo('user repo')).toBe(false);
    });
  });

  describe('sanitizeInput', () => {
    it('removes dangerous HTML tags', () => {
      expect(sanitizeInput('hello<script>alert("xss")</script>')).toBe('helloscriptalert("xss")/script');
      expect(sanitizeInput('<div>content</div>')).toBe('divcontent/div');
    });

    it('leaves safe content unchanged', () => {
      expect(sanitizeInput('normal text')).toBe('normal text');
      expect(sanitizeInput('text with (parentheses)')).toBe('text with (parentheses)');
    });

    it('handles empty string', () => {
      expect(sanitizeInput('')).toBe('');
    });
  });

  describe('Combined validation', () => {
    it('validates technology title', () => {
      const validateTechnologyTitle = (title: string): boolean => {
        return validateRequired(title) && validateMinLength(title, 2) && validateMaxLength(title, 100);
      };

      expect(validateTechnologyTitle('Python')).toBe(true);
      expect(validateTechnologyTitle('A')).toBe(false);
      expect(validateTechnologyTitle('')).toBe(false);
      expect(validateTechnologyTitle('A'.repeat(101))).toBe(false);
    });

    it('validates repository URL', () => {
      const validateRepoURL = (url: string): boolean => {
        return validateRequired(url) && validateURL(url);
      };

      expect(validateRepoURL('https://github.com/user/repo')).toBe(true);
      expect(validateRepoURL('')).toBe(false);
      expect(validateRepoURL('not-a-url')).toBe(false);
    });

    it('validates priority score', () => {
      const validatePriority = (score: number): boolean => {
        return validateRange(score, 1, 5);
      };

      expect(validatePriority(3)).toBe(true);
      expect(validatePriority(1)).toBe(true);
      expect(validatePriority(5)).toBe(true);
      expect(validatePriority(0)).toBe(false);
      expect(validatePriority(6)).toBe(false);
    });
  });
});
