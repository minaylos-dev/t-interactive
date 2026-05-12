import { defineStore } from 'pinia'

export const useQuizStore = defineStore('quiz', {
  state: () => ({
    // answers keyed by question id -> variant id
    answers: {}
  }),
  actions: {
    setAnswer(questionId, variantId) {
      if (!questionId) return
      this.answers = { ...this.answers, [questionId]: variantId }
    },
    getAnswer(questionId) {
      return this.answers[questionId] ?? null
    },
    getAllAnswers() {
      return { ...this.answers }
    },
    resetAnswers() {
      this.answers = {}
    }
  }
})
