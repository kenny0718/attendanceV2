<template>
  <PageShell>
    <Navbar />

    <PageIntroCard
      eyebrow="LEAVE REQUEST"
      title="請假申請"
      description="此頁面先恢復為最小可用版本，後續可再接正式請假表單與流程。"
    />

    <PageCard>
      <h2>功能建置中</h2>
      <p>目前已保留路由與頁面骨架，之後可在這裡接上假別、日期區間、代理人與送審流程。</p>
    </PageCard>
  </PageShell>
</template>

<script setup>
import Navbar from '@/components/Navbar.vue'
import PageShell from '@/components/PageShell.vue'
import PageCard from '@/components/PageCard.vue'
import PageIntroCard from '@/components/PageIntroCard.vue'
</script>

<style scoped>
h2 {
  margin: 0;
  color: #0f172a;
}

p {
  margin: 10px 0 0;
  color: #475569;
  line-height: 1.7;
}
</style>
