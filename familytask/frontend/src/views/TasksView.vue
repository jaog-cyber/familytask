<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import TaskList from '../components/TaskList.vue'
import { apiFetch, getMe, setSession } from '../api.js'

const me = getMe()
const tasks = ref([])
const members = ref([])
const newTitle = ref('')
const selectedMemberId = ref(null)
const error = ref('')
const isAdmin = computed(() => Boolean(me?.is_admin))
const otherMembers = computed(() => members.value.filter(member => member.id !== me?.id))

async function refresh() {
  const response = await apiFetch('/api/tasks')
  if (response.status === 401) {
    setSession(null, null)
    return
  }
  tasks.value = await response.json()
}

function handleTasksRefresh() {
  refresh().catch(() => {
    error.value = 'Le serveur est momentanément indisponible.'
  })
}

async function addTask() {
  if (!newTitle.value.trim()) return
  const params = new URLSearchParams({ title: newTitle.value.trim() })
  if (isAdmin.value && selectedMemberId.value !== null) {
    params.set('member_id', selectedMemberId.value)
  }
  await apiFetch(`/api/tasks?${params}`, { method: 'POST' })
  newTitle.value = ''
  await refresh()
}

async function loadMembers() {
  if (!isAdmin.value) return
  const response = await apiFetch('/api/members')
  if (response.ok) members.value = await response.json()
}

async function toggle(taskId) {
  await apiFetch(`/api/tasks/${taskId}`, { method: 'PATCH' })
  await refresh()
}

async function remove(taskId) {
  await apiFetch(`/api/tasks/${taskId}`, { method: 'DELETE' })
  await refresh()
}

onMounted(async () => {
  try {
    await refresh()
    await loadMembers()
  } catch { error.value = 'Le serveur est momentanément indisponible.' }

  window.addEventListener('familytask:tasks-refresh', handleTasksRefresh)
})

onBeforeUnmount(() => {
  window.removeEventListener('familytask:tasks-refresh', handleTasksRefresh)
})
</script>

<template>
  <section class="view">
    <div class="welcome"><p class="section-kicker">AUJOURD'HUI</p><h2>Bonjour {{ me?.name || '' }}</h2><p class="muted">Les petites actions qui font tourner la maison.</p></div>
    <div class="card">
      <div class="section-heading"><h3>Mes tâches</h3><span class="task-count">{{ tasks.length }}</span></div>
      <form class="task-form" @submit.prevent="addTask"><input v-model="newTitle" class="task-input" placeholder="Nouvelle tâche" /><select v-if="isAdmin" v-model="selectedMemberId" class="assignee-select" aria-label="Pour qui ?"><option :value="null">Pour moi</option><option v-for="member in otherMembers" :key="member.id" :value="member.id">Pour {{ member.name }}</option></select><button class="primary-button" type="submit">Ajouter</button></form>
      <TaskList :tasks="tasks" @toggle="toggle" @remove="remove" />
      <p v-if="error" class="error-message">{{ error }}</p>
    </div>
  </section>
</template>
