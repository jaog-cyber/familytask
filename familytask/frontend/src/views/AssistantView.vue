<script setup>
import ChatAssistant from '../components/ChatAssistant.vue'
</script>

<template>
  <section class="view">
    <div class="welcome">
      <p class="section-kicker">ASSISTANT</p>
      <h2>Un coup de main ?</h2>
      <p class="muted">Prépare une idée de tâche pour ta famille.</p>
    </div>

    <div class="card assistant-card">
      <ChatAssistant />
    </div>
  </section>
</template>
