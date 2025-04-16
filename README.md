# Deploy steps
1. Create a new server on DigitalOcean or any other cloud provider.
2. Install Docker and Docker Compose on the server.
3. Edit file `.github/workflows/deploy.yml` and replace git repository URL with your repository URL and folder name with your project folder name.
4. Create ssh key pair on the server and add public key.
5. Add public key to settings of your account on GitHub.
6. Add next secrets to your repository on GitHub:
   - `HOST` - server IP address
   - `USERNAME` - server username
   - `PASSWORD` - server password
   - `ENV_FILE` - envs variables
7. Make test pull on your server manually to add it to known hosts.
8. Push changes to your repository.
9. Go to Actions tab on GitHub and run deploy workflow (you can run it manually or push changes to the repository).
10. Setup nginx or apache on the server to serve your project.
11. Done! Your project is deployed on the server.
