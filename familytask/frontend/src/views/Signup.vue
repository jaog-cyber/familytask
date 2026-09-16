<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, setSession } from '../api.js'

const router = useRouter()
const name = ref('')
const family = ref('')
const lien = ref('')
const email = ref('')
const password = ref('')
const error = ref('')

async function submit() {
  error.value = ''
  try {
    const response = await apiFetch('/api/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        email: email.value.trim(),
        password: password.value,
        name: name.value.trim(),
        family: family.value.trim(),
        lien: lien.value.trim(),
      }),
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      error.value = data.detail || 'Impossible de créer le compte.'
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
    <div class="auth-hero"><span class="auth-logo">🏠</span><p class="section-kicker">FAMILYTASK</p><h2>Créer un compte</h2></div>
    <form class="form-stack" @submit.prevent="submit">
      <label>Prénom<input v-model="name" required placeholder="Ton prénom" /></label>
      <label>Nom de famille<input v-model="family" required placeholder="Nom de ta famille" /></label>
      <label>Lien de parenté<input v-model="lien" required placeholder="Parent, mère, père..." /></label>
      <label>Email<input v-model="email" type="email" autocomplete="email" required placeholder="toi@example.com" /></label>
      <label>Mot de passe<input v-model="password" type="password" minlength="8" autocomplete="new-password" required /></label>
      <button class="primary-button block" type="submit">Créer mon compte</button>
    </form>
    <p v-if="error" class="error-message">{{ error }}</p>
    <p class="switch-link">Déjà inscrit ? <router-link to="/login">Se connecter</router-link></p>
  </section>
</template>
