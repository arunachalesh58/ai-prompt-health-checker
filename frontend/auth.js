// ─── COGNITO CONFIG ───────────────────────────────────────────────
// Replace these values after you create your Cognito User Pool
const COGNITO_CONFIG = {
  UserPoolId: 'us-east-1_KsnEWpB4s',
  ClientId: '1llv7bd5f6mpqfu0eqm2hn5p1h',
  Domain: 'us-east-1ksnewpb4s.auth.us-east-1.amazoncognito.com',
  RedirectUri: window.location.origin + '/index.html'
};
// ──────────────────────────────────────────────────────────────────

const poolData = {
  UserPoolId: COGNITO_CONFIG.UserPoolId,
  ClientId: COGNITO_CONFIG.ClientId
};

function getUserPool() {
  return new AmazonCognitoIdentity.CognitoUserPool(poolData);
}

// Sign up with email + password
function cognitoSignUp(email, password) {
  return new Promise((resolve, reject) => {
    const attributeList = [
      new AmazonCognitoIdentity.CognitoUserAttribute({ Name: 'email', Value: email })
    ];
    getUserPool().signUp(email, password, attributeList, null, (err, result) => {
      if (err) reject(err);
      else resolve(result);
    });
  });
}

// Confirm email with verification code
function cognitoConfirm(email, code) {
  return new Promise((resolve, reject) => {
    const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
      Username: email,
      Pool: getUserPool()
    });
    cognitoUser.confirmRegistration(code, true, (err, result) => {
      if (err) reject(err);
      else resolve(result);
    });
  });
}

// Sign in with email + password
function cognitoSignIn(email, password) {
  return new Promise((resolve, reject) => {
    const authDetails = new AmazonCognitoIdentity.AuthenticationDetails({
      Username: email,
      Password: password
    });
    const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
      Username: email,
      Pool: getUserPool()
    });
    cognitoUser.authenticateUser(authDetails, {
      onSuccess: (result) => {
        localStorage.setItem('idToken', result.getIdToken().getJwtToken());
        localStorage.setItem('accessToken', result.getAccessToken().getJwtToken());
        resolve(result);
      },
      onFailure: (err) => reject(err)
    });
  });
}

// Sign out
function cognitoSignOut() {
  const pool = getUserPool();
  const user = pool.getCurrentUser();
  if (user) {
    user.signOut();
  }
  localStorage.removeItem('idToken');
  localStorage.removeItem('accessToken');
  window.location.href = 'login.html';
}

// Check if user is currently logged in
function isLoggedIn() {
  return new Promise((resolve) => {
    const pool = getUserPool();
    const user = pool.getCurrentUser();
    if (!user) { resolve(false); return; }
    user.getSession((err, session) => {
      if (err || !session.isValid()) resolve(false);
      else resolve(true);
    });
  });
}

// Get current user email
function getCurrentUserEmail() {
  return new Promise((resolve, reject) => {
    const pool = getUserPool();
    const user = pool.getCurrentUser();
    if (!user) { reject('No user'); return; }
    user.getSession((err, session) => {
      if (err) { reject(err); return; }
      user.getUserAttributes((err, attrs) => {
        if (err) { reject(err); return; }
        const email = attrs.find(a => a.getName() === 'email');
        resolve(email ? email.getValue() : '');
      });
    });
  });
}

// Get Google / GitHub SSO login URL
function getCognitoOAuthURL(provider) {
  const params = new URLSearchParams({
    client_id: COGNITO_CONFIG.ClientId,
    response_type: 'code',
    scope: 'email openid profile',
    redirect_uri: COGNITO_CONFIG.RedirectUri,
    identity_provider: provider
  });
  return `https://${COGNITO_CONFIG.Domain}/oauth2/authorize?${params.toString()}`;
}

// Redirect to login if not authenticated (call this on protected pages)
async function requireAuth() {
  const loggedIn = await isLoggedIn();
  if (!loggedIn) {
    window.location.href = 'login.html';
  }
}
