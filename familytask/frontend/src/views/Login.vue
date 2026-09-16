<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, setSession } from '../api.js'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')

async function connect() {
  error.value = ''
  try {
    const response = await apiFetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email: email.value.trim(), password: password.value }),
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      error.value = data.detail || 'Email ou mot de passe incorrect.'
      return
    }
    setSession(data.token, data.member)
    router.push('/taches')
  } catch {
    error.value = 'Le serveur est momentanément indisponible. Réessayez.'
  }
}
</script>

<template>
  <section class="auth card">
    <div class="auth-hero"><span class="auth-logo">🏠</span><p class="section-kicker">FAMILYTASK</p><h2>Retrouver sa famille</h2></div>
    <form class="form-stack" @submit.prevent="connect">
      <label>Email<input v-model="email" type="email" autocomplete="email" required placeholder="maman@example.com" /></label>
      <label>Mot de passe<input v-model="password" type="password" autocomplete="current-password" required /></label>
      <button class="primary-button block" type="submit">Se connecter</button>
    </form>
    <p v-if="error" class="error-message">{{ error }}</p>
    <p class="switch-link">Pas encore de compte ? <router-link to="/signup">Créer un compte</router-link></p>
  </section>
</template>
