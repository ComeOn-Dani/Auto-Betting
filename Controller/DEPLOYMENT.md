# Vercel Deployment Guide

This guide will help you deploy the Bet Automation Controller to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, or Bitbucket)
3. **Node.js**: Make sure you have Node.js installed locally for testing

## Step-by-Step Deployment

### Step 1: Prepare Your Repository

1. Make sure all the files are committed to your Git repository
2. The Controller directory should contain:
   - `package.json`
   - `server.js`
   - `api/ws.js`
   - `vercel.json`
   - `public/` directory with all frontend files
   - `users.json` (will be created if not exists)

### Step 2: Connect to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "New Project"
3. Import your Git repository
4. Select the repository containing your Controller code

### Step 3: Configure the Project

1. **Framework Preset**: Select "Node.js"
2. **Root Directory**: Set to `Controller` (since your code is in the Controller subdirectory)
3. **Build Command**: Leave empty (not needed for this project)
4. **Output Directory**: Leave empty
5. **Install Command**: `npm install`

### Step 4: Set Environment Variables

In the Vercel dashboard, go to your project settings and add these environment variables:

```
JWT_SECRET=your_secure_jwt_secret_here
```

**Important**: Replace `your_secure_jwt_secret_here` with a strong, random string. You can generate one using:
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Step 5: Deploy

1. Click "Deploy"
2. Wait for the deployment to complete
3. Vercel will provide you with a URL like `https://your-project.vercel.app`

### Step 6: Test the Deployment

1. Visit your Vercel URL
2. You should be redirected to the login page
3. Try logging in with the default admin credentials (if you have them in users.json)

## Post-Deployment Configuration

### Step 7: Update Chrome Extensions

You'll need to update the Chrome extensions to connect to your Vercel deployment:

1. Open the Extension directory
2. Update `background.js` to use your Vercel WebSocket URL:
   ```javascript
   const WS_URL = 'wss://your-project.vercel.app/api/ws';
   ```

### Step 8: Create Initial Admin User

If you don't have an admin user set up, you can create one by:

1. Using the admin interface at `https://your-project.vercel.app/admin.html`
2. Or by manually editing the `users.json` file and redeploying

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Make sure the WebSocket URL in your extensions is correct
   - Check that the `/api/ws` endpoint is working

2. **CORS Errors**
   - The server is configured with CORS enabled
   - If you still get CORS errors, check the browser console

3. **Environment Variables Not Working**
   - Make sure you've set the `JWT_SECRET` environment variable in Vercel
   - Redeploy after changing environment variables

4. **Static Files Not Loading**
   - Check that all files in the `public/` directory are committed to Git
   - Make sure the `vercel.json` configuration is correct

### Debugging

1. Check Vercel function logs in the dashboard
2. Use browser developer tools to check for JavaScript errors
3. Verify that all API endpoints are working

## Security Considerations

1. **JWT Secret**: Use a strong, random JWT secret
2. **HTTPS**: Vercel automatically provides HTTPS
3. **User Management**: Regularly review and update user accounts
4. **License Management**: Monitor license expiration dates

## Updating the Deployment

To update your deployment:

1. Make changes to your code
2. Commit and push to your Git repository
3. Vercel will automatically redeploy (if auto-deploy is enabled)
4. Or manually trigger a redeploy from the Vercel dashboard

## Support

If you encounter issues:

1. Check the Vercel documentation
2. Review the function logs in the Vercel dashboard
3. Test locally first to ensure the code works
4. Check that all dependencies are properly listed in `package.json`
