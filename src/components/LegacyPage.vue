<template>
  <div ref="host" class="legacy-page"></div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

const props = defineProps({
  page: { type: String, required: true },
  title: { type: String, required: true },
});

const router = useRouter();
const host = ref(null);
let cleanupFns = [];

const htmlToRoute = {
  'login.html': '/login',
  'recruit-dashboard.html': '/recruit-dashboard',
  'recruit-demand.html': '/recruit-demand',
  'recruit-demand-detail.html': '/recruit-demand-detail',
  'recruit-talent.html': '/recruit-talent',
  'recruit-interview.html': '/recruit-interview',
  'recruit-ai.html': '/recruit-ai',
  'recruit-config.html': '/recruit-config',
};

function transformLegacySource(source) {
  return Object.entries(htmlToRoute).reduce(
    (text, [legacy, route]) => text.split(legacy).join(route),
    source,
  );
}

function normalizeLegacyLinks(root) {
  root.querySelectorAll('a[href]').forEach((link) => {
    const href = link.getAttribute('href');
    if (htmlToRoute[href]) link.setAttribute('href', htmlToRoute[href]);
  });
}

function installClickBridge(root) {
  const onClick = (event) => {
    const link = event.target.closest('a[href]');
    if (!link) return;
    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('mailto:')) return;
    if (href.startsWith('/')) {
      event.preventDefault();
      router.push(href);
    }
  };

  root.addEventListener('click', onClick);
  cleanupFns.push(() => root.removeEventListener('click', onClick));
}

function runInlineScripts(scripts) {
  scripts.forEach((source) => {
    const script = document.createElement('script');
    script.text = transformLegacySource(source);
    document.body.appendChild(script);
    script.remove();
  });
}

async function loadLegacyPage() {
  cleanupFns.forEach((fn) => fn());
  cleanupFns = [];

  const response = await fetch(`/legacy/${props.page}.html`, { cache: 'no-store' });
  if (!response.ok) throw new Error(`无法加载旧页面: ${props.page}`);

  const rawHtml = await response.text();
  const parser = new DOMParser();
  const documentSnapshot = parser.parseFromString(rawHtml, 'text/html');
  const scripts = Array.from(documentSnapshot.querySelectorAll('script:not([src])')).map((script) => script.textContent || '');
  documentSnapshot.querySelectorAll('script').forEach((script) => script.remove());

  host.value.innerHTML = documentSnapshot.body.innerHTML;
  normalizeLegacyLinks(host.value);
  installClickBridge(host.value);

  await nextTick();
  runInlineScripts(scripts);
  normalizeLegacyLinks(host.value);
}

onMounted(loadLegacyPage);
watch(() => props.page, loadLegacyPage);
onBeforeUnmount(() => cleanupFns.forEach((fn) => fn()));
</script>

<style>
.legacy-page {
  display: flex;
  min-height: 100vh;
  width: 100%;
}
</style>
