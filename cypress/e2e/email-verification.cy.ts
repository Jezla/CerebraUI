// eslint-disable-next-line @typescript-eslint/triple-slash-reference
/// <reference path="../support/index.d.ts" />

// Test email verification functionality
describe('Email Verification', () => {
	const testUser = {
		name: `Test User ${Date.now()}`,
		email: `test-${Date.now()}@example.com`,
		password: 'TestPassword123!'
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

	context('Email Verification After Registration', () => {
		it('should redirect to verification page after registration', () => {
			// Switch to sign up mode
			cy.contains('Sign up').click();

			// Fill out the registration form
			cy.get('input[autocomplete="name"]').type(testUser.name);
			cy.get('input[autocomplete="email"]').type(testUser.email);
			cy.get('input[type="password"]').type(testUser.password);

			// Intercept send email request
			cy.intercept('POST', '/api/v1/auths/send_email').as('sendEmail');

			// Submit the form
			cy.get('button[type="submit"]').click();

			// Should redirect to verification page
			cy.url({ timeout: 10000 }).should('include', '/verify');

			// Wait for email to be sent
			cy.wait('@sendEmail');
		});

		it('should display 6 verification code input boxes', () => {
			// Register first
			cy.contains('Sign up').click();
			cy.get('input[autocomplete="name"]').type(testUser.name);
			cy.get('input[autocomplete="email"]').type(testUser.email);
			cy.get('input[type="password"]').type(testUser.password);
			cy.get('button[type="submit"]').click();

			// Wait for redirect
			cy.url({ timeout: 10000 }).should('include', '/verify');

			// Check for 6 input boxes
			cy.get('input[maxlength="1"]').should('have.length', 6);
		});

		it('should display user email address', () => {
			// Set sessionStorage
			cy.window().then((win) => {
				win.sessionStorage.setItem('email', testUser.email);
				win.sessionStorage.setItem('token', 'test-token');
			});

			cy.visit('/verify');

			// Check email is displayed
			cy.contains(testUser.email).should('exist');
		});
	});

	context('OTP Input and Verification', () => {
		beforeEach(() => {
			// Set up verification environment
			cy.window().then((win) => {
				win.sessionStorage.setItem('email', 'test@example.com');
				win.sessionStorage.setItem('token', 'test-token');
			});
			cy.visit('/verify');
		});

		it('should allow entering digits in verification code input boxes', () => {
			// Enter 6 digits
			cy.get('input[maxlength="1"]').eq(0).type('1');
			cy.get('input[maxlength="1"]').eq(1).type('2');
			cy.get('input[maxlength="1"]').eq(2).type('3');
			cy.get('input[maxlength="1"]').eq(3).type('4');
			cy.get('input[maxlength="1"]').eq(4).type('5');
			cy.get('input[maxlength="1"]').eq(5).type('6');

			// Check values
			cy.get('input[maxlength="1"]').eq(0).should('have.value', '1');
			cy.get('input[maxlength="1"]').eq(5).should('have.value', '6');
		});

		it('should auto-focus to next input box on entry', () => {
			// Enter first digit
			cy.get('input[maxlength="1"]').eq(0).type('1');

			// Second input should have focus
			cy.get('input[maxlength="1"]').eq(1).should('have.focus');
		});

		it('should return to previous input box on backspace', () => {
			// Enter first three digits
			cy.get('input[maxlength="1"]').eq(0).type('1');
			cy.get('input[maxlength="1"]').eq(1).type('2');
			cy.get('input[maxlength="1"]').eq(2).type('3');

			// Press backspace in third input box
			cy.get('input[maxlength="1"]').eq(2).clear().type('{backspace}');

			// Should return to second input box
			cy.get('input[maxlength="1"]').eq(1).should('have.focus');
		});

		it('should display verify email button', () => {
			cy.contains('Verify Email').should('exist');
		});

		it('should display resend button', () => {
			cy.contains('Resend code').should('exist');
		});

		it('resend button should have countdown', () => {
			// Button should be disabled and show countdown
			cy.contains(/Resend code \d+s/).should('exist');
		});

		it('should display error on incorrect OTP submission', () => {
			// Intercept verification request
			cy.intercept('POST', '/api/v1/auths/verify_otp', {
				statusCode: 400,
				body: { detail: 'Invalid OTP' }
			}).as('verifyOtp');

			// Enter 6 digits
			cy.get('input[maxlength="1"]').eq(0).type('1');
			cy.get('input[maxlength="1"]').eq(1).type('2');
			cy.get('input[maxlength="1"]').eq(2).type('3');
			cy.get('input[maxlength="1"]').eq(3).type('4');
			cy.get('input[maxlength="1"]').eq(4).type('5');
			cy.get('input[maxlength="1"]').eq(5).type('6');

			// Click verify button
			cy.contains('Verify Email').click();

			// Wait for request to complete
			cy.wait('@verifyOtp');

			// Should display error message
			cy.contains('Invalid OTP', { timeout: 5000 }).should('exist');
		});
	});

	context('Token Verification', () => {
		it('should display warning when token is missing', () => {
			// Only set email, no token
			cy.window().then((win) => {
				win.sessionStorage.setItem('email', 'test@example.com');
			});

			cy.visit('/verify');

			// Should display resend prompt
			cy.contains(/Resend code/, { timeout: 5000 }).should('exist');
		});

		it('should redirect to auth page on invalid token', () => {
			// Intercept token verification request and return failure
			cy.intercept('POST', '/api/v1/auths/verify_otp_token', {
				statusCode: 400,
				body: false
			}).as('verifyToken');

			cy.window().then((win) => {
				win.sessionStorage.setItem('email', 'test@example.com');
				win.sessionStorage.setItem('token', 'invalid-token');
			});

			cy.visit('/verify');

			// Wait for verification to fail
			cy.wait('@verifyToken');

			// Should redirect to auth page (note: may need to adjust wait time)
			cy.url({ timeout: 10000 }).should('include', '/auth');
		});
	});

	context('Resending OTP', () => {
		beforeEach(() => {
			cy.window().then((win) => {
				win.sessionStorage.setItem('email', 'test@example.com');
				win.sessionStorage.setItem('token', 'test-token');
			});
			cy.visit('/verify');
		});

		it('should enable resend button after countdown ends', () => {
			// Wait for countdown to end (11 seconds)
			// eslint-disable-next-line cypress/no-unnecessary-waiting
			cy.wait(11000);

			// Button should no longer show countdown
			cy.contains('Resend code').should('exist');
			cy.contains(/\d+s/).should('not.exist');
		});

		it('should be able to resend verification code', () => {
			// Intercept resend request
			cy.intercept('POST', '/api/v1/auths/send_email', {
				statusCode: 200,
				body: {
					received_email: 'test@example.com',
					token: 'new-token'
				}
			}).as('resendEmail');

			// Intercept get email type request
			cy.intercept('POST', '/api/v1/auths/get_email_type', {
				statusCode: 200,
				body: 'signup'
			}).as('getEmailType');

			// Wait for countdown to end
			// eslint-disable-next-line cypress/no-unnecessary-waiting
			cy.wait(11000);

			// Click resend button
			cy.contains('Resend code').click();

			// Wait for requests
			cy.wait('@getEmailType');
			cy.wait('@resendEmail');

			// Countdown should restart
			cy.contains(/Resend code \d+s/, { timeout: 2000 }).should('exist');
		});

		it('should display error on reaching maximum attempts', () => {
			// Intercept request and return error
			cy.intercept('POST', '/api/v1/auths/send_email', {
				statusCode: 400,
				body: {
					detail: 'You have reached the maximum number of attempts. Please try again later.'
				}
			}).as('resendEmail');

			cy.intercept('POST', '/api/v1/auths/get_email_type', {
				statusCode: 200,
				body: 'signup'
			}).as('getEmailType');

			// Wait for countdown to end
			// eslint-disable-next-line cypress/no-unnecessary-waiting
			cy.wait(11000);

			// Click resend button
			cy.contains('Resend code').click();

			// Should display error message
			cy.contains(/maximum number of attempts/, { timeout: 5000 }).should('exist');
		});
	});

	context('Successful Verification Flow', () => {
		it('should redirect to home page after successful verification (signup type)', () => {
			cy.window().then((win) => {
				win.sessionStorage.setItem('email', 'test@example.com');
				win.sessionStorage.setItem('token', 'test-token');
			});

			cy.visit('/verify');

			// Intercept requests
			cy.intercept('POST', '/api/v1/auths/get_email_type', {
				statusCode: 200,
				body: 'signup'
			}).as('getEmailType');

			cy.intercept('POST', '/api/v1/auths/verify_otp', {
				statusCode: 200,
				body: {
					result: true,
					token: 'verified-token',
					auth_token: 'auth-token'
				}
			}).as('verifyOtp');

			cy.intercept('GET', '/api/v1/auths/', {
				statusCode: 200,
				body: {
					id: 'user-id',
					email: 'test@example.com',
					name: 'Test User',
					role: 'user',
					profile_image_url: '',
					is_email_verified: true
				}
			}).as('getSessionUser');

			// Enter correct OTP
			cy.get('input[maxlength="1"]').eq(0).type('1');
			cy.get('input[maxlength="1"]').eq(1).type('2');
			cy.get('input[maxlength="1"]').eq(2).type('3');
			cy.get('input[maxlength="1"]').eq(3).type('4');
			cy.get('input[maxlength="1"]').eq(4).type('5');
			cy.get('input[maxlength="1"]').eq(5).type('6');

			// Click verify
			cy.contains('Verify Email').click();

			// Wait for all requests
			cy.wait('@verifyOtp');
			cy.wait('@getSessionUser');

			// Should redirect to home page
			cy.url({ timeout: 10000 }).should('eq', Cypress.config().baseUrl + '/');
		});

		it('should redirect to reset password page after successful verification (reset type)', () => {
			cy.window().then((win) => {
				win.sessionStorage.setItem('email', 'test@example.com');
				win.sessionStorage.setItem('token', 'test-token');
			});

			cy.visit('/verify');

			// Intercept requests
			cy.intercept('POST', '/api/v1/auths/get_email_type', {
				statusCode: 200,
				body: 'reset'
			}).as('getEmailType');

			cy.intercept('POST', '/api/v1/auths/verify_otp', {
				statusCode: 200,
				body: {
					result: true,
					token: 'reset-token'
				}
			}).as('verifyOtp');

			// Enter OTP
			cy.get('input[maxlength="1"]').eq(0).type('1');
			cy.get('input[maxlength="1"]').eq(1).type('2');
			cy.get('input[maxlength="1"]').eq(2).type('3');
			cy.get('input[maxlength="1"]').eq(3).type('4');
			cy.get('input[maxlength="1"]').eq(4).type('5');
			cy.get('input[maxlength="1"]').eq(5).type('6');

			// Click verify
			cy.contains('Verify Email').click();

			// Wait for request
			cy.wait('@verifyOtp');

			// Should redirect to reset password page
			cy.url({ timeout: 10000 }).should('include', '/verify/reset');
		});
	});

	context('Invalid Email Handling', () => {
		it('should redirect to auth page when email is missing', () => {
			cy.visit('/verify');

			// Should redirect to auth page
			cy.url({ timeout: 5000 }).should('include', '/auth');
		});
	});
});
