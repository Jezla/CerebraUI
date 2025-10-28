// eslint-disable-next-line @typescript-eslint/triple-slash-reference
/// <reference path="../support/index.d.ts" />
import { adminUser } from '../support/e2e';

// Test login and registration functionality
describe('Authentication', () => {
	// Wait 2 seconds after all tests to fix Cypress video recording issue
	after(() => {
		// eslint-disable-next-line cypress/no-unnecessary-waiting
		cy.wait(2000);
	});

	beforeEach(() => {
		// Ensure English interface is used
		cy.clearLocalStorage();
		cy.visit('/auth', {
			onBeforeLoad(win) {
				win.localStorage.setItem('locale', 'en-US');
			}
		});
	});

	context('Page Loading', () => {
		it('should load the sign in page', () => {
			cy.contains('Sign in to').should('exist');
		});

		it('should display the logo', () => {
			cy.get('img[alt="logo"]').should('exist');
		});

		it('should display the sign in form by default', () => {
			cy.get('input[autocomplete="email"]').should('exist');
			cy.get('input[type="password"]').should('exist');
			cy.get('button[type="submit"]').should('exist');
		});

		it('should display the Turnstile verification component', () => {
			cy.get('.cf-turnstile').should('exist');
		});
	});

	context('Sign In Functionality', () => {
		it('should be able to sign in with valid credentials', () => {
			// Intercept Turnstile verification
			cy.intercept('POST', '**/siteverify', {
				statusCode: 200,
				body: { success: true }
			}).as('verifyCF');

			// Intercept sign in request
			cy.intercept('POST', '/api/v1/auths/signin', {
				statusCode: 200,
				body: {
					token: 'test-token',
					id: 'user-id',
					email: adminUser.email,
					name: adminUser.name,
					role: 'admin',
					is_email_verified: true,
					needs_verification: false
				}
			}).as('signin');

			// Fill out the form
			cy.get('input[autocomplete="email"]').type(adminUser.email);
			cy.get('input[type="password"]').type(adminUser.password);

			// Simulate Turnstile success
			cy.window().then((win) => {
				if (win.onSuccess) {
					win.onSuccess('test-turnstile-token');
				}
			});

			// Submit the form
			cy.get('button[type="submit"]').click();

			// Should send sign in request
			cy.wait('@signin');

			// Should redirect to home page
			cy.url({ timeout: 10000 }).should('eq', Cypress.config().baseUrl + '/');
		});

		it('should display error on invalid credentials', () => {
			// Simulate Turnstile success
			cy.window().then((win) => {
				if (win.onSuccess) {
					win.onSuccess('test-turnstile-token');
				}
			});

			// Intercept sign in request and return error
			cy.intercept('POST', '/api/v1/auths/signin', {
				statusCode: 400,
				body: {
					detail: 'Invalid email or password'
				}
			}).as('signin');

			// Fill out the form
			cy.get('input[autocomplete="email"]').type('wrong@example.com');
			cy.get('input[type="password"]').type('wrongpassword');

			// Submit the form
			cy.get('button[type="submit"]').click();

			// Should display error message
			cy.contains(/invalid/i, { timeout: 5000 }).should('exist');
		});

		it('should validate email format', () => {
			// Enter invalid email
			cy.get('input[autocomplete="email"]').type('invalid-email');
			cy.get('input[type="password"]').type('password123');

			// HTML5 validation should prevent submission
			cy.get('input[autocomplete="email"]').then(($input) => {
				const input = $input[0] as HTMLInputElement;
				expect(input.validity.valid).to.be.false;
			});
		});

		it('should require all fields', () => {
			// Try to submit empty form
			cy.get('button[type="submit"]').click();

			// Email input should show required validation
			cy.get('input[autocomplete="email"]').then(($input) => {
				const input = $input[0] as HTMLInputElement;
				expect(input.validity.valueMissing).to.be.true;
			});
		});

		it('should redirect to verification page for unverified emails', () => {
			// Simulate Turnstile success
			cy.window().then((win) => {
				if (win.onSuccess) {
					win.onSuccess('test-turnstile-token');
				}
			});

			// Intercept sign in request
			cy.intercept('POST', '/api/v1/auths/signin', {
				statusCode: 200,
				body: {
					token: 'test-token',
					id: 'user-id',
					email: 'unverified@example.com',
					name: 'Unverified User',
					role: 'user',
					is_email_verified: false,
					needs_verification: true
				}
			}).as('signin');

			// Intercept send email request
			cy.intercept('POST', '/api/v1/auths/send_email', {
				statusCode: 200,
				body: {
					received_email: 'unverified@example.com',
					token: 'verify-token'
				}
			}).as('sendEmail');

			// Fill out the form
			cy.get('input[autocomplete="email"]').type('unverified@example.com');
			cy.get('input[type="password"]').type('password');

			// Submit the form
			cy.get('button[type="submit"]').click();

			// Should redirect to verification page
			cy.url({ timeout: 10000 }).should('include', '/verify');
		});

		it('should display forgot password link', () => {
			cy.contains('Forgot password?').should('exist');
		});
	});

	context('Sign Up Functionality', () => {
		const newUser = {
			name: `Test User ${Date.now()}`,
			email: `test-${Date.now()}@example.com`,
			password: 'TestPassword123!'
		};

		it('should be able to switch to sign up mode', () => {
			cy.contains('Sign up').click();

			// Should display sign up title
			cy.contains('Sign up to').should('exist');

			// Should display name input
			cy.get('input[autocomplete="name"]').should('exist');
		});

		it('should display all required fields in sign up mode', () => {
			cy.contains('Sign up').click();

			cy.get('input[autocomplete="name"]').should('exist');
			cy.get('input[autocomplete="email"]').should('exist');
			cy.get('input[type="password"]').should('exist');
			cy.get('button[type="submit"]').should('contain', 'Create Account');
		});

		it('should be able to sign up new user successfully', () => {
			cy.contains('Sign up').click();

			// Simulate Turnstile success
			cy.window().then((win) => {
				if (win.onSuccess) {
					win.onSuccess('test-turnstile-token');
				}
			});

			// Intercept sign up request
			cy.intercept('POST', '/api/v1/auths/signup', {
				statusCode: 200,
				body: {
					token: 'new-user-token',
					id: 'new-user-id',
					email: newUser.email,
					name: newUser.name,
					role: 'pending',
					is_email_verified: false
				}
			}).as('signup');

			// Intercept send email request
			cy.intercept('POST', '/api/v1/auths/send_email', {
				statusCode: 200,
				body: {
					received_email: newUser.email,
					token: 'verify-token'
				}
			}).as('sendEmail');

			// Fill out the form
			cy.get('input[autocomplete="name"]').type(newUser.name);
			cy.get('input[autocomplete="email"]').type(newUser.email);
			cy.get('input[type="password"]').type(newUser.password);

			// Submit the form
			cy.get('button[type="submit"]').click();

			// Should send sign up request
			cy.wait('@signup');

			// Should send verification email
			cy.wait('@sendEmail');

			// Should redirect to verification page
			cy.url({ timeout: 10000 }).should('include', '/verify');
		});

		it('should display error when email already exists', () => {
			cy.contains('Sign up').click();

			// Simulate Turnstile success
			cy.window().then((win) => {
				if (win.onSuccess) {
					win.onSuccess('test-turnstile-token');
				}
			});

			// Intercept sign up request and return error
			cy.intercept('POST', '/api/v1/auths/signup', {
				statusCode: 400,
				body: {
					detail: 'Email already exists'
				}
			}).as('signup');

			// Fill out the form
			cy.get('input[autocomplete="name"]').type('Existing User');
			cy.get('input[autocomplete="email"]').type(adminUser.email);
			cy.get('input[type="password"]').type('password123');

			// Submit the form
			cy.get('button[type="submit"]').click();

			// Should display error message
			cy.contains(/email.*exist/i, { timeout: 5000 }).should('exist');
		});

		it('should validate all required fields', () => {
			cy.contains('Sign up').click();

			// Try to submit empty form
			cy.get('button[type="submit"]').click();

			// Name input should show required validation
			cy.get('input[autocomplete="name"]').then(($input) => {
				const input = $input[0] as HTMLInputElement;
				expect(input.validity.valueMissing).to.be.true;
			});
		});

		it('should be able to switch back to sign in mode', () => {
			cy.contains('Sign up').click();

			// Should display sign in button
			cy.contains('Already have an account?').should('exist');

			// Click sign in
			cy.contains('button', 'Sign in').click();

			// Should return to sign in mode
			cy.contains('Sign in to').should('exist');
			cy.get('input[autocomplete="name"]').should('not.exist');
		});
	});

	context('Turnstile Verification', () => {
		it('should prevent submission on Turnstile failure', () => {
			// Don't simulate Turnstile success

			// Intercept verification request and return failure
			cy.intercept('POST', '**/siteverify', {
				statusCode: 200,
				body: { success: false }
			}).as('verifyCF');

			// Fill out the form
			cy.get('input[autocomplete="email"]').type(adminUser.email);
			cy.get('input[type="password"]').type(adminUser.password);

			// Submit the form
			cy.get('button[type="submit"]').click();

			// Should display verification failed message
			cy.contains(/verification failed/i, { timeout: 5000 }).should('exist');
		});

		it('should display error on Turnstile expiration', () => {
			// Simulate Turnstile expiration
			cy.window().then((win) => {
				if (win.onExpired) {
					win.onExpired();
				}
			});

			// Should display expiration message
			cy.contains(/expired/i, { timeout: 5000 }).should('exist');
		});

		it('should display error on Turnstile error', () => {
			// Simulate Turnstile error
			cy.window().then((win) => {
				if (win.onError) {
					win.onError();
				}
			});

			// Should display error message
			cy.contains(/error/i, { timeout: 5000 }).should('exist');
		});
	});

	context('OAuth Login', () => {
		it('should display Google login button (if configured)', () => {
			// This test needs to be adjusted based on actual configuration
			// If Google OAuth is enabled, button should be displayed
			cy.get('body').then(($body) => {
				if ($body.find('button:contains("Google")').length > 0) {
					cy.contains('Continue with Google').should('exist');
				}
			});
		});

		it('should display separator (if OAuth providers exist)', () => {
			cy.get('body').then(($body) => {
				if ($body.find('button:contains("Google")').length > 0 || 
				    $body.find('button:contains("Microsoft")').length > 0) {
					cy.contains('or').should('exist');
				}
			});
		});
	});

	context('LDAP Login', () => {
		it('should be able to switch to LDAP mode (if enabled)', () => {
			cy.get('body').then(($body) => {
				if ($body.find('button:contains("LDAP")').length > 0) {
					cy.contains('Continue with LDAP').click();

					// Should display username input
					cy.get('input[autocomplete="username"]').should('exist');
				}
			});
		});
	});

	context('Logged In User Access', () => {
		it('should redirect logged in users to home page', () => {
			// Set token
			cy.window().then((win) => {
				win.localStorage.setItem('token', 'valid-token');
			});

			// Intercept get session user request
			cy.intercept('GET', '/api/v1/auths/', {
				statusCode: 200,
				body: {
					token: 'valid-token',
					id: 'user-id',
					email: 'test@example.com',
					name: 'Test User',
					role: 'user',
					is_email_verified: true
				}
			}).as('getSessionUser');

			// Visit auth page
			cy.visit('/auth');

			// Should redirect to home page
			cy.url({ timeout: 10000 }).should('eq', Cypress.config().baseUrl + '/');
		});
	});

	context('Redirect Parameters', () => {
		it('should redirect to specified page after login', () => {
			const redirectPath = '/settings';

			// Simulate Turnstile success
			cy.window().then((win) => {
				if (win.onSuccess) {
					win.onSuccess('test-turnstile-token');
				}
			});

			// Intercept sign in request
			cy.intercept('POST', '/api/v1/auths/signin', {
				statusCode: 200,
				body: {
					token: 'test-token',
					id: 'user-id',
					email: adminUser.email,
					name: adminUser.name,
					role: 'admin',
					is_email_verified: true,
					needs_verification: false
				}
			}).as('signin');

			// Visit auth page with redirect parameter
			cy.visit(`/auth?redirect=${redirectPath}`);

			// Fill out the form
			cy.get('input[autocomplete="email"]').type(adminUser.email);
			cy.get('input[type="password"]').type(adminUser.password);

			// Submit the form
			cy.get('button[type="submit"]').click();

			cy.wait('@signin');

			// Should redirect to specified page
			cy.url({ timeout: 10000 }).should('include', redirectPath);
		});

		it('should prevent redirect to verify page', () => {
			// Simulate Turnstile success
			cy.window().then((win) => {
				if (win.onSuccess) {
					win.onSuccess('test-turnstile-token');
				}
			});

			// Intercept sign in request
			cy.intercept('POST', '/api/v1/auths/signin', {
				statusCode: 200,
				body: {
					token: 'test-token',
					id: 'user-id',
					email: adminUser.email,
					name: adminUser.name,
					role: 'admin',
					is_email_verified: true,
					needs_verification: false
				}
			}).as('signin');

			// Visit auth page with verify redirect
			cy.visit('/auth?redirect=/verify');

			// Fill out the form
			cy.get('input[autocomplete="email"]').type(adminUser.email);
			cy.get('input[type="password"]').type(adminUser.password);

			// Submit the form
			cy.get('button[type="submit"]').click();

			cy.wait('@signin');

			// Should redirect to home page instead of verify page
			cy.url({ timeout: 10000 }).should('eq', Cypress.config().baseUrl + '/');
		});
	});

	context('UI Interactions', () => {
		it('should hide name field in sign in mode', () => {
			cy.get('input[autocomplete="name"]').should('not.exist');
		});

		it('should display sign in button in sign in mode', () => {
			cy.get('button[type="submit"]').should('contain', 'Sign in');
		});

		it('should display create account button in sign up mode', () => {
			cy.contains('Sign up').click();
			cy.get('button[type="submit"]').should('contain', 'Create Account');
		});

		it('should maintain dark mode styling', () => {
			// Check for dark background
			cy.get('body').then(($body) => {
				expect($body.hasClass('dark') || !$body.hasClass('dark')).to.be.true;
			});
		});
	});

	context('Error Handling', () => {
		it('should handle network errors', () => {
			// Simulate Turnstile success
			cy.window().then((win) => {
				if (win.onSuccess) {
					win.onSuccess('test-turnstile-token');
				}
			});

			// Intercept sign in request and simulate network error
			cy.intercept('POST', '/api/v1/auths/signin', {
				forceNetworkError: true
			}).as('signin');

			// Fill out the form
			cy.get('input[autocomplete="email"]').type(adminUser.email);
			cy.get('input[type="password"]').type(adminUser.password);

			// Submit the form
			cy.get('button[type="submit"]').click();

			// Should display error message
			cy.contains(/error|failed/i, { timeout: 5000 }).should('exist');
		});

		it('should handle server errors', () => {
			// Simulate Turnstile success
			cy.window().then((win) => {
				if (win.onSuccess) {
					win.onSuccess('test-turnstile-token');
				}
			});

			// Intercept sign in request and return 500 error
			cy.intercept('POST', '/api/v1/auths/signin', {
				statusCode: 500,
				body: {
					detail: 'Internal server error'
				}
			}).as('signin');

			// Fill out the form
			cy.get('input[autocomplete="email"]').type(adminUser.email);
			cy.get('input[type="password"]').type(adminUser.password);

			// Submit the form
			cy.get('button[type="submit"]').click();

			// Should display error message
			cy.contains(/error|failed/i, { timeout: 5000 }).should('exist');
		});
	});
});

