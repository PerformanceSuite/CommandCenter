export interface User {
  id: string; // Using string for UUIDs
  username: string;
  email: string;
  passwordHash: string;
  createdAt: Date;
  updatedAt: Date;
}
