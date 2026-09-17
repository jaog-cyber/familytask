<script setup>
import { ref } from 'vue'
import { apiFetch } from '../api.js'

const emit = defineEmits(['tasks-refresh'])

const prompt = ref('')
const messages = ref([
  {
    author: 'FamilyTask',
    text: 'Bonjour ! Demande-moi d’ajouter une tâche ou de préparer une idée pour la maison.',
  },
])
const isListening = ref(false)

function pushMessage(author, text) {
  messages.value.push({ author, text })
}

async function ask() {
  const text = prompt.value.trim()
  if (!text) return

  pushMessage('Vous', text)
  const previousPrompt = text
  prompt.value = ''

  try {
    const response = await apiFetch('/api/assistant', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    })

    const payload = await response.json().catch(() => null)

    if (!response.ok) {
      throw new Error(payload?.detail || 'L’assistant n’a pas répondu.')
    }

    const assistantText = typeof payload === 'string'
      ? payload
      : payload?.message || 'Je peux vous aider à organiser vos tâches.'

    pushMessage('FamilyTask', assistantText)

    if (payload && typeof payload === 'object' && payload.task) {
      emit('tasks-refresh')
      window.dispatchEvent(new CustomEvent('familytask:tasks-refresh'))
    }
  } catch (error) {
    pushMessage('FamilyTask', error?.message || 'L’assistant est momentanément indisponible.')
    prompt.value = previousPrompt
  }
}

function startSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

  if (!SpeechRecognition) {
    pushMessage('FamilyTask', 'La reconnaissance vocale n’est pas prise en charge par ce navigateur.')
    return
  }

  const recognition = new SpeechRecognition()
  recognition.lang = 'fr-FR'
  recognition.interimResults = false
  recognition.maxAlternatives = 1
  isListening.value = true

  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map((result) => result[0]?.transcript || '')
      .join(' ')
      .trim()

    if (transcript) {
      prompt.value = transcript
    }
  }

  recognition.onerror = () => {
    pushMessage('FamilyTask', 'Je n’ai pas bien compris la phrase dictée. Réessayez.')
    isListening.value = false
  }

  recognition.onend = () => {
    isListening.value = false
  }

  recognition.start()
}
</script>

<template>
  <div class="chat-assistant">
    <div class="chat-messages">
      <p v-if="!messages.length" class="empty-state">Écris une demande pour commencer.</p>
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="chat-bubble"
        :class="message.author === 'Vous' ? 'chat-bubble-user' : 'chat-bubble-assistant'"
      >
        <strong>{{ message.author }}</strong>
        <span>{{ message.text }}</span>
      </div>
    </div>

    <form class="chat-form" @submit.prevent="ask">
      <input
        v-model="prompt"
        class="task-input"
        type="text"
        placeholder="Ex : ajoute une tâche pour Léo"
        aria-label="Message à l’assistant"
      />
      <button
        type="button"
        class="icon-button"
        :disabled="isListening"
        :aria-label="isListening ? 'Écoute en cours' : 'Diction vocale'"
        @click="startSpeechRecognition"
      >
        {{ isListening ? '…' : '🎤' }}
      </button>
      <button class="primary-button" type="submit">Envoyer</button>
    </form>
  </div>
</template>
