<script setup>
import { getMe } from '../api.js'
const me = getMe()
</script>

<template>
  <section class="view">
    <div class="welcome"><p class="section-kicker">ESPACE FAMILLE</p><h2>Ma famille</h2><p class="muted">Ton profil FamilyTask est prêt.</p></div>
    <div class="card profile-card"><span class="profile-avatar">{{ me?.name?.slice(0, 1).toUpperCase() || '?' }}</span><div><h3>{{ me?.name || 'Membre' }}</h3><p class="muted">{{ me?.email }}</p></div></div>
    <div class="card info-card"><h3>Gestion des membres</h3><p class="muted">La gestion des comptes familiaux sera disponible lorsque les routes membres seront activées dans le backend.</p></div>
  </section>
</template>
