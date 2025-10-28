// load the global Cypress types
/// <reference types="cypress" />

declare namespace Cypress {
	interface Chainable {
		login(email: string, password: string): Chainable<any>;
		register(name: string, email: string, password: string): Chainable<any>;
		registerAdmin(): Chainable<any>;
		loginAdmin(): Chainable<any>;
		uploadTestDocument(suffix: any): Chainable<Element>;
		deleteTestDocument(suffix: any): Chainable<Element>;
		
		
		sendVerificationEmail(email: string, type?: 'signin' | 'signup' | 'reset'): Chainable<any>;
		verifyOtp(email: string, otp: string, token: string): Chainable<any>;
		verifyToken(email: string, token: string): Chainable<any>;
		resetPassword(email: string, newPassword: string, token: string): Chainable<any>;
		registerAndVerify(name: string, email: string, password: string, otp?: string): Chainable<any>;
		setupVerificationEnvironment(email: string, token: string): Chainable<any>;
		inputOtp(otp: string): Chainable<any>;
		skipResendCountdown(): Chainable<any>;
	}
}
