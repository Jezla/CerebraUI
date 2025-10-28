/// <reference types="cypress" />
// eslint-disable-next-line @typescript-eslint/triple-slash-reference
/// <reference path="../support/index.d.ts" />

Cypress.on('uncaught:exception', (err, runnable) => {
	const ignoredErrors = [
		'Turnstile',
		'token required',
		'is not async iterable',
		'Not enough segments',
		'Failed to verify OTP token'
	];


	if (ignoredErrors.some(error => err.message.includes(error))) {
		return false;
	}


	return true;
});


beforeEach(() => {

	cy.clearLocalStorage();
	cy.window().then((win) => {
		win.localStorage.setItem('locale', 'en-US');
	});
});

export const adminUser = {
	name: 'Admin User',
	email: 'admin@example.com',
	password: 'password'
};

const login = (email: string, password: string) => {
	return cy.session(
		email,
		() => {
			// Make sure to test against us english to have stable tests,
			// regardless on local language preferences
			localStorage.setItem('locale', 'en-US');
			// Visit auth page
			cy.visit('/auth');
			// Fill out the form
			cy.get('input[autocomplete="email"]').type(email);
			cy.get('input[type="password"]').type(password);
			// Submit the form
			cy.get('button[type="submit"]').click();
			// Wait until the user is redirected to the home page
			cy.get('#chat-search').should('exist');
			// Get the current version to skip the changelog dialog
			if (localStorage.getItem('version') === null) {
				cy.get('button').contains("Okay, Let's Go!").click();
			}
		},
		{
			validate: () => {
				cy.request({
					method: 'GET',
					url: '/api/v1/auths/',
					headers: {
						Authorization: 'Bearer ' + localStorage.getItem('token')
					}
				});
			}
		}
	);
};

const register = (name: string, email: string, password: string) => {
	return cy
		.request({
			method: 'POST',
			url: '/api/v1/auths/signup',
			body: {
				name: name,
				email: email,
				password: password
			},
			failOnStatusCode: false
		})
		.then((response) => {
			expect(response.status).to.be.oneOf([200, 400]);
		});
};

const registerAdmin = () => {
	return register(adminUser.name, adminUser.email, adminUser.password);
};

const loginAdmin = () => {
	return login(adminUser.email, adminUser.password);
};


const sendVerificationEmail = (email: string, type: 'signin' | 'signup' | 'reset' = 'signup') => {
	return cy.request({
		method: 'POST',
		url: '/api/v1/auths/send_email',
		body: {
			email: email,
			type: type
		},
		failOnStatusCode: false
	});
};


const verifyOtp = (email: string, otp: string, token: string) => {
	return cy.request({
		method: 'POST',
		url: '/api/v1/auths/verify_otp',
		body: {
			email: email,
			otp: otp,
			token: token
		},
		failOnStatusCode: false
	});
};


const verifyToken = (email: string, token: string) => {
	return cy.request({
		method: 'POST',
		url: '/api/v1/auths/verify_otp_token',
		body: {
			email: email,
			token: token
		},
		failOnStatusCode: false
	});
};


const resetPassword = (email: string, newPassword: string, token: string) => {
	return cy.request({
		method: 'POST',
		url: '/api/v1/auths/resetPassword',
		body: {
			email: email,
			new_password: newPassword,
			token: token
		},
		failOnStatusCode: false
	});
};


const registerAndVerify = (name: string, email: string, password: string, otp: string = '123456') => {
	return cy
		.request({
			method: 'POST',
			url: '/api/v1/auths/signup',
			body: {
				name: name,
				email: email,
				password: password
			},
			failOnStatusCode: false
		})
		.then((signupResponse) => {
			if (signupResponse.status === 200) {
				// 发送验证邮件
				return cy
					.request({
						method: 'POST',
						url: '/api/v1/auths/send_email',
						body: {
							email: email,
							type: 'signup'
						},
						failOnStatusCode: false
					})
					.then((emailResponse) => {
						if (emailResponse.status === 200 && emailResponse.body.token) {
							// 验证OTP
							return cy.request({
								method: 'POST',
								url: '/api/v1/auths/verify_otp',
								body: {
									email: email,
									otp: otp,
									token: emailResponse.body.token
								},
								failOnStatusCode: false
							});
						}
						return emailResponse;
					});
			}
			return signupResponse;
		});
};


const setupVerificationEnvironment = (email: string, token: string) => {
	cy.window().then((win) => {
		win.sessionStorage.setItem('email', email);
		win.sessionStorage.setItem('token', token);
	});
};


const inputOtp = (otp: string) => {
	const digits = otp.split('');
	digits.forEach((digit, index) => {
		cy.get('input[maxlength="1"]').eq(index).type(digit);
	});
};


const skipResendCountdown = () => {
	// eslint-disable-next-line cypress/no-unnecessary-waiting
	cy.wait(11000);
};

Cypress.Commands.add('login', (email, password) => login(email, password));
Cypress.Commands.add('register', (name, email, password) => register(name, email, password));
Cypress.Commands.add('registerAdmin', () => registerAdmin());
Cypress.Commands.add('loginAdmin', () => loginAdmin());
Cypress.Commands.add('sendVerificationEmail', (email, type) => sendVerificationEmail(email, type));
Cypress.Commands.add('verifyOtp', (email, otp, token) => verifyOtp(email, otp, token));
Cypress.Commands.add('verifyToken', (email, token) => verifyToken(email, token));
Cypress.Commands.add('resetPassword', (email, newPassword, token) => resetPassword(email, newPassword, token));
Cypress.Commands.add('registerAndVerify', (name, email, password, otp) => registerAndVerify(name, email, password, otp));
Cypress.Commands.add('setupVerificationEnvironment', (email, token) => setupVerificationEnvironment(email, token));
Cypress.Commands.add('inputOtp', (otp) => inputOtp(otp));
Cypress.Commands.add('skipResendCountdown', () => skipResendCountdown());

before(() => {
	cy.registerAdmin();
});
