// eslint-disable-next-line @typescript-eslint/triple-slash-reference
/// <reference path="../support/index.d.ts" />

// Test password reset functionality
describe('Password Reset', () => {
	const existingUser = {
		email: 'admin@example.com',
		password: 'password',
		newPassword: 'NewPassword123!'
	};

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

	context('Request Password Reset', () => {
		it('should display forgot password link', () => {
			cy.contains('Forgot password?').should('exist');
		});

		it('should be able to switch to reset password mode', () => {
			// Click forgot password
			cy.contains('Forgot password?').click();

			// Should display reset password title
			cy.contains('Reset password').should('exist');

			// Should display email input box
			cy.get('input[type="email"]').should('exist');

			// Should not display password input box
			cy.get('input[type="password"]').should('not.exist');
		});

		it('should be able to return to sign in mode', () => {
			// Switch to reset password mode
			cy.contains('Forgot password?').click();

			// Click return to sign in
			cy.contains('Remembered your password?').should('exist');
			cy.contains('button', 'Sign in').click();

			// Should return to sign in mode
			cy.contains('Sign in to').should('exist');
		});

		it('should send reset email after submission', () => {
			// Intercept send email request
			cy.intercept('POST', '/api/v1/auths/send_email', {
				statusCode: 200,
				body: {
					received_email: existingUser.email,
					token: 'reset-token'
				}
			}).as('sendEmail');

			// Switch to reset password mode
			cy.contains('Forgot password?').click();

			// Enter email
			cy.get('input[type="email"]').type(existingUser.email);

			// Submit form
			cy.contains('button', 'Send email').click();

			// Should send request
			cy.wait('@sendEmail');

			// Should redirect to verification page
			cy.url({ timeout: 10000 }).should('include', '/verify');
		});

		it('should still display success message when email does not exist (security consideration)', () => {
			// Intercept request
			cy.intercept('POST', '/api/v1/auths/send_email', {
				statusCode: 200,
				body: {
					received_email: 'nonexistent@example.com',
					otp: null
				}
			}).as('sendEmail');

			// Switch to reset password mode
			cy.contains('Forgot password?').click();

			// Enter non-existent email
			cy.get('input[type="email"]').type('nonexistent@example.com');

			// Submit form
			cy.contains('button', 'Send email').click();

			// Should display success message (even if email doesn't exist)
			cy.contains(/email sent/i, { timeout: 5000 }).should('exist');
		});

		it('should display error on reaching maximum attempts', () => {
			// Intercept request and return error
			cy.intercept('POST', '/api/v1/auths/send_email', {
				statusCode: 400,
				body: {
					detail: 'You have reached the maximum number of attempts. Please try again later.'
				}
			}).as('sendEmail');

			// Switch to reset password mode
			cy.contains('Forgot password?').click();

			// Enter email
			cy.get('input[type="email"]').type(existingUser.email);

			// Submit form
			cy.contains('button', 'Send email').click();

			// Should display error message
			cy.contains(/maximum number of attempts/i, { timeout: 5000 }).should('exist');
		});

		it('should validate email format', () => {
			// Switch to reset password mode
			cy.contains('Forgot password?').click();

			// Enter invalid email
			cy.get('input[type="email"]').type('invalid-email');

			// HTML5 validation should prevent submission
			cy.get('input[type="email"]').then(($input) => {
				const input = $input[0] as HTMLInputElement;
				expect(input.validity.valid).to.be.false;
			});
		});
	});

	context('Reset Password Page', () => {
		beforeEach(() => {
			// Set sessionStorage
			cy.window().then((win) => {
				win.sessionStorage.setItem('email', existingUser.email);
				win.sessionStorage.setItem('rt', 'reset-token');
			});
		});

		it('should load reset page with valid token', () => {
			// Intercept token verification
			cy.intercept('POST', '/api/v1/auths/verify_reset_token', {
				statusCode: 200,
				body: true
			}).as('verifyToken');

			cy.visit('/verify/reset');

			// Should verify token
			cy.wait('@verifyToken');

			// Should display reset password title
			cy.contains('Reset password').should('exist');

			// Should display email
			cy.contains(existingUser.email).should('exist');
		});

		it('should redirect to auth page when token is missing', () => {
			// Remove token
			cy.window().then((win) => {
				win.sessionStorage.removeItem('rt');
			});

			cy.visit('/verify/reset');

			// Should redirect to auth page
			cy.url({ timeout: 5000 }).should('include', '/auth');
		});

		it('should redirect to auth page on invalid token', () => {
			// Intercept token verification and return failure
			cy.intercept('POST', '/api/v1/auths/verify_reset_token', {
				statusCode: 400,
				body: false
			}).as('verifyToken');

			cy.visit('/verify/reset');

			// Should redirect to auth page
			cy.url({ timeout: 5000 }).should('include', '/auth');
		});

		it('should display new password input boxes', () => {
			// Intercept token verification
			cy.intercept('POST', '/api/v1/auths/verify_reset_token', {
				statusCode: 200,
				body: true
			}).as('verifyToken');

			cy.visit('/verify/reset');

			// Should have two password input boxes
			cy.get('input[type="password"]').should('have.length', 2);
		});

		it('should be able to successfully reset password', () => {
			// Intercept token verification
			cy.intercept('POST', '/api/v1/auths/verify_reset_token', {
				statusCode: 200,
				body: true
			}).as('verifyToken');

			// Intercept reset password request
			cy.intercept('POST', '/api/v1/auths/resetPassword', {
				statusCode: 200,
				body: true
			}).as('resetPassword');

			cy.visit('/verify/reset');

			cy.wait('@verifyToken');

			// Enter new password
			cy.get('input[type="password"]').eq(0).type(existingUser.newPassword);
			cy.get('input[type="password"]').eq(1).type(existingUser.newPassword);

			// Submit form
			cy.contains('button', 'Reset password').click();

			// Should send reset request
			cy.wait('@resetPassword');

			// Should display success message
			cy.contains(/successfully/i, { timeout: 5000 }).should('exist');

			// Should redirect to auth page
			cy.url({ timeout: 5000 }).should('include', '/auth');
		});

		it('should display error on reset failure', () => {
			// Intercept token verification
			cy.intercept('POST', '/api/v1/auths/verify_reset_token', {
				statusCode: 200,
				body: true
			}).as('verifyToken');

			// Intercept reset password request and return error
			cy.intercept('POST', '/api/v1/auths/resetPassword', {
				statusCode: 400,
				body: {
					detail: 'Password reset failed'
				}
			}).as('resetPassword');

			cy.visit('/verify/reset');

			cy.wait('@verifyToken');

			// Enter new password
			cy.get('input[type="password"]').eq(0).type(existingUser.newPassword);
			cy.get('input[type="password"]').eq(1).type(existingUser.newPassword);

			// Submit form
			cy.contains('button', 'Reset password').click();

			// Should display error message
			cy.contains(/failed/i, { timeout: 5000 }).should('exist');
		});

		it('should display return to sign in link', () => {
			// Intercept token verification
			cy.intercept('POST', '/api/v1/auths/verify_reset_token', {
				statusCode: 200,
				body: true
			}).as('verifyToken');

			cy.visit('/verify/reset');

			// Should have return to sign in link
			cy.get('a[href="/auth"]').should('exist').and('contain', 'Sign in');
		});

		it('should be able to return to auth page via link', () => {
			// Intercept token verification
			cy.intercept('POST', '/api/v1/auths/verify_reset_token', {
				statusCode: 200,
				body: true
			}).as('verifyToken');

			cy.visit('/verify/reset');

			// Click return to sign in
			cy.get('a[href="/auth"]').click();

			// Should return to auth page
			cy.url({ timeout: 5000 }).should('include', '/auth');
		});
	});

	context('Complete Password Reset Flow', () => {
		it('should be able to complete the full password reset flow', () => {
			const testEmail = 'test-reset@example.com';

			// Step 1: Request password reset
			cy.contains('Forgot password?').click();

			// Intercept send email request
			cy.intercept('POST', '/api/v1/auths/send_email', {
				statusCode: 200,
				body: {
					received_email: testEmail,
					token: 'reset-token-123'
				}
			}).as('sendEmail');

			cy.get('input[type="email"]').type(testEmail);
			cy.contains('button', 'Send email').click();

			cy.wait('@sendEmail');

			// Should redirect to verification page
			cy.url({ timeout: 10000 }).should('include', '/verify');

			// Step 2: Verify OTP
			cy.intercept('POST', '/api/v1/auths/get_email_type', {
				statusCode: 200,
				body: 'reset'
			}).as('getEmailType');

			cy.intercept('POST', '/api/v1/auths/verify_otp', {
				statusCode: 200,
				body: {
					result: true,
					token: 'verified-reset-token'
				}
			}).as('verifyOtp');

			// Enter OTP
			cy.get('input[maxlength="1"]').eq(0).type('1');
			cy.get('input[maxlength="1"]').eq(1).type('2');
			cy.get('input[maxlength="1"]').eq(2).type('3');
			cy.get('input[maxlength="1"]').eq(3).type('4');
			cy.get('input[maxlength="1"]').eq(4).type('5');
			cy.get('input[maxlength="1"]').eq(5).type('6');

			cy.contains('Verify Email').click();

			cy.wait('@verifyOtp');

			// Should redirect to reset password page
			cy.url({ timeout: 10000 }).should('include', '/verify/reset');

			// Step 3: Set new password
			cy.intercept('POST', '/api/v1/auths/verify_reset_token', {
				statusCode: 200,
				body: true
			}).as('verifyResetToken');

			cy.intercept('POST', '/api/v1/auths/resetPassword', {
				statusCode: 200,
				body: true
			}).as('resetPassword');

			cy.wait('@verifyResetToken');

			cy.get('input[type="password"]').eq(0).type(existingUser.newPassword);
			cy.get('input[type="password"]').eq(1).type(existingUser.newPassword);

			cy.contains('button', 'Reset password').click();

			cy.wait('@resetPassword');

			// Should redirect to auth page
			cy.url({ timeout: 10000 }).should('include', '/auth');
		});
	});

	context('Security Tests', () => {
		it('should prevent unauthorized password reset', () => {
			// Try to directly access reset page without valid token
			cy.visit('/verify/reset');

			// Should redirect to auth page
			cy.url({ timeout: 5000 }).should('include', '/auth');
		});

		it('should block password reset on expired token', () => {
			// Set expired token
			cy.window().then((win) => {
				win.sessionStorage.setItem('email', existingUser.email);
				win.sessionStorage.setItem('rt', 'expired-token');
			});

			// Intercept token verification and return failure
			cy.intercept('POST', '/api/v1/auths/verify_reset_token', {
				statusCode: 400,
				body: {
					detail: 'Token expired'
				}
			}).as('verifyToken');

			cy.visit('/verify/reset');

			// Should redirect to auth page
			cy.url({ timeout: 5000 }).should('include', '/auth');
		});

		it('should clear sessionStorage after reset', () => {
			// Set token
			cy.window().then((win) => {
				win.sessionStorage.setItem('email', existingUser.email);
				win.sessionStorage.setItem('rt', 'reset-token');
			});

			// Intercept requests
			cy.intercept('POST', '/api/v1/auths/verify_reset_token', {
				statusCode: 200,
				body: true
			}).as('verifyToken');

			cy.intercept('POST', '/api/v1/auths/resetPassword', {
				statusCode: 200,
				body: true
			}).as('resetPassword');

			cy.visit('/verify/reset');

			cy.wait('@verifyToken');

			// Enter new password and submit
			cy.get('input[type="password"]').eq(0).type(existingUser.newPassword);
			cy.get('input[type="password"]').eq(1).type(existingUser.newPassword);
			cy.contains('button', 'Reset password').click();

			cy.wait('@resetPassword');

			// Check sessionStorage has been cleared
			cy.window().then((win) => {
				expect(win.sessionStorage.getItem('rt')).to.be.null;
				expect(win.sessionStorage.getItem('email')).to.be.null;
			});
		});
	});
});
