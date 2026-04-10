<template>
  <PageIntroCard :eyebrow="eyebrow" :title="title" :description="description">
    <p v-if="backTo" class="back-row">
      <router-link :to="backTo" class="back-link">{{ backLabel }}</router-link>
    </p>
    <slot />
  </PageIntroCard>
</template>

<script setup>
import PageIntroCard from '@/components/PageIntroCard.vue'

defineProps({
  eyebrow: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: '',
  },
  backTo: {
    type: String,
    default: '/admin',
  },
  backLabel: {
    type: String,
    default: '← 返回平台管理',
  },
})
</script>

<style scoped>
.back-row {
  margin-top: 14px;
}

.back-link {
  color: #0ea5e9;
  text-decoration: none;
  font-weight: 700;
}

.back-link:hover {
  text-decoration: underline;
}
</style>
