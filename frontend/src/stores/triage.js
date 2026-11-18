import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '../api/request'

export const useTriageStore = defineStore('triage', () => {
    const messages = ref([
        { role: 'agent', content: '您好！我是“民声直通”智能分诊助手，请描述您的诉求（例如：小区门口下水道堵了）。' }
    ])
    const currentTriage = ref(null)
    const activeOrder = ref({ status: '' })
    const isThinking = ref(false)

    // 把 mockTriage 换成 fetchTriage，向 Java 后端发送真实请求
    async function fetchTriage(text) {
        if (!text) return

        messages.value.push({ role: 'user', content: text })
        isThinking.value = true

        try {
            // 带上最近对话历史（多轮澄清用），由 Java 后端转发给 Python
            const history = messages.value.slice(0, -1).map(m => ({
                role: m.role === 'user' ? 'user' : 'assistant',
                content: m.content
            }))

            const response = await request.post('/triage', { text, history })
            const data = response.data

            if (data.type === 'clarify') {
                // 需要澄清：把反问显示为 agent 消息，等待用户继续回答
                messages.value.push({ role: 'agent', content: data.question })
            } else {
                const result = {
                    summary: data.summary,
                    mainDept: data.mainDept,
                    assistDept: data.assistDept,
                    basis: data.basis,
                    confidence: data.confidence,
                    status: '待派单'
                }

                currentTriage.value = result
                activeOrder.value = { ...result }

                messages.value.push({
                    role: 'agent',
                    content: `已为您分诊完毕。建议由【${result.mainDept}】主办，【${result.assistDept}】协办。`
                })
            }
        } catch (error) {
            console.error('请求后端失败:', error)
            messages.value.push({
                role: 'agent',
                content: '网络请求失败，请检查 Java 后端（8080）和 Python AI（8000）是否已启动。'
            })
        } finally {
            isThinking.value = false
        }
    }

    // 注意这里返回的是 fetchTriage
    return { messages, currentTriage, activeOrder, isThinking, fetchTriage }
})