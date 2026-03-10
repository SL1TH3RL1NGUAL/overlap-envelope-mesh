const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { User, Comment } = require('./db');

const app = express();
app.use(express.json());

const JWT_SECRET = 'CHANGE_THIS_SECRET';

// CORS (if front-end on different origin)
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

// Auth middleware
function auth(req, res, next) {
  const header = req.headers.authorization || '';
  const token = header.replace('Bearer ', '');
  if (!token) return res.status(401).json({ error: 'No token' });
  try {
    const payload = jwt.verify(token, JWT_SECRET);
    req.userId = payload.userId;
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
}

// Register
app.post('/api/register', async (req, res) => {
  try {
    const { name, email, phone, password } = req.body;
    const passwordHash = await bcrypt.hash(password, 10);
    const user = await User.create({ name, email, phone, passwordHash, lastSeen: new Date() });
    const token = jwt.sign({ userId: user._id }, JWT_SECRET);
    res.json({ token });
  } catch (e) {
    res.status(400).json({ error: 'Registration failed', detail: e.message });
  }
});

// Login
app.post('/api/login', async (req, res) => {
  const { email, password } = req.body;
  const user = await User.findOne({ email });
  if (!user) return res.status(400).json({ error: 'Invalid credentials' });
  const ok = await bcrypt.compare(password, user.passwordHash);
  if (!ok) return res.status(400).json({ error: 'Invalid credentials' });
  user.lastSeen = new Date();
  await user.save();
  const token = jwt.sign({ userId: user._id }, JWT_SECRET);
  res.json({ token });
});

// Post comment (authenticated)
app.post('/api/comment', auth, async (req, res) => {
  const user = await User.findById(req.userId);
  if (!user) return res.status(400).json({ error: 'User not found' });

  await Comment.create({
    userId: user._id,
    text: req.body.text,
    timestamp: new Date()
  });

  user.lastSeen = new Date();
  await user.save();

  res.json({ status: 'posted' });
});

// Get comments (for timeline)
app.get('/api/comments', async (req, res) => {
  const comments = await Comment.find()
    .sort({ timestamp: 1 })
    .populate('userId', 'name division');
  res.json(comments.map(c => ({
    name: c.userId ? c.userId.name : 'Unknown',
    division: c.userId ? c.userId.division : 'UNKNOWN',
    text: c.text,
    timestamp: c.timestamp
  })));
});

// Online users (for right-side pullout panel)
app.get('/api/online', async (req, res) => {
  const cutoff = new Date(Date.now() - 60 * 1000);
  const users = await User.find({ lastSeen: { $gte: cutoff } }).select('name division');
  res.json(users);
});

// Helix Runtime state endpoint
app.get('/api/helix/state', async (req, res) => {
  const cutoff = new Date(Date.now() - 60 * 1000);
  const [onlineCount, totalComments, divisions] = await Promise.all([
    User.countDocuments({ lastSeen: { $gte: cutoff } }),
    Comment.countDocuments(),
    User.aggregate([
      { $group: { _id: '$division', count: { $sum: 1 } } }
    ])
  ]);

  res.json({
    runtimeVersion: '1.0.0',
    onlineCitizens: onlineCount,
    totalComments,
    divisions: divisions.reduce((acc, d) => {
      acc[d._id || 'UNKNOWN'] = d.count;
      return acc;
    }, {})
  });
});

const PORT = 3000;
app.listen(PORT, () => console.log(`BlackCorp API running on port ${PORT}`));
