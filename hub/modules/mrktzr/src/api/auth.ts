import { Router } from 'express';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import { User } from '../models/user';

const router = Router();

// This is a mock database for demonstration purposes.
const users: User[] = [];
let nextUserId = 1;

router.post('/register', async (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).send('Username and password are required');
  }

  const existingUser = users.find(u => u.username === username);
  if (existingUser) {
    return res.status(400).send('Username already exists');
  }

  const passwordHash = await bcrypt.hash(password, 10);

  const newUser: User = {
    id: nextUserId++,
    username,
    passwordHash,
  };

  users.push(newUser);

  res.status(201).send('User registered successfully');
});

router.post('/login', async (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).send('Username and password are required');
  }

  const user = users.find(u => u.username === username);
  if (!user) {
    return res.status(401).send('Invalid username or password');
  }

  const isPasswordValid = await bcrypt.compare(password, user.passwordHash);
  if (!isPasswordValid) {
    return res.status(401).send('Invalid username or password');
  }

  const token = jwt.sign({ userId: user.id }, 'your-secret-key', { expiresIn: '1h' });

  res.json({ token });
});

export default router;
