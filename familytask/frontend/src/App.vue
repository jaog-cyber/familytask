<script setup>
import { onMounted, ref } from 'vue'
import TaskList from './components/TaskList.vue'

// La liste des tâches est réactive et provient de l'API.
const tasks = ref([])

// Le texte saisi dans le champ du formulaire.
const newTaskTitle = ref('')

// Recharge la liste des tâches depuis l'API.
async function loadTasks() {
  const response = await fetch('/api/tasks')
  tasks.value = await response.json()
}

// Ajoute une nouvelle tâche via l'API, puis recharge la liste.
async function addTask() {
  const title = newTaskTitle.value.trim()

  // Ne rien ajouter si le champ est vide.
  if (!title) return

  await fetch(`/api/tasks?title=${encodeURIComponent(title)}`, {
    method: 'POST',
  })
  await loadTasks()

  // Vide le champ après l'ajout.
  newTaskTitle.value = ''
}

// Inverse l'état terminé d'une tâche via l'API, puis recharge la liste.
async function toggleTask(taskId) {
  await fetch(`/api/tasks/${taskId}`, { method: 'PATCH' })
  await loadTasks()
}

// Supprime une tâche via l'API, puis recharge la liste.
async function removeTask(taskId) {
  await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' })
  await loadTasks()
}

// Charge les tâches dès que le composant est monté.
onMounted(loadTasks)
</script>

<template>
  <header class="app-header">
    <div class="header-content">
      <span class="header-mark">🏠</span>
      <div>
        <p class="eyebrow">ORGANISATION FAMILIALE</p>
        <h1>FamilyTask</h1>
      </div>
      </div>
  </header>
  <main class="app-main">
    <section class="card task-card">
      <div class="section-heading">
        <div>
          <p class="section-kicker">Aujourd'hui</p>
          <h2>Mes tâches</h2>
        </div>
        <span class="task-count">{{ tasks.length }}</span>
      </div>

      <form class="task-form" @submit.prevent="addTask">
        <input
          v-model="newTaskTitle"
          class="task-input"
          type="text"
          placeholder="Nouvelle tâche"
        />
        <button class="primary-button" type="submit">Ajouter</button>
      </form>

      <TaskList
        :tasks="tasks"
        @toggle="toggleTask"
        @remove="removeTask"
      />
    </section>
  </main>
</template>
