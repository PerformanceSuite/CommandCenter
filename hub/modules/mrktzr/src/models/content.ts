export enum ContentType {
  SOCIAL_MEDIA_POST = 'social_media_post',
  BLOG_POST = 'blog_post',
  VIDEO_SCRIPT = 'video_script',
}

export enum ContentStatus {
  DRAFT = 'draft',
  PENDING_APPROVAL = 'pending_approval',
  APPROVED = 'approved',
  REJECTED = 'rejected',
}

export interface Content {
  id: string;
  title: string;
  body: string;
  type: ContentType;
  status: ContentStatus;
  authorId: string; // Foreign key to User
  createdAt: Date;
  updatedAt: Date;
}
