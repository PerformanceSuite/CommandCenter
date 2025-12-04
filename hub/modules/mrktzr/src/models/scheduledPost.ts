export enum ScheduledPostStatus {
  SCHEDULED = 'scheduled',
  POSTED = 'posted',
  FAILED = 'failed',
}

export interface ScheduledPost {
  id: string;
  contentId: string; // Foreign key to Content
  accountId: string; // Foreign key to SocialMediaAccount
  scheduledAt: Date;
  postedAt?: Date;
  status: ScheduledPostStatus;
  postUrl?: string; // URL of the post after it's published
  error?: string; // To log any errors on failure
  createdAt: Date;
  updatedAt: Date;
}
