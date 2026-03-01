<template>
  <div class="app">
    <header class="header">
      <h1>DM-Code-Agent</h1>
      <div class="config">
        <select v-model="config.provider" class="select">
          <option value="glm">GLM</option>
        </select>
        <input v-model="config.model" class="input" placeholder="模型名称" value="glm-4" />
      </div>
    </header>

    <div class="chat-container">
      <div class="messages">
        <ChatMessage
          v-for="msg in messages"
          :key="msg.id"
          :message="msg"
        />
      </div>

      <div class="input-area">
        <textarea
          v-model="inputMessage"
          class="textarea"
          placeholder="输入你的任务..."
          @keydown.enter.prevent="handleSend"
          :disabled="isLoading"
        />
        <button
          class="button"
          @click="handleSend"
          :disabled="isLoading || !inputMessage.trim()"
        >
          {{ isLoading ? '执行中...' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import axios from 'axios'
import ChatMessage from './components/ChatMessage.vue'
import type { Message, ChatRequest } from './types'

const messages = ref<Message[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const currentSessionId = ref<string | null>(null)

const config = reactive({
  provider: 'glm',
  model: 'ep-20260210175539-4gr98',
  base_url: 'https://ark.cn-beijing.volces.com/api/v3',
  max_steps: 100,
  temperature: 0.7
})

const handleSend = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userMessage = inputMessage.value
  inputMessage.value = ''

  const userMsg: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: userMessage,
    steps: [],
    timestamp: Date.now()
  }
  messages.value.push(userMsg)

  const assistantMsg: Message = {
    id: (Date.now() + 1).toString(),
    role: 'assistant',
    content: '',
    steps: [],
    timestamp: Date.now()
  }
  messages.value.push(assistantMsg)

  await nextTick()
  isLoading.value = true

  console.log('消息已添加到列表，开始发送请求')

  try {
    const request: ChatRequest = {
      message: userMessage,
      provider: config.provider,
      model: config.model,
      base_url: config.base_url || undefined,
      max_steps: config.max_steps,
      temperature: config.temperature
    }

    console.log('发送请求:', request)
    const response = await axios.post('/api/chat', request)
    console.log('收到响应:', response.data)
    currentSessionId.value = response.data.session_id

    const streamUrl = `http://localhost:8000/api/chat/${response.data.session_id}/stream`
    console.log('连接 SSE:', streamUrl)
    
    const eventSource = new EventSource(streamUrl)

    eventSource.onopen = () => {
      console.log('SSE 连接已打开')
    }

    eventSource.onmessage = (event) => {
      console.log('收到 SSE 事件:', event.data)
      try {
        const data = JSON.parse(event.data)
        console.log('解析后的数据:', data)

        const msg = messages.value.find(m => m.id === assistantMsg.id)
        if (!msg) {
          console.error('找不到消息:', assistantMsg.id)
          return
        }

        if (data.error) {
          msg.content = `错误：${data.error}`
          isLoading.value = false
          eventSource.close()
          return
        }

        if (data.is_final) {
          msg.content = data.final_answer || '任务完成'
          isLoading.value = false
          eventSource.close()
          console.log('任务完成')
        } else {
          msg.steps.push(data)
          console.log('添加步骤:', data.step_num, data.action)
          console.log('当前步骤数量:', msg.steps.length)
        }
      } catch (e) {
        console.error('解析 SSE 数据失败:', e, event.data)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE 错误:', error)
      const msg = messages.value.find(m => m.id === assistantMsg.id)
      if (msg) {
        msg.content = '连接错误'
      }
      isLoading.value = false
      eventSource.close()
    }
  } catch (error) {
    console.error('请求失败:', error)
    const msg = messages.value.find(m => m.id === assistantMsg.id)
    if (msg) {
      msg.content = `请求失败：${error}`
    }
    isLoading.value = false
  }
}
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #1a1a2e;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #16213e;
  border-bottom: 1px solid #0f3460;
}

.header h1 {
  font-size: 1.5rem;
  color: #e94560;
}

.config {
  display: flex;
  gap: 0.5rem;
}

.select,
.input {
  padding: 0.5rem;
  background: #0f3460;
  border: 1px solid #1a1a2e;
  border-radius: 4px;
  color: #eee;
  font-size: 0.9rem;
}

.select {
  min-width: 100px;
}

.input {
  width: 200px;
}

.chat-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.input-area {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  background: #16213e;
  border-top: 1px solid #0f3460;
}

.textarea {
  flex: 1;
  padding: 0.75rem;
  background: #0f3460;
  border: 1px solid #1a1a2e;
  border-radius: 4px;
  color: #eee;
  font-size: 1rem;
  resize: none;
  min-height: 50px;
  max-height: 150px;
}

.textarea:focus {
  outline: none;
  border-color: #e94560;
}

.textarea:disabled {
  opacity: 0.6;
}

.button {
  padding: 0.75rem 1.5rem;
  background: #e94560;
  border: none;
  border-radius: 4px;
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.button:hover:not(:disabled) {
  background: #d63d56;
}

.button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
