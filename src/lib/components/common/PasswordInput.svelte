<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    export let id = 'password';
    export let name = 'password';
    export let value: string = '';
    export let placeholder = '';
    export let showStrengthIndicator = false;
    const dispatch = createEventDispatcher();
    let show: boolean = false;
    

    let passwordStrength = 0;
    let strengthText = '';
    let strengthClass = '';
    

    function calculatePasswordStrength(password: string) {
      if (!password) {
        passwordStrength = 0;
        strengthText = '';
        strengthClass = '';
        return;
      }
      
      let score = 0;

      if (password.length >= 8) score += 1;
      if (password.length >= 12) score += 1;
      
      if (/[a-z]/.test(password)) score += 1;
      if (/[A-Z]/.test(password)) score += 1; 
      if (/[0-9]/.test(password)) score += 1; 
      if (/[^A-Za-z0-9]/.test(password)) score += 1; 
      
      passwordStrength = score;
      
      if (score <= 2) {
        strengthText = 'Weak';
        strengthClass = 'weak';
      } else if (score <= 4) {
        strengthText = 'Medium';
        strengthClass = 'medium';
      } else {
        strengthText = 'Strong';
        strengthClass = 'strong';
      }
    }

    function handleInput(e: Event) {
      value = (e.target as HTMLInputElement).value;
      calculatePasswordStrength(value);
      dispatch('input', { value });
    }
    
    function handleStrength(e: Event) {
      value = (e.target as HTMLInputElement).value;
      dispatch('strength', { value });
    }

    function toggleShow() {
      show = !show;
    }
  </script>
  
  <label for={id} class="sr-only">password</label>
  <div class="password-field">
    <input
      id={id}
      name={name}
      type={show ? 'text' : 'password'}
      value={value}
      on:input={handleInput}
      placeholder={placeholder}
      aria-label="password"
      class="password-input"
      on:input={handleStrength}
    />

    <button
      type="button"
      on:click={toggleShow}
      aria-pressed={show}
      title={show ? 'Hide password' : 'Show password'}
      class="toggle-btn"
    >
      {#if show}
        <!-- eye-off icon -->
          <img src="/assets/emojis/eye-closed.svg" alt="eye-closed"/>
        {:else}
          <!-- eye icon -->
          <img src="/assets/emojis/eye.svg" alt="eye"/>
      {/if}
    </button>
  </div>
  
  {#if showStrengthIndicator && value}
    <div class="strength-indicator">
      <div class="strength-indicator-bar {strengthClass}">
        Password Strength: {strengthText}
      </div>
    </div>
  {/if}
  
  <style>
    .sr-only {
      position: absolute !important;
      width: 1px !important;
      height: 1px !important;
      padding: 0 !important;
      margin: -1px !important;
      overflow: hidden !important;
      clip: rect(0, 0, 0, 0) !important;
      white-space: nowrap !important;
      border: 0 !important;
    }
    
    .password-field {
      position: relative !important;
      display: flex !important;
      align-items: center !important;
      width: 100% !important;
      max-width: 300px !important;
      margin: 0 auto !important;
      margin-bottom: 10px !important;
    }
    
    .password-input {
      width: 100% !important;
      padding: 8px 50px 8px 12px !important;
      border: 1px solid #666 !important;
      border-radius: 4px !important;
      background: transparent !important;
      color: white !important;
      font-size: 14px !important;
      outline: none !important;
    }
    
    .password-input:focus {
      border-color: #888 !important;
      box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.1) !important;
    }
    
    .password-input::placeholder {
      color: #888 !important;
    }
    
    .toggle-btn {
      position: absolute !important;
      right: 8px !important;
      background: transparent !important;
      border: none !important;
      padding: 4px !important;
      cursor: pointer !important;
      color: white !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      width: 32px !important;
      height: 32px !important;
      border-radius: 4px !important;
      z-index: 1 !important;
    }
    
    .toggle-btn:hover {
      background: rgba(255, 255, 255, 0.1) !important;
    }
    
    .toggle-btn:focus {
      outline: 2px solid rgba(255, 255, 255, 0.3) !important;
      outline-offset: 1px !important;
    }
    
    .toggle-btn img {
      width: 20px !important;
      height: 20px !important;
      filter: invert(1) !important;
      opacity: 0.8 !important;
    }
    
    .toggle-btn:hover img {
      opacity: 1 !important;
    }
    
    .strength-indicator {
      width: 100% !important;
      max-width: 300px !important;
      margin: 0 auto !important;
      margin-top: 8px !important;
      padding: 0 !important;
    }
    
    .strength-indicator-bar {
        padding: 4px 8px !important;
        font-size: 12px !important;
        color: white !important;
        text-align: center !important;
        border-radius: 4px !important;
        border: 1px solid !important;
        transition: all 0.3s ease !important;
    }
    
    .strength-indicator-bar.weak {
        background: rgba(239, 68, 68, 0.2) !important;
        border-color: #ef4444 !important;
        color: #ef4444 !important;
    }
    
    .strength-indicator-bar.medium {
        background: rgba(251, 191, 36, 0.2) !important;
        border-color: #fbbf24 !important;
        color: #fbbf24 !important;
    }
    
    .strength-indicator-bar.strong {
        background: rgba(34, 197, 94, 0.2) !important;
        border-color: #22c55e !important;
        color: #22c55e !important;
    }
  </style>