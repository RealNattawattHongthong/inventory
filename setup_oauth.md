# Setting up GitHub OAuth for Inventory Manager

To enable GitHub authentication, follow these steps:

## 1. Create a GitHub OAuth App

1. Go to https://github.com/settings/applications/new
2. Fill in the form:
   - **Application name**: Inventory Manager (or any name you prefer)
   - **Homepage URL**: http://localhost:8080
   - **Authorization callback URL**: http://localhost:8080/authorize
   - **Description**: (optional) Inventory management system with QR codes
3. Click "Register application"

## 2. Get your Client ID and Secret

After creating the app, you'll see:
- **Client ID**: A public identifier for your app
- **Client Secret**: Click "Generate a new client secret" and copy it

## 3. Set Environment Variables

### On macOS/Linux:
```bash
export GITHUB_CLIENT_ID="your-client-id-here"
export GITHUB_CLIENT_SECRET="your-client-secret-here"
```

### On Windows (Command Prompt):
```cmd
set GITHUB_CLIENT_ID=your-client-id-here
set GITHUB_CLIENT_SECRET=your-client-secret-here
```

### On Windows (PowerShell):
```powershell
$env:GITHUB_CLIENT_ID="your-client-id-here"
$env:GITHUB_CLIENT_SECRET="your-client-secret-here"
```

## 4. Run the Application

```bash
python inventory_auth_app.py
```

## 5. Access the Application

Open http://localhost:8080 in your browser

## Features with Authentication:

- **Public Access**: Anyone can view items and scan QR codes
- **Admin Access**: Only logged-in users can:
  - Add new items
  - Edit existing items
  - Delete items

## For Production Deployment:

1. Update the callback URL in your GitHub OAuth app settings to match your production domain
2. Set a secure SECRET_KEY environment variable:
   ```bash
   export SECRET_KEY="your-secure-secret-key-here"
   ```
3. Use a production-grade web server (like Gunicorn) instead of Flask's development server