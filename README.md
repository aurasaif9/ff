# 🔑 FF UID Checker v2 — Paid API with Admin Panel

## Files
```
ff_uid_checker_v2/
├── main.py             ← FastAPI (paid API)
├── uid_checker.py      ← FF player info logic
├── firebase_client.py  ← Firebase API key validation
├── requirements.txt
├── vercel.json
└── admin/
    └── index.html      ← Admin Panel (Firebase Auth)
```

## Setup Firebase Auth
1. Firebase Console → Authentication → Enable Email/Password
2. Add admin user: Authentication → Users → Add User
3. Email + Password দাও

## Deploy to Vercel
```bash
vercel --prod
```

## Admin Panel URL
```
https://your-app.vercel.app/admin
```

## API Usage
```
https://your-app.vercel.app/check?uid=3238846823&region=bd&Api_key=vx-YOUR_KEY
```

## Error Responses
| Code | Meaning |
|------|---------|
| INVALID_KEY | Key format ভুল |
| KEY_NOT_FOUND | Key নেই |
| KEY_DISABLED | Disabled |
| KEY_EXPIRED | মেয়াদ শেষ |
| LIMIT_EXCEEDED | Limit শেষ |
