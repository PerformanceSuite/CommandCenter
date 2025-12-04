export enum SocialPlatform {
  TWITTER = 'twitter',
  FACEBOOK = 'facebook',
  INSTAGRAM = 'instagram',
  LINKEDIN = 'linkedin',
  YOUTUBE = 'youtube',
}

export interface SocialMediaAccount {
  id: string;
  userId: string; // Foreign key to User
  platform: SocialPlatform;
  username: string;
  accessToken: string; // Encrypted
  refreshToken?: string; // Encrypted
  expiresAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}
