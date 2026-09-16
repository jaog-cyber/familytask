<script setup>
import { ref } from 'vue'

const prompt = ref('')
const messages = ref([])

function ask() {
  const text = prompt.value.trim()
  if (!text) return
  messages.value.push({ author: 'Vous', text })
  messages.value.push({ author: 'FamilyTask', text: 'Je peux vous aider à organiser vos tâches. L’assistant IA sera connecté dès que sa route backend sera activée.' })
  prompt.value = ''
}
</script>

<template>
  <section class="view">
    <div class="welcome"><p class="section-kicker">ASSISTANT</p><h2>Un coup de main ?</h2><p class="muted">Prépare une idée de tâche pour ta famille.</p></div>
    <div class="card assistant-card">
      <div class="messages"><p v-if="!messages.length" class="empty-state">Écris une demande pour commencer.</p><p v-for="(message, index) in messages" :key="index" class="message"><strong>{{ message.author }}</strong>{{ message.text }}</p></div>
      <form class="task-form" @submit.prevent="ask"><input v-model="prompt" class="task-input" placeholder="Ex : ranger la cuisine" /><button class="primary-button" type="submit">Envoyer</button></form>
    </div>
  </section>
</template>
