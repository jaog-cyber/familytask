<script setup>
import { ref } from 'vue'
import TaskList from './components/TaskList.vue'

// La liste des tâches est réactive : Vue met l'affichage à jour quand elle change.
const tasks = ref([
  { id: 1, title: 'Ranger la chambre', done: false },
  { id: 2, title: 'Faire les devoirs', done: true },
])

// Le texte saisi dans le champ du formulaire.
const newTaskTitle = ref('')

// Ajoute une nouvelle tâche à la liste.
function addTask() {
  const title = newTaskTitle.value.trim()

  // Ne rien ajouter si le champ est vide.
  if (!title) return

  tasks.value.push({
    id: Date.now(),
    title,
    done: false,
  })

  // Vide le champ après l'ajout.
  newTaskTitle.value = ''
}

// Inverse l'état terminé de la tâche sélectionnée.
function toggleTask(taskId) {
  const task = tasks.value.find((item) => item.id === taskId)
  if (task) task.done = !task.done
}

// Supprime la tâche sélectionnée.
function removeTask(taskId) {
  tasks.value = tasks.value.filter((task) => task.id !== taskId)
}
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
