const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');

const app = express();
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

const GITHUB_TOKEN = 'your_github_token';
const GITHUB_REPO = 'your_github_username/user-accounts';
const GITHUB_FILE_PATH = 'accounts.json';

// 获取账户数据
const getAccounts = async () => {
  try {
    const response = await axios.get(`https://api.github.com/repos/${GITHUB_REPO}/contents/${GITHUB_FILE_PATH}`, {
      headers: {
        Authorization: `token ${GITHUB_TOKEN}`,
        Accept: 'application/vnd.github.v3.raw'
      }
    });
    return JSON.parse(response.data);
  } catch (error) {
    console.error('Error getting accounts:', error);
    return {};
  }
};

// 保存账户数据
const saveAccounts = async (accounts, sha) => {
  try {
    const response = await axios.put(`https://api.github.com/repos/${GITHUB_REPO}/contents/${GITHUB_FILE_PATH}`, {
      message: 'Update accounts',
      content: Buffer.from(JSON.stringify(accounts, null, 2)).toString('base64'),
      sha: sha,
    }, {
      headers: {
        Authorization: `token ${GITHUB_TOKEN}`,
        Accept: 'application/vnd.github.v3+json'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error saving accounts:', error);
  }
};

// 注册处理
app.post('/register', async (req, res) => {
  const { username, password } = req.body;
  const accounts = await getAccounts();

  if (accounts[username]) {
    return res.status(400).send({ success: false, message: 'User already exists' });
  }

  accounts[username] = { password, points: username === 'liuyiwen' || username === 'kzy' ? Infinity : 1 };

  const response = await axios.get(`https://api.github.com/repos/${GITHUB_REPO}/contents/${GITHUB_FILE_PATH}`, {
    headers: {
      Authorization: `token ${GITHUB_TOKEN}`,
      Accept: 'application/vnd.github.v3.raw'
    }
  });

  const sha = response.data.sha;

  await saveAccounts(accounts, sha);

  res.send({ success: true, message: 'User registered successfully' });
});

// 登录处理
app.post('/login', async (req, res) => {
  const { username, password } = req.body;
  const accounts = await getAccounts();

  if (!accounts[username] || accounts[username].password !== password) {
    return res.status(400).send({ success: false, message: 'Invalid username or password' });
  }

  res.send({ success: true, message: 'Login successful' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
