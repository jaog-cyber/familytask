<script setup>
defineProps({
  tasks: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['toggle', 'remove'])
</script>

<template>
  <ul v-if="tasks.length" class="task-list">
    <li v-for="task in tasks" :key="task.id" class="task-item">
      <label class="task-label">
        <input
          type="checkbox"
          class="task-checkbox"
          :checked="task.done"
          @change="emit('toggle', task.id)"
        />
        <span class="task-title" :class="{ done: task.done }">{{ task.title }}</span>
      </label>
      <button
        type="button"
        class="delete-button"
        aria-label="Supprimer la tâche"
        @click="emit('remove', task.id)"
      >
        🗑️
      </button>
    </li>
  </ul>
  <p v-else class="empty-state">Tout est fait, bravo ! 🎉</p>
</template>
