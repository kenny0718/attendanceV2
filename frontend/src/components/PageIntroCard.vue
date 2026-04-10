<template>
  <PageCard>
    <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
    <h1>{{ title }}</h1>
    <p v-if="description">{{ description }}</p>
    <slot />
  </PageCard>
</template>

<script setup>
import PageCard from '@/components/PageCard.vue'

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
})
</script>

<style scoped>
.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.16em;
  color: #c2410c;
}

h1 {
  margin: 0;
  color: #0f172a;
}

p {
  margin: 10px 0 0;
  color: #475569;
  line-height: 1.7;
}
</style>
