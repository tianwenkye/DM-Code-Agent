<template>
  <div class="message" :class="message.role">
    <div class="message-header">
      <span class="role">{{ message.role === 'user' ? '用户' : '助手' }}</span>
      <span class="time">{{ formatTime(message.timestamp) }}</span>
    </div>

    <div v-if="message.role === 'user'" class="content">
      {{ message.content }}
    </div>

    <div v-else class="assistant-content">
      <div v-if="message.steps && message.steps.length > 0" class="steps">
        <div v-for="(step, index) in message.steps" :key="index" class="step">
          <div class="step-header">
            <span class="step-num">步骤 {{ step.step_num }}</span>
          </div>
          <div v-if="step.thought" class="step-section">
            <span class="label">思考：</span>
            <span class="value">{{ step.thought }}</span>
          </div>
          <div v-if="step.action" class="step-section">
            <span class="label">动作：</span>
            <span class="value">{{ step.action }}</span>
          </div>
          <div v-if="step.action_input" class="step-section">
            <span class="label">输入：</span>
            <span class="value">{{ formatInput(step.action_input) }}</span>
          </div>
          <div v-if="step.observation" class="step-section">
            <span class="label">观察：</span>
            <span class="value">{{ step.observation }}</span>
          </div>
        </div>
      </div>

      <div v-if="message.content" class="content">
        {{ message.content }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Message } from '../types'

defineProps<{
  message: Message
}>()

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatInput = (input: Record<string, unknown> | null) => {
  if (!input) return ''
  try {
    return JSON.stringify(input, null, 2)
  } catch {
    return String(input)
  }
}
</script>

<style scoped>
.message {
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 8px;
  max-width: 80%;
}

.message.user {
  margin-left: auto;
  background: #0f3460;
}

.message.assistant {
  margin-right: auto;
  background: #16213e;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.role {
  font-weight: 600;
  color: #e94560;
}

.time {
  color: #888;
}

.content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}

.assistant-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.step {
  padding: 0.75rem;
  background: #0f3460;
  border-radius: 4px;
  border-left: 3px solid #e94560;
}

.step-header {
  margin-bottom: 0.5rem;
}

.step-num {
  font-weight: 600;
  color: #e94560;
}

.step-section {
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
}

.label {
  color: #888;
  margin-right: 0.5rem;
}

.value {
  color: #eee;
  word-break: break-word;
}
</style>
