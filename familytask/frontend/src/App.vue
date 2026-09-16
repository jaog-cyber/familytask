<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getMe, isLogged, logout as apiLogout } from './api.js'

const route = useRoute()
const router = useRouter()
const member = ref(getMe())

async function logout() {
  try {
    await apiLogout()
  } finally {
    // Le membre est renvoyé vers la connexion même si le serveur ne répond pas.
    member.value = null
    router.push('/login')
  }
}
</script>

<template>
  <header v-if="isLogged() && route.meta.nav" class="app-header">
    <div class="header-content">
      <span class="header-mark">🏠</span>
      <div>
        <p class="eyebrow">ORGANISATION FAMILIALE</p>
        <h1>FamilyTask · {{ member?.name }}</h1>
      </div>
      <button class="header-action" type="button" @click="logout">Se déconnecter</button>
    </div>
  </header>
  <main class="app-main"><router-view /></main>
  <nav v-if="isLogged() && route.meta.nav" class="tabbar" aria-label="Navigation principale">
    <router-link to="/taches" class="tab">✅ <span>Tâches</span></router-link>
    <router-link to="/assistant" class="tab">✨ <span>Assistant</span></router-link>
    <router-link v-if="getMe()" to="/famille" class="tab">👨‍👩‍👧 <span>Famille</span></router-link>
    <router-link to="/about" class="tab">ⓘ <span>About</span></router-link>
  </nav>
</template>
