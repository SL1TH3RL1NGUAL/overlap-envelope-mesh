const mongoose = require('mongoose');

mongoose.connect('mongodb://127.0.0.1:27017/blackcorp', {
  useNewUrlParser: true,
  useUnifiedTopology: true
});

const UserSchema = new mongoose.Schema({
  name: String,
  email: { type: String, unique: true },
  phone: String,
  passwordHash: String,
  division: { type: String, default: 'CITIZEN' },
  lastSeen: { type: Date, default: Date.now }
});

const CommentSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  text: String,
  timestamp: { type: Date, default: Date.now }
});

const User = mongoose.model('User', UserSchema);
const Comment = mongoose.model('Comment', CommentSchema);

module.exports = { User, Comment };
