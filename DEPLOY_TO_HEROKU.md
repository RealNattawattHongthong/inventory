# Deploy to Heroku Guide

## Prerequisites
1. [Heroku Account](https://signup.heroku.com/)
2. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
3. [Git](https://git-scm.com/)

## Step 1: Initialize Git Repository
```bash
cd QRCode-Inventory-Manager-main
git init
git add .
git commit -m "Initial commit"
```

## Step 2: Create Heroku App
```bash
heroku create your-app-name
# Example: heroku create my-inventory-manager
```

## Step 3: Add PostgreSQL Database
```bash
heroku addons:create heroku-postgresql:mini
```

## Step 4: Set Environment Variables

### Required for GitHub OAuth:
```bash
# First, create a GitHub OAuth App:
# 1. Go to https://github.com/settings/applications/new
# 2. Application name: Your App Name
# 3. Homepage URL: https://your-app-name.herokuapp.com
# 4. Authorization callback URL: https://your-app-name.herokuapp.com/authorize

# Then set the credentials:
heroku config:set GITHUB_CLIENT_ID="your-github-client-id"
heroku config:set GITHUB_CLIENT_SECRET="your-github-client-secret"

# Set a secure secret key:
heroku config:set SECRET_KEY="$(openssl rand -hex 32)"
```

## Step 5: Deploy to Heroku
```bash
git push heroku main
# or if your branch is called master:
git push heroku master
```

## Step 6: Initialize Database
```bash
heroku run python
>>> from inventory_auth_app import db
>>> db.create_all()
>>> exit()
```

## Step 7: Open Your App
```bash
heroku open
```

## Updating Your App

After making changes:
```bash
git add .
git commit -m "Update description"
git push heroku main
```

## Viewing Logs
```bash
heroku logs --tail
```

## Useful Commands

### Check app status:
```bash
heroku ps
```

### Restart app:
```bash
heroku restart
```

### Run database migrations:
```bash
heroku run python
>>> from inventory_auth_app import db
>>> db.create_all()
```

### Check environment variables:
```bash
heroku config
```

## Troubleshooting

### If you get "No web processes running":
```bash
heroku ps:scale web=1
```

### If GitHub OAuth doesn't work:
1. Make sure your GitHub OAuth app URLs use HTTPS and your Heroku app URL
2. Double-check your CLIENT_ID and CLIENT_SECRET are set correctly
3. The callback URL must exactly match: `https://your-app-name.herokuapp.com/authorize`

### Database Issues:
```bash
# Reset database (WARNING: This deletes all data!)
heroku pg:reset DATABASE_URL
heroku run python
>>> from inventory_auth_app import db
>>> db.create_all()
```

## Custom Domain (Optional)

To add a custom domain:
```bash
heroku domains:add www.yourdomain.com
```

Then update your DNS settings and GitHub OAuth URLs accordingly.

## Free Tier Limitations

- Heroku free tier apps sleep after 30 minutes of inactivity
- Limited to 550-1000 dyno hours per month
- PostgreSQL mini plan: 10,000 row limit

For production use, consider upgrading to paid plans.