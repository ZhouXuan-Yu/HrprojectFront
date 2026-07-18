<template>
  <div
    data-slot="ai-markdown"
    v-html="renderedHtml"
    :class="{ 'ai-markdown--streaming': streaming }"
  ></div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  content: { type: String, required: true },
  streaming: { type: Boolean, default: false },
});

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function parseInline(text) {
  let html = escapeHtml(text);

  // Bold+italic ***...***
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  // Bold **...**
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Bold __...__
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
  // Italic *...*
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  // Italic _..._
  html = html.replace(/_(.+?)_/g, '<em>$1</em>');
  // Inline code `...`
  html = html.replace(/`(.+?)`/g, '<code>$1</code>');
  // Links [text](url)
  html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  return html;
}

function parseMarkdown(content) {
  if (!content) return '';

  // Step 1: Extract and protect fenced code blocks
  const codeBlocks = [];
  let text = content.replace(/```(\w*)\n([\s\S]*?)```/g, (_match, lang, code) => {
    const id = codeBlocks.length;
    const langLabel = lang ? `<span data-slot="ai-markdown-code-lang">${escapeHtml(lang)}</span>` : '';
    codeBlocks.push(
      `<pre data-slot="ai-markdown-code">${langLabel}<code>${escapeHtml(code.trimEnd())}</code></pre>`
    );
    return `\x00CODEBLOCK${id}\x00`;
  });

  const lines = text.split('\n');
  const result = [];
  let i = 0;
  let listBuffer = [];
  let listType = null; // 'ul' | 'ol'

  function flushList() {
    if (listBuffer.length > 0) {
      const tag = listType === 'ol' ? 'ol' : 'ul';
      result.push(`<${tag} data-slot="ai-markdown-list">${listBuffer.join('')}</${tag}>`);
      listBuffer = [];
      listType = null;
    }
  }

  function isSpecialLine(trimmed) {
    if (/^\x00CODEBLOCK\d+\x00$/.test(trimmed)) return true;
    if (/^#{1,6}\s/.test(trimmed)) return true;
    if (/^[-*]\s/.test(trimmed)) return true;
    if (/^\d+\.\s/.test(trimmed)) return true;
    return false;
  }

  while (i < lines.length) {
    const raw = lines[i];

    // Code block placeholder
    const cbMatch = raw.match(/^\x00CODEBLOCK(\d+)\x00$/);
    if (cbMatch) {
      flushList();
      result.push(codeBlocks[parseInt(cbMatch[1])]);
      i++;
      continue;
    }

    const trimmed = raw.trim();

    // Blank line — separates paragraphs and flushes lists
    if (trimmed === '') {
      flushList();
      i++;
      continue;
    }

    // Heading: #, ##, ###, ####, #####, ######
    const headingMatch = trimmed.match(/^(#{1,6})\s+(.+)/);
    if (headingMatch) {
      flushList();
      const level = headingMatch[1].length;
      result.push(`<h${level} data-slot="ai-markdown-heading">${parseInline(headingMatch[2])}</h${level}>`);
      i++;
      continue;
    }

    // Unordered list: - or *
    const ulMatch = trimmed.match(/^[-*]\s+(.+)/);
    if (ulMatch) {
      if (listType !== 'ul') {
        flushList();
        listType = 'ul';
      }
      listBuffer.push(`<li data-slot="ai-markdown-list-item">${parseInline(ulMatch[1])}</li>`);
      i++;
      continue;
    }

    // Ordered list: 1.
    const olMatch = trimmed.match(/^\d+\.\s+(.+)/);
    if (olMatch) {
      if (listType !== 'ol') {
        flushList();
        listType = 'ol';
      }
      listBuffer.push(`<li data-slot="ai-markdown-list-item">${parseInline(olMatch[1])}</li>`);
      i++;
      continue;
    }

    // Paragraph: collect consecutive non-special lines
    flushList();
    const paraLines = [];
    while (i < lines.length) {
      const curRaw = lines[i];
      const curTrimmed = curRaw.trim();
      if (curTrimmed === '' || isSpecialLine(curTrimmed)) break;
      paraLines.push(curRaw);
      i++;
    }
    if (paraLines.length > 0) {
      const paraHtml = paraLines
        .map((l) => {
          if (l.endsWith('  ')) {
            return parseInline(l.slice(0, -2)) + '<br>';
          }
          return parseInline(l);
        })
        .join('\n');
      result.push(`<p data-slot="ai-markdown-paragraph">${paraHtml}</p>`);
    } else {
      i++;
    }
  }

  flushList();
  return result.join('\n');
}

const renderedHtml = computed(() => {
  const html = parseMarkdown(props.content);
  if (props.streaming) {
    return html + '<span data-slot="ai-markdown-cursor" aria-hidden="true"></span>';
  }
  return html;
});
</script>

<style scoped>
[data-slot="ai-markdown"] {
  font-size: var(--fs-body, 14px);
  line-height: 1.7;
  color: var(--c-text, #172033);
  word-break: break-word;
}

/* Headings */
[data-slot="ai-markdown-heading"] {
  margin: 16px 0 8px;
  font-weight: 700;
  line-height: 1.35;
  color: var(--c-text, #172033);
}
h1[data-slot="ai-markdown-heading"] {
  font-size: 24px;
  margin-top: 20px;
}
h2[data-slot="ai-markdown-heading"] {
  font-size: 20px;
  margin-top: 18px;
}
h3[data-slot="ai-markdown-heading"] {
  font-size: var(--fs-title, 18px);
}
h4[data-slot="ai-markdown-heading"] {
  font-size: 16px;
}
h5[data-slot="ai-markdown-heading"] {
  font-size: var(--fs-body, 14px);
}
h6[data-slot="ai-markdown-heading"] {
  font-size: var(--fs-caption, 12px);
  color: var(--c-sub, #8C95A6);
}

/* Paragraph */
[data-slot="ai-markdown-paragraph"] {
  margin: 8px 0;
}
[data-slot="ai-markdown-paragraph"]:first-child {
  margin-top: 0;
}
[data-slot="ai-markdown-paragraph"]:last-child {
  margin-bottom: 0;
}

/* Lists */
[data-slot="ai-markdown-list"] {
  margin: 8px 0;
  padding-left: 20px;
}
[data-slot="ai-markdown-list-item"] {
  margin: 2px 0;
}

/* Inline code */
[data-slot="ai-markdown"] code {
  padding: 2px 5px;
  border-radius: 4px;
  background: var(--c-surface-elevated, #F9FAFC);
  border: 1px solid var(--c-border-light, #EFF1F5);
  font-family: 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 0.9em;
  color: var(--c-primary, #4F6EF7);
}

/* Code blocks */
[data-slot="ai-markdown-code"] {
  margin: 12px 0;
  padding: 14px 16px;
  border-radius: var(--radius, 8px);
  background: var(--c-surface-elevated, #F9FAFC);
  border: 1px solid var(--c-border-light, #EFF1F5);
  overflow-x: auto;
  position: relative;
}
[data-slot="ai-markdown-code"] code {
  font-family: 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.55;
  color: var(--c-text, #172033);
  background: none;
  border: none;
  padding: 0;
  white-space: pre;
  display: block;
}
[data-slot="ai-markdown-code-lang"] {
  position: absolute;
  top: 6px;
  right: 10px;
  font-size: 11px;
  color: var(--c-sub, #8C95A6);
  font-family: inherit;
  pointer-events: none;
}
[data-slot="ai-markdown-code"]:has([data-slot="ai-markdown-code-lang"]) {
  padding-top: 28px;
}

/* Bold / Italic */
[data-slot="ai-markdown"] strong {
  font-weight: 700;
}
[data-slot="ai-markdown"] em {
  font-style: italic;
}

/* Links */
[data-slot="ai-markdown"] a {
  color: var(--c-primary, #4F6EF7);
  text-decoration: underline;
  text-underline-offset: 2px;
}
[data-slot="ai-markdown"] a:hover {
  color: var(--c-primary-hover, #6B84FF);
}

/* Blink cursor (streaming) */
[data-slot="ai-markdown-cursor"] {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--c-primary, #4F6EF7);
  vertical-align: text-bottom;
  margin-left: 1px;
  animation: ai-markdown-blink 1s step-end infinite;
}
@keyframes ai-markdown-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Numbers */
[data-slot="ai-markdown"] {
  font-variant-numeric: tabular-nums;
}

@media (prefers-reduced-motion: reduce) {
  [data-slot="ai-markdown-cursor"] {
    animation: none;
    opacity: 1;
  }
}
</style>
